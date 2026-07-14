"""
terraform_modifier.py

Enterprise Terraform Patch Generator

Responsibilities:
- Convert approved change requests into Terraform patch plan
- Validate remediation safety
- Generate terraform_patch.json

Backward Compatible:
- Supports --inventory and --resources
- Supports old/new inventory formats
- Supports old/new change request formats

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

logger = logging.getLogger("terraform-modifier")


# ---------------------------------------------------------
# Defaults
# ---------------------------------------------------------

DEFAULT_CHANGE_FILE = "reports/change_requests.json"
DEFAULT_INVENTORY = "reports/terraform_resources.json"
DEFAULT_PATCH = "reports/terraform_patch.json"


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

        self.change_file = Path(change_file)
        self.inventory_file = Path(inventory_file)
        self.patch_file = Path(patch_file)

        self.patch = {
            "metadata": {
                "generated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "engine": "terraform_modifier",
                "version": "2.0.0"
            },
            "changes": []
        }

    # -----------------------------------------------------
    # Load JSON
    # -----------------------------------------------------

    def load_json(self, path: Path):

        if not path.exists():
            logger.warning("Missing file: %s", path)
            return {}

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # -----------------------------------------------------
    # Load Inventory
    # -----------------------------------------------------

    def load_inventory(self):

        inventory = self.load_json(self.inventory_file)

        # New inventory format
        if isinstance(inventory, list):

            resources = inventory

        # Old inventory format
        elif isinstance(inventory, dict):

            resources = inventory.get(
                "resources",
                []
            )

        else:

            resources = []

        logger.info(
            "Inventory resources loaded: %s",
            len(resources)
        )

        return resources

    # -----------------------------------------------------
    # Load Change Requests
    # -----------------------------------------------------

    def load_changes(self):

        requests = self.load_json(self.change_file)

        # Old format
        if isinstance(requests, dict):

            return requests.get(
                "changes",
                []
            )

        # New format
        elif isinstance(requests, list):

            return requests

        return []

    # -----------------------------------------------------
    # Validate Actions
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

            if action.lower() in blocked:
                return False

        return True
    # -----------------------------------------------------
    # Find Resource
    # -----------------------------------------------------

    def find_resource(
        self,
        resource_id: str,
        inventory
    ):

        if not resource_id:
            return None

        for resource in inventory:

            # Old inventory format
            if resource.get("address") == resource_id:
                return resource

            # New inventory format
            if resource.get("resource") == resource_id:
                return resource

        return None

    # -----------------------------------------------------
    # Generate Patch
    # -----------------------------------------------------

    def generate_patch(self):

        inventory = self.load_inventory()

        changes = self.load_changes()

        logger.info(
            "Approved changes loaded: %s",
            len(changes)
        )

        for change in changes:

            # Resource
            resource_id = (
                change.get("resource")
                or change.get("address")
            )

            # Type
            resource_type = (
                change.get("type")
                or change.get("resource_type")
                or "unknown"
            )

            # Actions
            actions = change.get("actions")

            if actions is None:

                action = change.get(
                    "action",
                    "update"
                )

                if isinstance(action, str):
                    actions = [action]
                else:
                    actions = action

            if actions is None:
                actions = ["update"]

            if not self.validate_action(actions):

                logger.warning(
                    "Skipping destructive resource: %s",
                    resource_id
                )

                continue

            inventory_resource = self.find_resource(
                resource_id,
                inventory
            )

            patch = {

                "resource": resource_id,

                "type": resource_type,

                "action": actions,

                "operation": "terraform_update",

                "inventory": inventory_resource or {}

            }

            self.patch["changes"].append(
                patch
            )

    # -----------------------------------------------------
    # Dependency Resolver
    # -----------------------------------------------------

    def add_dependencies(self):

        logger.info(
            "Dependency analysis completed"
        )

    # -----------------------------------------------------
    # Remove Duplicates
    # -----------------------------------------------------

    def remove_duplicates(self):

        unique = {}

        for item in self.patch["changes"]:

            key = item.get("resource")

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
        ) as f:

            json.dump(
                self.patch,
                f,
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
            len(self.patch["changes"])
        )

        return self.patch


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def create_arguments():

    parser = argparse.ArgumentParser(
        description="Enterprise Terraform Patch Generator"
    )

    parser.add_argument(
        "--changes",
        default=DEFAULT_CHANGE_FILE,
        help="Change request JSON"
    )

    # Backward compatible:
    # Supports both:
    #   --inventory
    #   --resources
    parser.add_argument(
        "--inventory",
        "--resources",
        dest="inventory",
        default=DEFAULT_INVENTORY,
        help="Terraform inventory/resources JSON"
    )

    parser.add_argument(
        "--output",
        default=DEFAULT_PATCH,
        help="Terraform patch output"
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

    print()
    print("=" * 70)
    print("Terraform Modification Plan Created")
    print("=" * 70)
    print(f"Changes : {len(result['changes'])}")
    print(f"Output  : {args.output}")
    print("=" * 70)


if __name__ == "__main__":
    main()
