"""
change_generator.py

Enterprise Terraform Change Request Generator

Responsibilities:
- Convert Terraform drift into remediation requests
- Separate safe and destructive changes
- Generate automation input
- Generate manual approval requests

Safety Model:
- create  -> allowed
- update  -> allowed
- delete  -> blocked
- replace -> blocked
"""


import os
import json
import argparse
import logging


from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List



# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s | %(levelname)s | %(message)s"

)


logger = logging.getLogger(
    "change-generator"
)



# ---------------------------------------------------------
# Defaults
# ---------------------------------------------------------

DEFAULT_DRIFT = (
    "reports/drift.json"
)

DEFAULT_CHANGE_REQUEST = (
    "reports/change_requests.json"
)

DEFAULT_REPORT = (
    "reports/change_requests_report.json"
)

DEFAULT_MANUAL_REVIEW = (
    "reports/manual_review.json"
)



# ---------------------------------------------------------
# Change Generator Engine
# ---------------------------------------------------------

class ChangeGenerator:


    def __init__(
        self,
        drift_file: str = DEFAULT_DRIFT,
        output_file: str = DEFAULT_CHANGE_REQUEST,
        report_file: str = DEFAULT_REPORT,
        manual_review_file: str = DEFAULT_MANUAL_REVIEW
    ):


        self.drift_file = Path(
            drift_file
        )


        self.output_file = Path(
            output_file
        )


        self.report_file = Path(
            report_file
        )


        self.manual_review_file = Path(
            manual_review_file
        )


        self.safe_changes = []


        self.blocked_changes = []


        self.report = {


            "metadata": {


                "generated_at":

                    datetime.now(
                        timezone.utc
                    ).isoformat(),


                "engine":

                    "change_generator",


                "version":

                    "1.0.0"

            },


            "summary": {


                "safe_changes":

                    0,


                "manual_review":

                    0

            }

        }



    # -----------------------------------------------------
    # Load JSON
    # -----------------------------------------------------

    def load_json(
        self,
        file_path: Path
    ) -> Dict[str, Any]:


        if not file_path.exists():

            logger.warning(
                "File not found: %s",
                file_path
            )

            return {}


        with open(

            file_path,

            "r",

            encoding="utf-8"

        ) as file:

            return json.load(file)



    # -----------------------------------------------------
    # Normalize Action
    # -----------------------------------------------------

    def normalize_action(
        self,
        action
    ) -> List[str]:

        """
        Terraform actions can be:

        ["update"]

        or

        "delete,create"
        """

        if isinstance(
            action,
            list
        ):

            return action


        if isinstance(
            action,
            str
        ):

            return [

                item.strip()

                for item in action.split(",")

            ]


        return []



    # -----------------------------------------------------
    # Analyze Drift
    # -----------------------------------------------------

    def analyze_drift(self):


        drift = self.load_json(

            self.drift_file

        )


        resources = drift.get(

            "resources",

            []

        )



        for resource in resources:


            actions = self.normalize_action(

                resource.get(
                    "action"
                )

            )



            change = {


                "resource":

                    resource.get(
                        "resource"
                    ),


                "type":

                    resource.get(
                        "type"
                    ),


                "actions":

                    actions,


                "source":

                    "terraform_drift"

            }



            if (

                "delete" in actions

                or

                "replace" in actions

                or

                (
                    "delete" in actions
                    and
                    "create" in actions
                )

            ):


                self.blocked_changes.append(

                    {


                        **change,


                        "risk":

                            "HIGH",


                        "status":

                            "MANUAL_APPROVAL_REQUIRED",


                        "reason":

                            "Destructive Terraform operation detected"

                    }

                )


                continue



            if (

                "create" in actions

                or

                "update" in actions

            ):


                self.safe_changes.append(

                    change

                )



    # -----------------------------------------------------
    # Save Change Requests
    # -----------------------------------------------------

    def save_changes(self):


        self.output_file.parent.mkdir(

            parents=True,

            exist_ok=True

        )


        with open(

            self.output_file,

            "w",

            encoding="utf-8"

        ) as file:


            json.dump(

                {


                    "changes":

                        self.safe_changes


                },

                file,

                indent=4

            )



    # -----------------------------------------------------
    # Save Manual Review
    # -----------------------------------------------------

    def save_manual_review(self):


        self.manual_review_file.parent.mkdir(

            parents=True,

            exist_ok=True

        )


        with open(

            self.manual_review_file,

            "w",

            encoding="utf-8"

        ) as file:


            json.dump(

                {


                    "manual_review":

                        self.blocked_changes


                },

                file,

                indent=4

            )



    # -----------------------------------------------------
    # Save Report
    # -----------------------------------------------------

    def save_report(self):


        self.report["summary"]["safe_changes"] = len(

            self.safe_changes

        )


        self.report["summary"]["manual_review"] = len(

            self.blocked_changes

        )



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

                indent=4

            )



    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------

    def execute(self):


        logger.info(
            "Starting Terraform Change Generator"
        )


        self.analyze_drift()


        self.save_changes()


        self.save_manual_review()


        self.save_report()



        logger.info(
            "Change requests generated: %s",
            len(self.safe_changes)
        )


        logger.info(
            "Manual review required: %s",
            len(self.blocked_changes)
        )



        return self.safe_changes





# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def create_arguments():


    parser = argparse.ArgumentParser(

        description=

        "Enterprise Terraform Change Generator"

    )


    parser.add_argument(

        "--drift",

        default=DEFAULT_DRIFT

    )


    parser.add_argument(

        "--output",

        default=DEFAULT_CHANGE_REQUEST

    )


    parser.add_argument(

        "--report",

        default=DEFAULT_REPORT

    )


    return parser.parse_args()




# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():


    args = create_arguments()



    generator = ChangeGenerator(

        drift_file=args.drift,

        output_file=args.output,

        report_file=args.report

    )



    changes = generator.execute()



    print(
        "Terraform change request generation completed"
    )


    print(
        f"Total safe changes: {len(changes)}"
    )


    print(
        f"Output: {args.output}"
    )





if __name__ == "__main__":

    main()
