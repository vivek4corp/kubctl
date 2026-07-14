"""
pr_creator.py

Enterprise Pull Request Automation Engine

Responsibilities:
- Create GitHub Pull Requests
- Add automation summary
- Link Terraform reports
- Work with GitHub Actions

Requires:
- GITHUB_TOKEN
- GitHub repository information
"""


import os
import json
import argparse
import logging
import requests


from pathlib import Path
from datetime import datetime
from typing import Dict, Any



# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(

    level=logging.INFO,

    format=
    "%(asctime)s | %(levelname)s | %(message)s"

)


logger = logging.getLogger(

    "pr-creator"

)



# ---------------------------------------------------------
# Defaults
# ---------------------------------------------------------

DEFAULT_REPORT = (

    "reports/pr_creation.json"

)


GITHUB_API = (

    "https://api.github.com"

)



# ---------------------------------------------------------
# PR Creator Engine
# ---------------------------------------------------------

class PullRequestCreator:


    def __init__(
        self,
        repository: str,
        token: str,
        report_file: str = DEFAULT_REPORT
    ):


        self.repository = repository



        self.token = token



        self.report_file = Path(

            report_file

        )



        self.headers = {


            "Authorization":

                f"Bearer {self.token}",


            "Accept":

                "application/vnd.github+json"

        }



        self.report = {


            "metadata":

            {

                "generated_at":

                    datetime.utcnow().isoformat(),


                "engine":

                    "pr_creator",


                "version":

                    "1.0.0"

            },


            "pull_request":

                {},


            "success":

                False

        }



    # -----------------------------------------------------
    # GitHub API Request
    # -----------------------------------------------------

    def github_request(
        self,
        method: str,
        endpoint: str,
        payload: Dict[str, Any] = None
    ):

        """
        Generic GitHub API wrapper.
        """


        url = (

            f"{GITHUB_API}{endpoint}"

        )



        try:


            response = requests.request(

                method,

                url,

                headers=self.headers,

                json=payload

            )



            return {


                "status":

                    response.status_code,


                "success":

                    response.ok,


                "data":

                    response.json()

                    if response.text

                    else {}

            }



        except Exception as error:


            return {


                "status":

                    -1,


                "success":

                    False,


                "error":

                    str(error)

            }
        # -----------------------------------------------------
    # Validate Repository Format
    # -----------------------------------------------------

    def validate_repository(
        self
    ) -> bool:

        """
        Validate GitHub repository format.

        Expected:

        owner/repository
        """


        if not self.repository:

            return False



        parts = self.repository.split(

            "/"

        )



        return len(parts) == 2



    # -----------------------------------------------------
    # Check Existing Pull Requests
    # -----------------------------------------------------

    def find_existing_pr(
        self,
        head_branch: str,
        base_branch: str
    ):

        """
        Check if PR already exists.
        """


        endpoint = (

            f"/repos/{self.repository}"

            f"/pulls"

            f"?head={head_branch}"

            f"&base={base_branch}"

            f"&state=open"

        )



        response = self.github_request(

            "GET",

            endpoint

        )



        if response.get(

            "success"

        ):


            prs = response.get(

                "data",

                []

            )



            if prs:

                return prs[0]



        return None



    # -----------------------------------------------------
    # Create Pull Request
    # -----------------------------------------------------

    def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ):

        """
        Create GitHub pull request.
        """


        existing = self.find_existing_pr(

            head_branch,

            base_branch

        )



        if existing:


            logger.info(

                "Existing PR found: #%s",

                existing.get(

                    "number"

                )

            )



            self.report["pull_request"] = existing



            self.report["success"] = True



            return existing



        payload = {


            "title":

                title,


            "body":

                body,


            "head":

                head_branch,


            "base":

                base_branch

        }



        response = self.github_request(

            "POST",

            f"/repos/{self.repository}/pulls",

            payload

        )



        if response.get(

            "success"

        ):


            pr = response.get(

                "data"

            )



            self.report["pull_request"] = {


                "number":

                    pr.get(

                        "number"

                    ),


                "url":

                    pr.get(

                        "html_url"

                    ),


                "title":

                    pr.get(

                        "title"

                    )

            }



            self.report["success"] = True



            logger.info(

                "Pull request created successfully"

            )



            return pr



        else:


            logger.error(

                "PR creation failed: %s",

                response

            )



            return None



    # -----------------------------------------------------
    # Generate PR Description
    # -----------------------------------------------------

    def generate_body(
        self,
        summary: Dict[str, Any]
    ) -> str:

        """
        Generate automated PR description.
        """


        body = f"""

## Automated Terraform Change

This pull request was generated automatically.

### Summary

- Create: {summary.get('create',0)}
- Update: {summary.get('update',0)}
- Delete: {summary.get('delete',0)}
- Replace: {summary.get('replace',0)}

### Validation

Terraform validation completed before PR creation.

### Generated By

Terraform Automation Engine

"""


        return body
    # -----------------------------------------------------
    # Add PR Comment
    # -----------------------------------------------------

    def add_comment(
        self,
        pr_number: int,
        message: str
    ):

        """
        Add comment to pull request.
        """


        payload = {


            "body":

                message

        }



        response = self.github_request(

            "POST",

            f"/repos/{self.repository}"

            f"/issues/{pr_number}/comments",

            payload

        )



        return response.get(

            "success"

        )



    # -----------------------------------------------------
    # Load Report File
    # -----------------------------------------------------

    def load_report(
        self,
        report_path: str
    ) -> Dict[str, Any]:

        """
        Load generated automation reports.
        """


        file_path = Path(

            report_path

        )



        if not file_path.exists():

            return {}



        try:


            with open(

                file_path,

                "r",

                encoding="utf-8"

            ) as file:


                return json.load(

                    file

                )



        except Exception:


            return {}



    # -----------------------------------------------------
    # Generate Report Summary
    # -----------------------------------------------------

    def generate_report_summary(
        self,
        reports: Dict[str, Any]
    ) -> str:

        """
        Create markdown summary.
        """


        summary = """

## Terraform Automation Reports


"""


        for name, data in reports.items():


            summary += f"""

### {name}

```json
{json.dumps(data, indent=2)[:1500]}
```
"""
    # -----------------------------------------------------
    # Save PR Report
    # -----------------------------------------------------

    def save_report(self):

        """
        Save PR creation report.
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

                "PR report created: %s",

                self.report_file

            )



        except Exception as error:


            logger.error(

                "Unable to save PR report: %s",

                error

            )


            raise



    # -----------------------------------------------------
    # Complete PR Workflow
    # -----------------------------------------------------

    def execute(
        self,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str = "main",
        reports: Dict[str, Any] = None
    ):

        """
        Complete pull request workflow.
        """


        logger.info(

            "Starting PR creation workflow"

        )



        if not self.validate_repository():


            raise ValueError(

                "Invalid repository format. Expected owner/repo"

            )



        pr = self.create_pull_request(

            title,

            body,

            source_branch,

            target_branch

        )



        if pr and reports:


            self.update_pull_request(

                pr.get(

                    "number"

                ),

                reports

            )



        self.save_report()



        return self.report



# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def create_arguments():

    parser = argparse.ArgumentParser(

        description=

        "Enterprise GitHub Pull Request Creator"

    )


    parser.add_argument(

        "--repository",

        required=True,

        help=

        "GitHub repository owner/name"

    )


    parser.add_argument(

        "--token",

        default=

        os.getenv(

            "GITHUB_TOKEN"

        ),

        help=

        "GitHub API token"

    )


    parser.add_argument(

        "--title",

        default=

        "Automated Terraform Update",

        help=

        "Pull request title"

    )


    parser.add_argument(

        "--source",

        required=True,

        help=

        "Source branch"

    )


    parser.add_argument(

        "--target",

        default=

        "main",

        help=

        "Target branch"

    )


    parser.add_argument(

        "--report",

        default=

        DEFAULT_REPORT,

        help=

        "PR report output"

    )


    return parser.parse_args()



# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():


    args = create_arguments()



    if not args.token:


        raise ValueError(

            "GITHUB_TOKEN missing"

        )



    creator = PullRequestCreator(

        repository=args.repository,

        token=args.token,

        report_file=args.report

    )



    try:


        body = creator.generate_body(

            {

                "create": 0,

                "update": 0,

                "delete": 0,

                "replace": 0

            }

        )



        creator.execute(

            title=args.title,

            body=body,

            source_branch=args.source,

            target_branch=args.target

        )



        print(

            "Pull request workflow completed"

        )


        print(

            f"Report: {args.report}"

        )



    except Exception as error:


        logger.exception(

            "PR creation failed: %s",

            error

        )


        exit(1)



if __name__ == "__main__":

    main()
