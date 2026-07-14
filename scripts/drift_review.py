"""Create a committed, human-readable Terraform drift review document.

The document is deliberately separate from the ignored reports directory so a
pull request is created for reviewers without changing infrastructure code.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def value(value):
    """Render JSON values compactly while keeping the review readable."""
    if value is None:
        return "`null`"
    rendered = json.dumps(value, indent=2, sort_keys=True, default=str)
    return f"```json\n{rendered}\n```"


def main():
    parser = argparse.ArgumentParser(description="Generate a Terraform drift review")
    parser.add_argument("--drift", required=True, help="Drift JSON report")
    parser.add_argument("--output", required=True, help="Tracked Markdown output")
    args = parser.parse_args()

    # utf-8-sig also accepts normal UTF-8, while making locally produced
    # PowerShell JSON fixtures work on Windows.
    data = json.loads(Path(args.drift).read_text(encoding="utf-8-sig"))
    resources = data.get("resources", data if isinstance(data, list) else [])

    lines = [
        "# Terraform drift review",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "> This document is a review aid. No Terraform configuration was changed and no `terraform apply` was run by the drift workflow.",
        "",
        f"Detected resources: **{len(resources)}**",
        "",
    ]
    for item in resources:
        lines.extend([
            f"## `{item.get('resource', 'unknown resource')}`",
            "",
            f"- Actions Terraform proposes: `{', '.join(item.get('actions', []))}`",
            f"- Risk: `{item.get('risk', 'UNKNOWN')}`",
            "",
            "### Observed state (before)",
            value(item.get("before")),
            "",
            "### Configuration target (after)",
            value(item.get("after")),
            "",
        ])

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
