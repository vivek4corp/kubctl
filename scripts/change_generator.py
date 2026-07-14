"""
change_generator.py

Enterprise Terraform Change Request Generator

Responsibilities:
- Convert drift findings into Terraform change requests
- Prepare input for terraform_modifier.py
- Keep resource handling generic

Flow:

drift.json
    |
    v
change_requests.json
    |
    v
terraform_modifier.py

"""


import json
import argparse
import logging


from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any



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

DEFAULT_INPUT = (

    "reports/drift.json"

)


DEFAULT_OUTPUT = (

    "reports/change_requests.json"

)



# ---------------------------------------------------------
# Change Generator Engine
# ---------------------------------------------------------

class ChangeGenerator:


    def __init__(
        self,
        drift_file: str,
        output_file: str
    ):


        self.drift_file = Path(

            drift_file

        )


        self.output_file = Path(

            output_file

        )


        self.changes = []



        self.report = {


            "metadata":

            {

                "generated_at":

                    datetime.utcnow().isoformat(),


                "engine":

                    "change_generator",


                "version":

                    "1.0.0"

            },


            "total_changes":

                0,


            "changes":

                []

        }



    # -----------------------------------------------------
    # Load JSON
    # -----------------------------------------------------

    def load_json(
        self,
        file_path: Path
    ) -> Any:

        """
        Generic JSON loader.
        """


        if not file_path.exists():

            raise FileNotFoundError(

                f"File not found: {file_path}"

            )



        with open(

            file_path,

            "r",

            encoding="utf-8"

        ) as file:


            return json.load(

                file

            )
    # -----------------------------------------------------
    # Normalize Drift Data
    # -----------------------------------------------------

    def normalize_drift(
        self,
        drift_data: Any
    ) -> List[Dict[str, Any]]:

        """
        Normalize different drift report formats.

        Supports:

        [
          {...}
        ]

        or

        {
          "resources":[...]
        }

        """


        if isinstance(

            drift_data,

            list

        ):

            return drift_data



        if isinstance(

            drift_data,

            dict

        ):


            if "resources" in drift_data:


                return drift_data["resources"]



            if "changes" in drift_data:


                return drift_data["changes"]



        logger.warning(

            "Unknown drift format"

        )


        return []



    # -----------------------------------------------------
    # Extract Terraform Address
    # -----------------------------------------------------

    def extract_address(
        self,
        item: Dict[str, Any]
    ) -> str:

        """
        Extract terraform resource address.

        Supports generic keys.
        """


        possible_keys = [


            "terraform_address",


            "resource_address",


            "address",


            "resource",


            "id"

        ]



        for key in possible_keys:


            if item.get(key):


                return item[key]



        return ""



    # -----------------------------------------------------
    # Extract Changes
    # -----------------------------------------------------

    def extract_changes(
        self,
        item: Dict[str, Any]
    ) -> Dict[str, Any]:

        """
        Extract attribute differences.
        """


        possible_keys = [


            "changes",


            "diff",


            "attributes",


            "difference"

        ]



        for key in possible_keys:


            value = item.get(

                key

            )


            if isinstance(

                value,

                dict

            ):


                return value



        return {}



    # -----------------------------------------------------
    # Convert Drift To Terraform Change
    # -----------------------------------------------------

    def convert_change(
        self,
        resource: Dict[str, Any]
    ) -> Dict[str, Any]:

        """
        Convert one drift item into
        terraform_modifier input format.
        """


        address = self.extract_address(

            resource

        )



        changes = self.extract_changes(

            resource

        )



        if not address or not changes:


            return {}



        terraform_changes = {}



        for attribute, value in changes.items():


            # Existing drift format

            if isinstance(

                value,

                dict

            ) and "expected" in value:


                terraform_changes[attribute] = {


                    "after":

                        value["expected"]

                }



            elif isinstance(

                value,

                dict

            ) and "desired" in value:


                terraform_changes[attribute] = {


                    "after":

                        value["desired"]

                }



            else:


                terraform_changes[attribute] = {


                    "after":

                        value

                }



        return {


            "terraform_address":

                address,


            "changes":

                terraform_changes

        }
    # -----------------------------------------------------
    # Remove Duplicate Changes
    # -----------------------------------------------------

    def remove_duplicates(
        self,
        changes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        """
        Remove duplicate terraform changes.
        """


        unique = {}



        for item in changes:


            address = item.get(

                "terraform_address"

            )


            if not address:

                continue



            key = json.dumps(

                item,

                sort_keys=True

            )



            unique[key] = item



        return list(

            unique.values()

        )



    # -----------------------------------------------------
    # Generate Change Requests
    # -----------------------------------------------------

    def generate_requests(self):

        """
        Convert drift into terraform requests.
        """


        drift_data = self.load_json(

            self.drift_file

        )



        resources = self.normalize_drift(

            drift_data

        )



        generated = []



        for resource in resources:


            change = self.convert_change(

                resource

            )



            if change:


                generated.append(

                    change

                )



        generated = self.remove_duplicates(

            generated

        )



        self.changes = generated



        self.report["total_changes"] = len(

            generated

        )



        self.report["changes"] = generated



        return generated



    # -----------------------------------------------------
    # Change Summary
    # -----------------------------------------------------

    def generate_summary(self):

        """
        Create execution summary.
        """


        summary = {


            "total":

                len(

                    self.changes

                ),


            "resources":

                []

        }



        for item in self.changes:


            summary["resources"].append(

                item.get(

                    "terraform_address"

                )

            )



        self.report["summary"] = summary



        return summary



    # -----------------------------------------------------
    # Save Output
    # -----------------------------------------------------

    def save_output(self):

        """
        Save change request JSON.
        """


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

                self.changes,

                file,

                indent=4

            )



        logger.info(

            "Change request generated: %s",

            self.output_file

        )
    # -----------------------------------------------------
    # Save Execution Report
    # -----------------------------------------------------

    def save_report(self):

        """
        Save generator execution report.
        """


        report_file = Path(

            str(self.output_file).replace(

                ".json",

                "_report.json"

            )

        )



        with open(

            report_file,

            "w",

            encoding="utf-8"

        ) as file:


            json.dump(

                self.report,

                file,

                indent=4

            )



        logger.info(

            "Generator report created: %s",

            report_file

        )



    # -----------------------------------------------------
    # Execute Generator
    # -----------------------------------------------------

    def execute(self):

        """
        Complete workflow.
        """


        logger.info(

            "Starting Terraform Change Generator"

        )



        self.generate_requests()



        self.generate_summary()



        self.save_output()



        self.save_report()



        return self.report



# ---------------------------------------------------------
# CLI Arguments
# ---------------------------------------------------------

def create_arguments():

    parser = argparse.ArgumentParser(

        description=

        "Enterprise Terraform Change Request Generator"

    )


    parser.add_argument(

        "--drift",

        default=DEFAULT_INPUT,

        help=

        "Drift JSON input file"

    )


    parser.add_argument(

        "--output",

        default=DEFAULT_OUTPUT,

        help=

        "Change request output file"

    )


    return parser.parse_args()



# ---------------------------------------------------------
# Main Execution
# ---------------------------------------------------------

def main():


    args = create_arguments()



    try:


        generator = ChangeGenerator(

            drift_file=args.drift,

            output_file=args.output

        )



        result = generator.execute()



        print(

            "Terraform change request generation completed"

        )


        print(

            f"Total changes: {result['total_changes']}"

        )


        print(

            f"Output: {args.output}"

        )



    except Exception as error:


        logger.exception(

            "Change generation failed: %s",

            error

        )


        exit(1)



if __name__ == "__main__":

    main()
