import json
import os
import sys
from datetime import datetime

from git import Repo, GitCommandError

REPORT = "reports/git_info.json"


def main():

    try:
        repo = Repo(".")
    except Exception as ex:
        print(ex)
        sys.exit(1)

    if repo.bare:
        print("Invalid git repository")
        sys.exit(1)

    ####################################################################
    # Current Branch
    ####################################################################

    current_branch = repo.active_branch.name

    ####################################################################
    # Create Feature Branch
    ####################################################################

    branch_name = (
        "terraform-drift-"
        + datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    )

    print("=" * 80)
    print("Git Manager")
    print("=" * 80)

    print(f"Current Branch : {current_branch}")
    print(f"New Branch     : {branch_name}")

    try:

        repo.git.checkout("-b", branch_name)

    except GitCommandError as ex:

        print(ex)

        sys.exit(1)

    ####################################################################
    # Git Config
    ####################################################################

    with repo.config_writer() as cfg:

        cfg.set_value("user", "name", "Terraform Drift Agent")
        cfg.set_value(
            "user",
            "email",
            "terraform-agent@github.local"
        )

    ####################################################################
    # Stage Only Required Files
    ####################################################################

    staged = []

    allowed_extensions = (
        ".tf",
        ".tfvars",
        ".json",
        ".md"
    )

    for item in repo.index.diff(None):

        path = item.a_path

        if path.endswith(allowed_extensions):

            repo.git.add(path)

            staged.append(path)

    ####################################################################
    # Untracked Files
    ####################################################################

    for path in repo.untracked_files:

        if path.endswith(allowed_extensions):

            repo.git.add(path)

            staged.append(path)

    ####################################################################
    # Nothing Changed
    ####################################################################

    if len(staged) == 0:

        print("No Terraform changes detected.")

        return

    ####################################################################
    # Commit
    ####################################################################

    commit = repo.index.commit(
        "AI Drift Auto Remediation"
    )

    print(f"Commit : {commit.hexsha}")

    ####################################################################
    # Push
    ####################################################################

    origin = repo.remote("origin")

    origin.push(
        refspec=f"{branch_name}:{branch_name}"
    )

    print("Branch pushed successfully.")

    ####################################################################
    # Report
    ####################################################################

    os.makedirs("reports", exist_ok=True)

    data = {

        "current_branch": current_branch,
        "feature_branch": branch_name,
        "commit": commit.hexsha,
        "files": staged

    }

    with open(REPORT, "w") as f:

        json.dump(data, f, indent=4)

    print()
    print(f"Report written : {REPORT}")


if __name__ == "__main__":

    main()
