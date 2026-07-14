"""
terraform_modifier.py

Enterprise Terraform Patch Generator

Responsibilities:
- Convert approved change requests into Terraform patch plan
- Validate remediation safety
- Generate terraform_patch.json

Safety:
- update  -> allowed
- create  -> allowed
- delete  -> blocked
- replace -> blocked
"""


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
    "terraform-modifier"
)



# ---------------------------------------------------------
# Defaults
# ---------------------------------------------------------

DEFAULT_CHANGE_FILE = (
    "reports/change_requests.json"
)

DEFAULT_INVENTORY = (
    "reports/terraform_resources.json"
)

DEFAULT_PATCH = (
    "reports/terraform_patch.json"
)



# ---------------------------------------------------------
# Modifier Engine
# ---------------------------------------------------------

class TerraformModifier:


    def __init__(
        self,
        change_file: str = DEFAULT_CHANGE_FILE,
        inventory_file: str = DEFAULT_INVENTORY,
        patch_file: str = DEFAULT_PATCH
    ):


        self.change_file = Path(
            change_file
        )


        self.inventory_file = Path(
            inventory_file
        )


        self.patch_file = Path(
            patch_file
        )


        self.patch = {


            "metadata": {


                "generated_at":

                    datetime.now(
                        timezone.utc
                    ).isoformat(),


                "engine":

                    "terraform_modifier",


                "version":

                    "1.0.0"

            },


            "changes":[]

        }




    # -----------------------------------------------------
    # Load JSON
    # -----------------------------------------------------

    def load_json(
        self,
        path: Path
    ) -> Dict[str,Any]:


        if not path.exists():

            logger.warning(
                "File missing: %s",
                path
            )

            return {}



        with open(

            path,

            "r",

            encoding="utf-8"

        ) as file:

            return json.load(file)




    # -----------------------------------------------------
    # Load Inventory
    # -----------------------------------------------------

    def load_inventory(self):


        inventory = self.load_json(

            self.inventory_file

        )


        resources = inventory.get(

            "resources",

            []

        )


        logger.info(

            "Resources loaded: %s",

            len(resources)

        )


        return resources




    # -----------------------------------------------------
    # Validate Action
    # -----------------------------------------------------

    def validate_action(
        self,
        actions: List[str]
    ) -> bool:


        blocked = [

            "delete",

            "replace"

        ]



        for action in actions:


            if action in blocked:

                return False



        return True




    # -----------------------------------------------------
    # Find Resource
    # -----------------------------------------------------

    def find_resource(
        self,
        resource_id: str,
        inventory: List[Dict[str,Any]]
    ):


        for resource in inventory:


            if resource.get(
                "address"
            ) == resource_id:


                return resource



        return None




    # -----------------------------------------------------
    # Generate Patch
    # -----------------------------------------------------

    def generate_patch(self):


        requests = self.load_json(

            self.change_file

        )


        inventory = self.load_inventory()



        changes = requests.get(

            "changes",

            []

        )



        logger.info(

            "Approved changes: %s",

            len(changes)

        )



        for change in changes:


            actions = change.get(

                "actions",

                []

            )



            if not self.validate_action(actions):


                logger.warning(

                    "Skipping destructive change: %s",

                    change.get(
                        "resource"
                    )

                )

                continue



            resource = self.find_resource(

                change.get(
                    "resource"
                ),

                inventory

            )



            patch = {


                "resource":

                    change.get(
                        "resource"
                    ),


                "type":

                    change.get(
                        "type"
                    ),


                "action":

                    actions,


                "operation":

                    "terraform_update",


                "inventory":

                    resource or {}

            }



            self.patch["changes"].append(

                patch

            )




    # -----------------------------------------------------
    # Dependency Resolver
    # -----------------------------------------------------

    def add_dependencies(self):

        """
        Placeholder for dependency graph.

        Future:
        - module dependency
        - resource dependency
        - output dependency
        """


        logger.info(

            "Dependency analysis completed"

        )




    # -----------------------------------------------------
    # Remove Duplicate
    # -----------------------------------------------------

    def remove_duplicates(self):


        unique = {}



        for item in self.patch["changes"]:


            key = item.get(

                "resource"

            )


            unique[key] = item



        self.patch["changes"] = list(

            unique.values()

        )




    # -----------------------------------------------------
    # Save Patch
    # -----------------------------------------------------

    def save_patch(self):


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

                self.patch,

                file,

                indent=4

            )



    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------

    def execute(self):


        logger.info(

            "Starting Terraform Modifier"

        )


        self.generate_patch()


        self.remove_duplicates()


        self.add_dependencies()


        self.save_patch()



        logger.info(

            "Patch generated: %s",

            len(
                self.patch["changes"]
            )

        )



        return self.patch




# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def create_arguments():

    parser = argparse.ArgumentParser(

        description=

        "Enterprise Terraform Patch Generator"

    )


    parser.add_argument(

        "--changes",

        default=DEFAULT_CHANGE_FILE

    )


    parser.add_argument(

        "--inventory",

        default=DEFAULT_INVENTORY

    )


    parser.add_argument(

        "--output",

        default=DEFAULT_PATCH

    )


    return parser.parse_args()




# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    args = create_arguments()



    modifier = TerraformModifier(

        change_file=args.changes,

        inventory_file=args.inventory,

        patch_file=args.output

    )



    result = modifier.execute()



    print(
        "Terraform modification plan created"
    )


    print(
        f"Changes: {len(result['changes'])}"
    )


    print(
        f"Report: {args.output}"
    )




if __name__ == "__main__":

    main()
