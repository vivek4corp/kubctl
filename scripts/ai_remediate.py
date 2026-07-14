"""Ask GitHub Models for a reviewable Terraform patch that adopts live drift.

This script never runs Terraform apply.  It only accepts a unified diff limited
to Terraform source files inside the supplied working directory, checks it with
git, and applies it to the Actions workspace so it can be reviewed in a PR.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests


MODEL = "openai/gpt-4.1"
ALLOWED_SUFFIXES = {".tf", ".tfvars"}
SENSITIVE_KEYWORDS = ("password", "secret", "token", "private_key", "access_key", "sas")


def read_drift(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return redact(data.get("resources", data if isinstance(data, list) else []))


def redact(value, key=""):
    """Do not send credentials from plan JSON or tfvars to the AI service."""
    if any(word in key.lower() for word in SENSITIVE_KEYWORDS):
        return "<redacted>"
    if isinstance(value, dict):
        return {name: redact(item, name) for name, item in value.items()}
    if isinstance(value, list):
        return [redact(item, key) for item in value]
    return value


def source_files(root: Path):
    files = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in ALLOWED_SUFFIXES and ".terraform" not in path.parts:
            content = path.read_text(encoding="utf-8")
            # HCL assignments whose keys identify a secret are safe to redact;
            # the AI must preserve them, not change them.
            content = re.sub(
                r'(?im)^(\\s*[^#\\n]*(?:password|secret|token|private_key|access_key|sas)[^=\\n]*=\\s*)([^\\n#]+)',
                r'\\1"<redacted>"',
                content,
            )
            files.append({"path": path.relative_to(Path.cwd()).as_posix(), "content": content})
    return files


def extract_diff(text: str):
    match = re.search(r"```(?:diff|patch)?\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    candidate = match.group(1) if match else text
    start = candidate.find("diff --git ")
    if start == -1:
        raise ValueError("AI response did not contain a unified git diff")
    return candidate[start:].strip() + "\n"


def validate_paths(diff: str, root: Path):
    allowed_root = root.resolve()
    paths = re.findall(r"^(?:---|\+\+\+) [ab]/(.+)$", diff, re.MULTILINE)
    if not paths:
        raise ValueError("Diff contains no file paths")
    for relative in paths:
        path = (Path.cwd() / relative).resolve()
        if path.suffix not in ALLOWED_SUFFIXES or allowed_root not in path.parents:
            raise ValueError(f"AI proposed an unsupported file: {relative}")


def main():
    parser = argparse.ArgumentParser(description="Create an AI Terraform adoption patch")
    parser.add_argument("--drift", required=True)
    parser.add_argument("--terraform-root", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--patch", required=True)
    args = parser.parse_args()

    token = os.getenv("MODELS_PAT")
    if not token:
        raise RuntimeError("MODELS_PAT is required to generate an AI remediation patch")

    root = Path(args.terraform_root).resolve()
    resources = read_drift(Path(args.drift))
    files = source_files(root)
    prompt = f"""
You are a senior Terraform engineer. Adopt the CURRENT live infrastructure state
into this repository's Terraform configuration. The live observed values are in
each resource's `before` object; `after` is the old desired configuration.

For every supported value that differs, update the configuration to the value
in `before`. For example, when a storage account has
`before.account_replication_type = "ZRS"` and the Terraform source currently
uses `LRS`, the diff must replace `LRS` with `ZRS`. Apply this same rule to all
supported drifted settings (tags, SKU/tier, locations, replication settings,
and module input values). Preserve references and expressions instead of
replacing them with literal values.

Generate a minimal unified git diff that updates only files under
`{root.relative_to(Path.cwd()).as_posix()}` with `.tf` or `.tfvars` extensions.
Do not change providers, backend, workflow files, state, lock files, or scripts.
Do not add explanations: return one ```diff fenced block only. Preserve computed,
sensitive, and provider-generated fields; never copy those into Terraform.
For create/delete/replace, make the smallest configuration change that adopts the
current live state. Do not silently omit an update just because it has medium or
high risk: put the proposed source change in the diff for human PR review. If a
change cannot be represented safely with the supplied module inputs, return an
empty diff block.

Terraform source files:
{json.dumps(files, indent=2)}

Drift data:
{json.dumps(resources, indent=2)}
"""
    response = requests.post(
        "https://models.github.ai/inference/chat/completions",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "Return safe, minimal Terraform diffs only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": 4000,
        },
        timeout=120,
    )
    response.raise_for_status()
    answer = response.json()["choices"][0]["message"]["content"]

    report = {"model": MODEL, "resources": len(resources), "patch_applied": False}
    try:
        diff = extract_diff(answer)
        validate_paths(diff, root)
        patch_path = Path(args.patch)
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_text(diff, encoding="utf-8")
        checked = subprocess.run(["git", "apply", "--check", str(patch_path)], capture_output=True, text=True)
        if checked.returncode:
            raise ValueError(f"AI patch failed validation: {checked.stderr.strip()}")
        subprocess.run(["git", "apply", str(patch_path)], check=True)
        report["patch_applied"] = True
        report["patch_file"] = str(patch_path)
    except ValueError as error:
        report["reason"] = str(error)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    if not report["patch_applied"]:
        print("AI could not produce a safe patch; the drift review PR will still contain the report.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"AI remediation failed: {error}", file=sys.stderr)
        sys.exit(1)
