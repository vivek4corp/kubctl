import json
import os
import subprocess
import sys
from datetime import datetime, UTC

WRITER_REPORT = "reports/terraform_writer.json"
OUTPUT_FILE = "reports/git_info.json"


def run(cmd):

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return result


def git(*args):

    return run(["git", *args])


def load_json(file):

    if not os.path.exists(file):
        return []

    with open(file, encoding="utf-8") as f:
        return json.load(f)


print("=" * 80)
print("Git Manager")
print("=" * 80)

repo = os.getenv("GITHUB_REPOSITORY")

if not repo:
    print("GITHUB_REPOSITORY not found")
    sys.exit(1)

###############################################################
# Current Branch
###############################################################

branch = git(
    "rev-parse",
    "--abbrev-ref",
    "HEAD"
).stdout.strip()

print(f"Current Branch : {branch}")

###############################################################
# Feature Branch
###############################################################

timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")

feature_branch = f"drift-remediation/{timestamp}"

print(f"Feature Branch : {feature_branch}")

###############################################################
# Create Branch
###############################################################

result = git(
    "checkout",
    "-b",
    feature_branch
)

if result.returncode != 0:
    print(result.stderr)
    sys.exit(1)

###############################################################
# Stage Only Modified Terraform Files
###############################################################

writer = load_json(WRITER_REPORT)

changed_files = []

for item in writer:

    if not item.get("modified"):
        continue

    file = item["file"]

    if not os.path.exists(file):
        continue

    print(f"Adding : {file}")

    result = git(
        "add",
        file
    )

    if result.returncode == 0:
        changed_files.append(file)

###############################################################
# Nothing Changed
###############################################################

if len(changed_files) == 0:

    print("No Terraform changes detected.")

    report = {
        "repository": repo,
        "current_branch": branch,
        "feature_branch": None,
        "changed_files": [],
        "commit": False,
        "push": False
    }

    os.makedirs("reports", exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=4)

    sys.exit(0)

###############################################################
# Commit
###############################################################

commit_message = "AI Terraform Drift Auto Remediation"

result = git(
    "commit",
    "-m",
    commit_message
)

if result.returncode != 0:
    print(result.stderr)
    sys.exit(1)

###############################################################
# Commit SHA
###############################################################

commit_sha = git(
    "rev-parse",
    "HEAD"
).stdout.strip()

###############################################################
# Push
###############################################################

result = git(
    "push",
    "--set-upstream",
    "origin",
    feature_branch
)

if result.returncode != 0:
    print(result.stderr)
    sys.exit(1)

###############################################################
# Report
###############################################################

report = {
    "repository": repo,
    "current_branch": branch,
    "feature_branch": feature_branch,
    "changed_files": changed_files,
    "commit": True,
    "push": True,
    "commit_sha": commit_sha,
    "commit_message": commit_message
}

os.makedirs("reports", exist_ok=True)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(report, f, indent=4)

print()
print("=" * 80)
print("Git completed successfully.")
print("=" * 80)
