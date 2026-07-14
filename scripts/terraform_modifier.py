"""
terraform_modifier.py

Enterprise Terraform Generic Modification Engine

Responsibilities:
- Read Terraform resource inventory
- Compare resource changes
- Generate modification plans
- Create generic patch instructions

This file does NOT:
- modify terraform files directly
- know cloud providers
- know resource types
- know module structures

Writing is handled by terraform_writer.py
"""


import os
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

    format=
    "%(asctime)s | %(levelname)s | %(message)s"

)


logger = logging.getLogger(
    "terraform-modifier"
)



# ---------------------------------------------------------
# Defaults
# ---------------------------------------------------------

DEFAULT_RESOURCE_FILE = (
    "reports/terraform_resources.json"
)


DEFAULT_PATCH_FILE = (
    "reports/terraform_patch.json"
)



# ---------------------------------------------------------
# Terraform Modifier Engine
# ---------------------------------------------------------

class TerraformModifier:
    """
    Generic Terraform modification planner.

    Responsible for creating
    change instructions only.
    """



    def __init__(
        self,
        resource_file: str,
        patch_file: str = DEFAULT_PATCH_FILE
    ):


        self.resource_file = Path(
            resource_file
        )


        self.patch_file = Path(
            patch_file
        )


        self.resources = {}


        self.patch_plan = {


            "metadata":
            {

                "generated_at":
                    datetime.utcnow().isoformat(),


                "engine":
                    "terraform_modifier",


                "version":
                    "1.0.0"

            },


            "changes": [],


            "summary":
            {

                "create": 0,

                "update": 0,

                "delete": 0,

                "replace": 0

            }

        }



    # -----------------------------------------------------
    # Load Terraform Inventory
    # -----------------------------------------------------

    def load_resources(self):

        """
        Load parser output.
        """

        logger.info(
            "Loading terraform inventory"
        )


        if not self.resource_file.exists():

            raise FileNotFoundError(

                f"Resource file missing: {self.resource_file}"

            )


        with open(

            self.resource_file,

            "r",

            encoding="utf-8"

        ) as file:


            self.resources = json.load(
                file
            )


        logger.info(

            "Resources loaded: %s",

            len(
                self.resources.get(
                    "resources",
                    []
                )
            )

        )



    # -----------------------------------------------------
    # Patch Object Generator
    # -----------------------------------------------------

    def create_patch_object(
        self,
        action: str,
        resource: Dict[str, Any],
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:

        """
        Create standard patch object.
        """


        return {


            "action":

                action,


            "terraform_address":

                resource.get(
                    "terraform_address"
                ),


            "resource_type":

                resource.get(
                    "resource_type"
                ),


            "resource_name":

                resource.get(
                    "resource_name"
                ),


            "source_file":

                resource.get(
                    "source",
                    {}
                ).get(
                    "file"
                ),


            "changes":

                changes


        }
            # -----------------------------------------------------
    # Resource Lookup
    # -----------------------------------------------------

    def find_resource(
        self,
        terraform_address: str
    ) -> Dict[str, Any]:
        """
        Find resource using terraform address.
        """

        resources = self.resources.get(
            "resources",
            []
        )


        for resource in resources:

            if resource.get(
                "terraform_address"
            ) == terraform_address:

                return resource



        return {}



    # -----------------------------------------------------
    # Generic Attribute Comparison
    # -----------------------------------------------------

    def compare_attributes(
        self,
        current: Dict[str, Any],
        desired: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare resource attributes.

        Works for any terraform resource.
        """


        changes = {}


        all_keys = set(

            current.keys()

        ).union(

            desired.keys()

        )



        for key in all_keys:


            current_value = current.get(
                key
            )


            desired_value = desired.get(
                key
            )



            if current_value != desired_value:


                changes[key] = {


                    "before":

                        current_value,


                    "after":

                        desired_value


                }



        return changes



    # -----------------------------------------------------
    # Determine Action
    # -----------------------------------------------------

    def determine_action(
        self,
        current_exists: bool,
        desired_exists: bool,
        changes: Dict[str, Any]
    ) -> str:

        """
        Determine terraform operation.
        """


        if not current_exists and desired_exists:

            return "create"



        if current_exists and not desired_exists:

            return "delete"



        if current_exists and desired_exists:


            if changes:

                return "update"


            return "none"



        return "none"



    # -----------------------------------------------------
    # Generate Modification Plan
    # -----------------------------------------------------

    def generate_change(
        self,
        terraform_address: str,
        desired_configuration: Dict[str, Any]
    ):
        """
        Compare desired state with current terraform state.
        """


        resource = self.find_resource(

            terraform_address

        )


        current_configuration = {}


        if resource:


            current_configuration = resource.get(

                "configuration",

                {}

            )



        changes = self.compare_attributes(

            current_configuration,

            desired_configuration

        )



        action = self.determine_action(

            bool(resource),

            bool(desired_configuration),

            changes

        )



        if action == "none":

            return



        patch = self.create_patch_object(

            action,

            resource,

            changes

        )



        self.patch_plan["changes"].append(

            patch

        )


        self.patch_plan["summary"][action] += 1



        logger.info(

            "%s planned for %s",

            action,

            terraform_address

        )



    # -----------------------------------------------------
    # Process Change Requests
    # -----------------------------------------------------

    def process_changes(
        self,
        change_requests: List[Dict[str, Any]]
    ):
        """
        Process external change requests.

        Example:

        [
          {
            "terraform_address":
                "resource.type.name",

            "configuration":
                {
                   "attribute":"value"
                }
          }
        ]

        """


        for request in change_requests:


            self.generate_change(

                request.get(
                    "terraform_address"
                ),


                request.get(
                    "configuration",
                    {}
                )

            )
        # -----------------------------------------------------
    # Validate Patch Entry
    # -----------------------------------------------------

    def validate_patch(
        self,
        patch: Dict[str, Any]
    ) -> bool:
        """
        Validate generated modification.

        Prevents invalid operations.
        """


        required_fields = [

            "action",

            "terraform_address",

            "changes"

        ]



        for field in required_fields:


            if field not in patch:


                logger.error(

                    "Invalid patch missing field: %s",

                    field

                )


                return False



        valid_actions = [

            "create",

            "update",

            "delete",

            "replace"

        ]



        if patch["action"] not in valid_actions:


            logger.error(

                "Unsupported action: %s",

                patch["action"]

            )


            return False



        return True



    # -----------------------------------------------------
    # Validate Complete Plan
    # -----------------------------------------------------

    def validate_plan(self):

        """
        Remove invalid patches.
        """


        valid_changes = []



        for patch in self.patch_plan["changes"]:


            if self.validate_patch(
                patch
            ):


                valid_changes.append(
                    patch
                )



        removed = (

            len(
                self.patch_plan["changes"]
            )

            -

            len(valid_changes)

        )


        if removed:


            logger.warning(

                "Removed invalid patches: %s",

                removed

            )



        self.patch_plan["changes"] = valid_changes



    # -----------------------------------------------------
    # Detect Duplicate Changes
    # -----------------------------------------------------

    def remove_duplicates(self):

        """
        Avoid duplicate modifications
        for same terraform address.
        """


        unique = {}



        for patch in self.patch_plan["changes"]:


            key = (

                patch.get(
                    "terraform_address"
                )

                +

                patch.get(
                    "action"
                )

            )



            unique[key] = patch



        self.patch_plan["changes"] = list(

            unique.values()

        )



    # -----------------------------------------------------
    # Dependency Mapping
    # -----------------------------------------------------

    def attach_dependencies(self):

        """
        Attach dependency information
        if available from parser output.
        """


        dependency_map = (

            self.resources.get(

                "resource_dependencies",

                {}

            )

        )



        for patch in self.patch_plan["changes"]:


            address = patch.get(

                "terraform_address"

            )


            patch["dependencies"] = (

                dependency_map.get(

                    address,

                    []

                )

            )



    # -----------------------------------------------------
    # Finalize Modification Plan
    # -----------------------------------------------------

    def finalize_plan(self):

        """
        Execute all safety validations.
        """


        logger.info(

            "Validating patch plan"

        )


        self.validate_plan()



        logger.info(

            "Removing duplicates"

        )


        self.remove_duplicates()



        logger.info(

            "Adding dependencies"

        )


        self.attach_dependencies()



        self.patch_plan["metadata"][

            "total_changes"

        ] = len(

            self.patch_plan["changes"]

        )



        return self.patch_plan
        # -----------------------------------------------------
    # Save Patch Report
    # -----------------------------------------------------

    def save_patch_report(self):

        """
        Write terraform patch plan JSON.
        """


        try:

            self.patch_file.parent.mkdir(

                parents=True,

                exist_ok=True

            )



            with open(

                self.patch_file,

                "w",

                encoding="utf-8"

            ) as file:


                json.dump(

                    self.patch_plan,

                    file,

                    indent=4,

                    default=str

                )



            logger.info(

                "Patch report generated: %s",

                self.patch_file

            )


        except Exception as error:


            logger.error(

                "Unable to save patch report: %s",

                error

            )


            raise



    # -----------------------------------------------------
    # Complete Execution
    # -----------------------------------------------------

    def execute(
        self,
        change_requests: List[Dict[str, Any]]
    ):

        """
        Complete modifier workflow.
        """


        logger.info(

            "Starting Terraform Modifier"

        )


        self.load_resources()



        self.process_changes(

            change_requests

        )



        self.finalize_plan()



        self.save_patch_report()



        logger.info(

            "Terraform Modifier completed"

        )


        return self.patch_plan



# ---------------------------------------------------------
# CLI Helpers
# ---------------------------------------------------------

def load_change_file(
    path: str
) -> List[Dict[str, Any]]:

    """
    Load external change request JSON.
    """


    if not path:

        return []



    file_path = Path(path)



    if not file_path.exists():

        raise FileNotFoundError(

            f"Change file not found: {path}"

        )



    with open(

        file_path,

        "r",

        encoding="utf-8"

    ) as file:


        return json.load(file)



def create_arguments():

    parser = argparse.ArgumentParser(

        description=
        "Enterprise Terraform Modification Engine"

    )


    parser.add_argument(

        "--resources",

        default=DEFAULT_RESOURCE_FILE,

        help=
        "Terraform resource inventory JSON"

    )


    parser.add_argument(

        "--changes",

        required=True,

        help=
        "Desired change request JSON"

    )


    parser.add_argument(

        "--output",

        default=DEFAULT_PATCH_FILE,

        help=
        "Generated patch report"

    )


    return parser.parse_args()



# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():


    args = create_arguments()



    try:


        change_requests = load_change_file(

            args.changes

        )



        modifier = TerraformModifier(

            resource_file=args.resources,

            patch_file=args.output

        )



        modifier.execute(

            change_requests

        )



        print(

            "Terraform modification plan created"

        )


        print(

            f"Report: {args.output}"

        )



    except Exception as error:


        logger.exception(

            "Modifier failed: %s",

            error

        )


        exit(1)



if __name__ == "__main__":

    main()
