"""
terraform_writer.py

Enterprise Terraform Code Writer

Responsibilities:
- Read terraform patch plan
- Locate terraform blocks
- Apply safe modifications
- Create backup files
- Generate execution report

This engine does NOT know:
- Azure
- AWS
- GCP
- resource types
- module names
"""


import os
import json
import shutil
import argparse
import logging
import re

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

    "terraform-writer"

)



# ---------------------------------------------------------
# Defaults
# ---------------------------------------------------------

DEFAULT_PATCH_FILE = (
    "reports/terraform_patch.json"
)


DEFAULT_REPORT_FILE = (
    "reports/terraform_writer_report.json"
)



BACKUP_FOLDER = (
    ".terraform_backup"
)



# ---------------------------------------------------------
# Terraform Writer Engine
# ---------------------------------------------------------

class TerraformWriter:
    """
    Generic Terraform file modification engine.
    """



    def __init__(
        self,
        patch_file: str,
        report_file: str = DEFAULT_REPORT_FILE
    ):


        self.patch_file = Path(
            patch_file
        )


        self.report_file = Path(
            report_file
        )


        self.patch_plan = {}



        self.report = {


            "metadata":
            {

                "generated_at":
                    datetime.utcnow().isoformat(),

                "engine":
                    "terraform_writer",

                "version":
                    "1.0.0"

            },


            "modified_files": [],


            "failed_changes": [],


            "summary":
            {

                "success": 0,

                "failed": 0

            }

        }



    # -----------------------------------------------------
    # Load Patch Plan
    # -----------------------------------------------------

    def load_patch_plan(self):

        """
        Load terraform modifier output.
        """


        logger.info(

            "Loading patch plan"

        )



        if not self.patch_file.exists():

            raise FileNotFoundError(

                f"Patch file not found: {self.patch_file}"

            )



        with open(

            self.patch_file,

            "r",

            encoding="utf-8"

        ) as file:


            self.patch_plan = json.load(

                file

            )



        logger.info(

            "Changes loaded: %s",

            len(

                self.patch_plan.get(

                    "changes",

                    []

                )

            )

        )
        # -----------------------------------------------------
    # Read Terraform File
    # -----------------------------------------------------

    def read_file(
        self,
        file_path: Path
    ) -> str:
        """
        Read terraform file content.
        """

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                return file.read()


        except Exception as error:

            logger.error(

                "Unable to read %s : %s",

                file_path,

                error

            )

            return ""



    # -----------------------------------------------------
    # Write Terraform File
    # -----------------------------------------------------

    def write_file(
        self,
        file_path: Path,
        content: str
    ):

        """
        Write updated terraform content.
        """


        with open(

            file_path,

            "w",

            encoding="utf-8"

        ) as file:


            file.write(

                content

            )



    # -----------------------------------------------------
    # Backup Terraform File
    # -----------------------------------------------------

    def create_backup(
        self,
        file_path: Path
    ):

        """
        Create backup before modification.
        """


        backup_directory = Path(

            BACKUP_FOLDER

        )


        backup_directory.mkdir(

            parents=True,

            exist_ok=True

        )



        backup_file = (

            backup_directory

            /

            file_path.name

        )



        shutil.copy2(

            file_path,

            backup_file

        )



        logger.info(

            "Backup created: %s",

            backup_file

        )



    # -----------------------------------------------------
    # Locate Terraform Resource Block
    # -----------------------------------------------------

    def find_block(
        self,
        content: str,
        resource_type: str,
        resource_name: str
    ):
        """
        Locate terraform block.

        Example:

        resource "type" "name" {

        }

        """


        pattern = (

            r'(resource|data|module)'

            r'\s+"'

            + re.escape(resource_type)

            + r'"'

            r'\s+"'

            + re.escape(resource_name)

            + r'"'

            r'\s*\{'

        )



        match = re.search(

            pattern,

            content

        )



        if not match:

            return None



        start = match.start()



        brace_count = 0

        block_started = False

        end = None



        for index in range(

            match.end(),

            len(content)

        ):


            character = content[index]



            if character == "{":

                brace_count += 1

                block_started = True



            elif character == "}":


                brace_count -= 1



                if (

                    block_started

                    and

                    brace_count == 0

                ):

                    end = index + 1

                    break



        if end:


            return {

                "start": start,

                "end": end,

                "content":

                    content[start:end]

            }



        return None



    # -----------------------------------------------------
    # Extract Attribute Block
    # -----------------------------------------------------

    def get_block_attributes(
        self,
        block_content: str
    ) -> Dict[str, Any]:
        """
        Placeholder attribute reader.

        Detailed HCL rewrite logic is added
        in next phase.

        Keeps writer generic.
        """


        return {

            "raw":

                block_content

        }
        # -----------------------------------------------------
    # Update Terraform Attributes
    # -----------------------------------------------------

    def update_attributes(
        self,
        block_content: str,
        changes: Dict[str, Any]
    ) -> str:
        """
        Generic terraform attribute updater.

        Handles simple key=value updates.

        Example:

        Before:
            name = "old"

        After:
            name = "new"

        """


        updated_content = block_content



        for attribute, values in changes.items():


            if not isinstance(
                values,
                dict
            ):

                continue



            new_value = values.get(
                "after"
            )


            if new_value is None:

                continue



            # Convert python values
            # into terraform format

            terraform_value = (

                self.convert_to_hcl(

                    new_value

                )

            )



            # Existing attribute

            pattern = (

                r'(^\s*'

                + re.escape(attribute)

                +

                r'\s*=\s*).*$'

            )



            replacement = (

                r'\1'

                +

                terraform_value

            )



            updated_content, count = re.subn(

                pattern,

                replacement,

                updated_content,

                flags=re.MULTILINE

            )



            # Attribute does not exist

            if count == 0:


                updated_content = (

                    self.add_attribute(

                        updated_content,

                        attribute,

                        terraform_value

                    )

                )



        return updated_content



    # -----------------------------------------------------
    # Convert Python Value to HCL
    # -----------------------------------------------------

    def convert_to_hcl(
        self,
        value: Any
    ) -> str:

        """
        Convert values into terraform syntax.
        """


        if isinstance(
            value,
            str
        ):

            return f'"{value}"'



        if isinstance(
            value,
            bool
        ):

            return str(
                value
            ).lower()



        if isinstance(
            list,
            type(value)
        ):

            return json.dumps(
                value
            )



        if isinstance(
            dict,
            type(value)
        ):

            return json.dumps(
                value,
                indent=2
            )



        return str(value)



    # -----------------------------------------------------
    # Add New Attribute
    # -----------------------------------------------------

    def add_attribute(
        self,
        block_content: str,
        attribute: str,
        value: str
    ) -> str:

        """
        Add missing terraform argument.
        """


        lines = block_content.splitlines()



        if len(lines) < 2:

            return block_content



        insert_position = len(lines) - 1



        lines.insert(

            insert_position,

            f"  {attribute} = {value}"

        )



        return "\n".join(

            lines

        )



    # -----------------------------------------------------
    # Replace Block Content
    # -----------------------------------------------------

    def replace_block(
        self,
        content: str,
        block,
        new_block: str
    ) -> str:

        """
        Replace only required terraform block.
        """


        return (

            content[

                :block["start"]

            ]

            +

            new_block

            +

            content[

                block["end"]:

            ]

        )



    # -----------------------------------------------------
    # Apply Single Change
    # -----------------------------------------------------

    def apply_change(
        self,
        patch: Dict[str, Any]
    ) -> bool:
        """
        Apply one terraform modification.
        """


        file_path = Path(

            patch.get(

                "source_file"

            )

        )


        if not file_path.exists():

            logger.error(

                "Terraform file missing: %s",

                file_path

            )


            return False



        content = self.read_file(

            file_path

        )



        block = self.find_block(

            content,

            patch.get(

                "resource_type"

            ),

            patch.get(

                "resource_name"

            )

        )



        if not block:


            logger.error(

                "Block not found: %s",

                patch.get(

                    "terraform_address"

                )

            )


            return False



        self.create_backup(

            file_path

        )



        updated_block = self.update_attributes(

            block["content"],

            patch.get(

                "changes",

                {}

            )

        )



        updated_content = self.replace_block(

            content,

            block,

            updated_block

        )



        self.write_file(

            file_path,

            updated_content

        )



        self.report["modified_files"].append(

            {

                "file":

                    str(file_path),


                "resource":

                    patch.get(

                        "terraform_address"

                    )

            }

        )



        self.report["summary"]["success"] += 1



        return True
        # -----------------------------------------------------
    # Apply Patch Plan
    # -----------------------------------------------------

    def apply_patches(self):

        """
        Execute all patch operations.
        """


        changes = self.patch_plan.get(

            "changes",

            []

        )



        logger.info(

            "Applying %s terraform changes",

            len(changes)

        )



        for patch in changes:


            try:


                result = self.apply_change(

                    patch

                )


                if not result:


                    self.report["failed_changes"].append(

                        patch

                    )


                    self.report["summary"]["failed"] += 1



            except Exception as error:


                logger.exception(

                    "Failed applying patch: %s",

                    error

                )


                self.report["failed_changes"].append(

                    {

                        "patch":

                            patch,


                        "error":

                            str(error)

                    }

                )


                self.report["summary"]["failed"] += 1



    # -----------------------------------------------------
    # Save Execution Report
    # -----------------------------------------------------

    def save_report(self):

        """
        Save writer execution report.
        """


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

            "Writer report created: %s",

            self.report_file

        )



    # -----------------------------------------------------
    # Execute Writer
    # -----------------------------------------------------

    def execute(self):

        """
        Complete writer workflow.
        """


        logger.info(

            "Starting Terraform Writer"

        )


        self.load_patch_plan()



        self.apply_patches()



        self.save_report()



        logger.info(

            "Terraform Writer completed"

        )


        return self.report



# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def create_arguments():

    parser = argparse.ArgumentParser(

        description=

        "Enterprise Terraform Code Writer"

    )


    parser.add_argument(

        "--patch",

        default=

        DEFAULT_PATCH_FILE,

        help=

        "Terraform patch JSON file"

    )


    parser.add_argument(

        "--report",

        default=

        DEFAULT_REPORT_FILE,

        help=

        "Writer execution report"

    )


    return parser.parse_args()



# ---------------------------------------------------------
# Main Execution
# ---------------------------------------------------------

def main():


    args = create_arguments()



    try:


        writer = TerraformWriter(

            patch_file=args.patch,

            report_file=args.report

        )



        writer.execute()



        print(

            "\nTerraform files updated successfully"

        )


        print(

            f"Report: {args.report}"

        )



    except Exception as error:


        logger.exception(

            "Terraform writer failed: %s",

            error

        )


        exit(1)



if __name__ == "__main__":

    main()
