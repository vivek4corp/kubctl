"""
git_manager.py

Enterprise Git Automation Engine

Responsibilities:
- Manage git workflow
- Create branches
- Commit changes
- Push changes
- Generate git execution report

No repository-specific assumptions.
"""


import os
import json
import argparse
import logging
import subprocess


from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any



# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(

    level=logging.INFO,

    format=
    "%(asctime)s | %(levelname)s | %(message)s"

)


logger = logging.getLogger(

    "git-manager"

)



# ---------------------------------------------------------
# Defaults
# ---------------------------------------------------------

DEFAULT_REPORT = (

    "reports/git_operation.json"

)



DEFAULT_BRANCH_PREFIX = (

    "terraform-update"

)



# ---------------------------------------------------------
# Git Manager Engine
# ---------------------------------------------------------

class GitManager:


    def __init__(
        self,
        repository_path: str = ".",
        report_file: str = DEFAULT_REPORT,
        allow_push: bool = False
    ):


        self.repository_path = Path(

            repository_path

        ).resolve()



        self.report_file = Path(

            report_file

        )

        self.allow_push = allow_push



        self.report = {


            "metadata":

            {

                "generated_at":

                    datetime.utcnow().isoformat(),


                "engine":

                    "git_manager",


                "version":

                    "1.0.0"

            },


            "operations": [],


            "summary":

            {

                "success": 0,

                "failed": 0

            }

        }



    # -----------------------------------------------------
    # Execute Git Command
    # -----------------------------------------------------

    def run_git(
        self,
        command: List[str]
    ) -> Dict[str, Any]:

        """
        Execute git command safely.
        """


        logger.info(

            "Executing: %s",

            " ".join(command)

        )



        try:


            result = subprocess.run(

                command,

                cwd=self.repository_path,

                capture_output=True,

                text=True

            )



            return {


                "command":

                    " ".join(command),


                "return_code":

                    result.returncode,


                "stdout":

                    result.stdout,


                "stderr":

                    result.stderr,


                "success":

                    result.returncode == 0

            }



        except Exception as error:


            return {


                "command":

                    " ".join(command),


                "return_code":

                    -1,


                "stdout":

                    "",


                "stderr":

                    str(error),


                "success":

                    False

            }
            # -----------------------------------------------------
    # Record Operation Result
    # -----------------------------------------------------

    def record_operation(
        self,
        name: str,
        result: Dict[str, Any]
    ):

        """
        Add git operation result to report.
        """


        operation = {


            "name":

                name,


            "command":

                result.get(

                    "command"

                ),


            "success":

                result.get(

                    "success"

                ),


            "return_code":

                result.get(

                    "return_code"

                ),


            "stdout":

                result.get(

                    "stdout"

                ),


            "stderr":

                result.get(

                    "stderr"

                )

        }



        self.report["operations"].append(

            operation

        )



        if result.get(

            "success"

        ):

            self.report["summary"]["success"] += 1



        else:

            self.report["summary"]["failed"] += 1



    # -----------------------------------------------------
    # Check Repository
    # -----------------------------------------------------

    def validate_repository(self) -> bool:

        """
        Verify git repository.
        """


        result = self.run_git(

            [

                "git",

                "rev-parse",

                "--is-inside-work-tree"

            ]

        )



        self.record_operation(

            "repository_check",

            result

        )



        return result.get(

            "success"

        )



    # -----------------------------------------------------
    # Get Current Branch
    # -----------------------------------------------------

    def current_branch(self) -> str:

        """
        Get current git branch.
        """


        result = self.run_git(

            [

                "git",

                "branch",

                "--show-current"

            ]

        )


        self.record_operation(

            "current_branch",

            result

        )



        return result.get(

            "stdout",

            ""

        ).strip()



    # -----------------------------------------------------
    # Create Branch
    # -----------------------------------------------------

    def create_branch(
        self,
        branch_name: str
    ) -> bool:

        """
        Create and checkout new branch.
        """


        result = self.run_git(

            [

                "git",

                "checkout",

                "-b",

                branch_name

            ]

        )



        self.record_operation(

            "create_branch",

            result

        )



        return result.get(

            "success"

        )



    # -----------------------------------------------------
    # Git Status
    # -----------------------------------------------------

    def git_status(self):

        """
        Get repository changes.
        """


        result = self.run_git(

            [

                "git",

                "status",

                "--short"

            ]

        )



        self.record_operation(

            "git_status",

            result

        )



        return result.get(

            "stdout",

            ""

        )



    # -----------------------------------------------------
    # Add Files
    # -----------------------------------------------------

    def add_changes(self) -> bool:

        """
        Stage all changes.
        """


        result = self.run_git(

            [

                "git",

                "add",

                "."

            ]

        )



        self.record_operation(

            "git_add",

            result

        )



        return result.get(

            "success"

        )



    # -----------------------------------------------------
    # Commit Changes
    # -----------------------------------------------------

    def commit_changes(
        self,
        message: str
    ) -> bool:

        """
        Commit staged changes.
        """


        result = self.run_git(

            [

                "git",

                "commit",

                "-m",

                message

            ]

        )



        self.record_operation(

            "git_commit",

            result

        )



        return result.get(

            "success"

        )
        # -----------------------------------------------------
    # Check Remote Repository
    # -----------------------------------------------------

    def validate_remote(self) -> bool:

        """
        Verify git remote configuration.
        """


        result = self.run_git(

            [

                "git",

                "remote",

                "-v"

            ]

        )


        self.record_operation(

            "remote_check",

            result

        )



        return result.get(

            "success"

        )



    # -----------------------------------------------------
    # Push Branch
    # -----------------------------------------------------

    def push_branch(
        self,
        branch_name: str
    ) -> bool:

        """
        Push branch to remote repository.
        """


        result = self.run_git(

            [

                "git",

                "push",

                "-u",

                "origin",

                branch_name

            ]

        )



        self.record_operation(

            "git_push",

            result

        )



        return result.get(

            "success"

        )



    # -----------------------------------------------------
    # Generate Branch Name
    # -----------------------------------------------------

    def generate_branch_name(
        self,
        prefix: str = DEFAULT_BRANCH_PREFIX
    ) -> str:

        """
        Generate unique branch name.
        """


        timestamp = datetime.utcnow().strftime(

            "%Y%m%d%H%M%S"

        )



        return (

            f"{prefix}-{timestamp}"

        )



    # -----------------------------------------------------
    # Complete Git Workflow
    # -----------------------------------------------------

    def execute_workflow(
        self,
        commit_message: str
    ) -> Dict[str, Any]:

        """
        Execute complete git automation.
        """


        logger.info(

            "Starting git workflow"

        )



        if not self.validate_repository():


            return self.report



        self.validate_remote()



        branch = self.generate_branch_name()



        self.report["branch"] = branch



        if not self.create_branch(

            branch

        ):

            return self.report



        status = self.git_status()



        self.report["changed_files"] = status



        if not status.strip():

            logger.warning(

                "No changes detected"

            )

            return self.report



        if not self.add_changes():

            return self.report



        if not self.commit_changes(

            commit_message

        ):

            return self.report



        if self.allow_push:

            self.push_branch(

                branch

            )

        else:

            logger.warning(

                "Branch push skipped; pass --allow-push to enable it"

            )



        return self.report
        # -----------------------------------------------------
    # Save Git Report
    # -----------------------------------------------------

    def save_report(self):

        """
        Save git operation report.
        """


        try:


            self.report_file.parent.mkdir(

                parents=True,

                exist_ok=True

            )



            with open(

                self.report_file,

                "w",

                encoding="utf-8"

            ) as file:


                json.dump(

                    self.report,

                    file,

                    indent=4,

                    default=str

                )



            logger.info(

                "Git report created: %s",

                self.report_file

            )



        except Exception as error:


            logger.error(

                "Unable to save git report: %s",

                error

            )


            raise



# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def create_arguments():

    parser = argparse.ArgumentParser(

        description=

        "Enterprise Git Automation Engine"

    )


    parser.add_argument(

        "--repo",

        default=".",

        help=

        "Repository path"

    )


    parser.add_argument(

        "--message",

        default=

        "Automated Terraform update",

        help=

        "Commit message"

    )


    parser.add_argument(

        "--report",

        default=

        DEFAULT_REPORT,

        help=

        "Git execution report"

    )


    parser.add_argument(

        "--allow-push",

        action="store_true",

        help="Explicitly allow this legacy script to push a branch to origin"

    )


    return parser.parse_args()



# ---------------------------------------------------------
# Main Execution
# ---------------------------------------------------------

def main():


    args = create_arguments()



    manager = GitManager(

        repository_path=args.repo,

        report_file=args.report,

        allow_push=args.allow_push

    )



    try:


        manager.execute_workflow(

            commit_message=args.message

        )


        manager.save_report()



        print(

            "Git workflow completed"

        )


        print(

            f"Report: {args.report}"

        )



    except Exception as error:


        logger.exception(

            "Git workflow failed: %s",

            error

        )


        exit(1)



if __name__ == "__main__":

    main()
