import json
import os
import subprocess
import sys
from datetime import datetime

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


print("=" * 80)
print("Git Manager")
print("=" * 80)

##############################################################
# Repository Information
##############################################################

repo = os.getenv("GITHUB_REPOSITORY")

if not repo:

    print("GITHUB_REPOSITORY not found")

    sys.exit(1)

##############################################################
# Current Branch
##############################################################

branch = (
    git("rev-parse", "--abbrev-ref", "HEAD")
    .stdout
    .strip()
)

print(f"Current Branch : {branch}")

##############################################################
# Feature Branch
##############################################################

timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

feature_branch = f"drift-remediation/{timestamp}"

print(f"Feature Branch : {feature_branch}")

##############################################################
# Git Status
##############################################################

status = git("status", "--porcelain")

changed_files = []

for line in status.stdout.splitlines():

    if line.strip():

        changed_files.append(line[3:])

if len(changed_files) == 0:

    print("No file changes detected.")

    report = {
        "current_branch": branch,
        "feature_branch": None,
        "repository": repo,
        "changed_files": [],
        "commit": False,
        "push": False
    }

    os.makedirs("reports", exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:

        json.dump(report, f, indent=4)

    sys.exit(0)

##############################################################
# Create Branch
##############################################################

print()

print("Creating feature branch...")

result = git(
    "checkout",
    "-b",
    feature_branch
)

if result.returncode != 0:

    print(result.stderr)

    sys.exit(1)

##############################################################
# Stage Files
##############################################################

git(
    "add",
    "."
)

##############################################################
# Commit
##############################################################

commit_message = "AI Terraform Drift Auto Remediation"

result = git(
    "commit",
    "-m",
    commit_message
)

if result.returncode != 0:

    print(result.stderr)

##############################################################
# Push
##############################################################

result = git(
    "push",
    "--set-upstream",
    "origin",
    feature_branch
)

push_success = result.returncode == 0

if not push_success:

    print(result.stderr)

##############################################################
# Report
##############################################################

report = {

    "repository": repo,

    "current_branch": branch,

    "feature_branch": feature_branch,

    "changed_files": changed_files,

    "commit": True,

    "push": push_success,

    "commit_message": commit_message

}

os.makedirs("reports", exist_ok=True)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        report,
        f,
        indent=4
    )

print()

print("=" * 80)
print("Git completed.")
print("=" * 80)
