import os
import sys
from datetime import datetime
from git import Repo, GitCommandError

REPO_PATH = "."
OUTPUT_FILE = "reports/git_info.json"


def main():
    try:
        repo = Repo(REPO_PATH)
    except Exception as e:
        print(f"Failed to open git repository: {e}")
        sys.exit(1)

    if repo.bare:
        print("Repository is bare.")
        sys.exit(1)

    branch_name = f"drift-fix-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    print("=" * 70)
    print("Git Manager")
    print("=" * 70)

    try:
        print(f"Creating branch: {branch_name}")
        repo.git.checkout("-b", branch_name)

        with repo.config_writer() as config:
            config.set_value("user", "name", "Terraform Drift Agent")
            config.set_value("user", "email", "terraform-agent@github.local")

        repo.git.add(A=True)

        if not repo.is_dirty(untracked_files=True):
            print("No changes detected.")
            return

        commit = repo.index.commit(
            "AI Auto Remediation - Terraform Drift Fix"
        )

        print(f"Commit Created : {commit.hexsha}")

        origin = repo.remote(name="origin")

        print("Pushing branch...")
        origin.push(branch_name)

        os.makedirs("reports", exist_ok=True)

        with open(OUTPUT_FILE, "w") as f:
            f.write(
                f"""{{
    "branch":"{branch_name}",
    "commit":"{commit.hexsha}"
}}
"""
            )

        print(f"Git information saved to {OUTPUT_FILE}")

    except GitCommandError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
