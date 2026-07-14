"""
terraform_parser.py

Enterprise Terraform Resource Parser

Responsibilities:
- Scan Terraform repository
- Parse Terraform HCL files
- Build resource inventory
- Generate normalized resource metadata

Dependencies:
    pip install python-hcl2
"""

import os
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

import hcl2


# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT
)

logger = logging.getLogger("terraform-parser")


# ---------------------------------------------------------
# Default Configuration
# ---------------------------------------------------------

DEFAULT_OUTPUT = "reports/terraform_resources.json"


TERRAFORM_EXTENSIONS = [
    ".tf"
]


IGNORE_DIRECTORIES = {
    ".git",
    ".terraform",
    ".github",
    "node_modules",
    "__pycache__"
}


# ---------------------------------------------------------
# Terraform Parser Engine
# ---------------------------------------------------------

class TerraformParser:
    """
    Generic Terraform repository parser.

    This class does not know:
    - Azure
    - AWS
    - GCP
    - resource names
    - module names

    It only understands Terraform structure.
    """


    def __init__(
        self,
        repository_path: str,
        output_file: str = DEFAULT_OUTPUT
    ):

        self.repository_path = Path(
            repository_path
        ).resolve()


        self.output_file = Path(
            output_file
        )


        self.inventory = {

            "metadata": {

                "generated_at":
                    datetime.utcnow().isoformat(),

                "repository":
                    str(self.repository_path),

                "parser_version":
                    "1.0.0"
            },


            "terraform_files": [],


            "providers": [],


            "modules": [],


            "resources": [],


            "data_sources": [],


            "variables": [],


            "outputs": [],


            "locals": []
        }



    # -----------------------------------------------------
    # File Discovery
    # -----------------------------------------------------

    def discover_terraform_files(self) -> List[Path]:
        """
        Recursively find terraform files.
        """

        logger.info(
            "Scanning terraform files..."
        )


        terraform_files = []


        for root, directories, files in os.walk(
            self.repository_path
        ):


            directories[:] = [
                d for d in directories
                if d not in IGNORE_DIRECTORIES
            ]


            for file in files:


                file_path = Path(root) / file


                if file_path.suffix in TERRAFORM_EXTENSIONS:

                    terraform_files.append(
                        file_path
                    )



        logger.info(
            "Terraform files found: %s",
            len(terraform_files)
        )


        return terraform_files



    # -----------------------------------------------------
    # File Reader
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
                "Unable to read file %s : %s",
                file_path,
                error
            )

            return ""



    # -----------------------------------------------------
    # HCL Parser Wrapper
    # -----------------------------------------------------

    def parse_hcl(
        self,
        content: str,
        file_path: Path
    ) -> Dict[str, Any]:
        """
        Convert Terraform HCL into python dictionary.
        """

        try:

            return hcl2.loads(
                content
            )


        except Exception as error:

            logger.error(
                "HCL parsing failed for %s : %s",
                file_path,
                error
            )

            return {}
        # -----------------------------------------------------
    # Generic Block Extraction
    # -----------------------------------------------------

    def extract_blocks(
        self,
        parsed_hcl: Dict[str, Any],
        block_name: str
    ) -> List[Any]:
        """
        Generic Terraform block extractor.

        Supports:
        - resource
        - data
        - module
        - provider
        - variable
        - output
        - locals
        """

        try:

            return parsed_hcl.get(
                block_name,
                []
            )

        except Exception as error:

            logger.error(
                "Unable to extract block %s : %s",
                block_name,
                error
            )

            return []



    # -----------------------------------------------------
    # Provider Extraction
    # -----------------------------------------------------

    def extract_providers(
        self,
        parsed_hcl: Dict[str, Any],
        file_path: Path
    ):

        providers = self.extract_blocks(
            parsed_hcl,
            "provider"
        )


        for provider in providers:

            for name, configuration in provider.items():

                self.inventory["providers"].append(
                    {
                        "name": name,
                        "configuration": configuration,
                        "source_file": str(file_path)
                    }
                )



    # -----------------------------------------------------
    # Module Extraction
    # -----------------------------------------------------

    def extract_modules(
        self,
        parsed_hcl: Dict[str, Any],
        file_path: Path
    ):

        modules = self.extract_blocks(
            parsed_hcl,
            "module"
        )


        for module in modules:

            for name, configuration in module.items():

                self.inventory["modules"].append(
                    {
                        "name": name,
                        "configuration": configuration,
                        "source_file": str(file_path)
                    }
                )



    # -----------------------------------------------------
    # Resource Extraction
    # -----------------------------------------------------

    def extract_resources(
        self,
        parsed_hcl: Dict[str, Any],
        file_path: Path
    ):

        resources = self.extract_blocks(
            parsed_hcl,
            "resource"
        )


        for resource_group in resources:


            for resource_type, instances in resource_group.items():


                for resource_name, configuration in instances.items():


                    resource_object = {


                        "type":
                            resource_type,


                        "name":
                            resource_name,


                        "address":
                            f"{resource_type}.{resource_name}",


                        "configuration":
                            configuration,


                        "source_file":
                            str(file_path)

                    }


                    self.inventory["resources"].append(
                        resource_object
                    )



    # -----------------------------------------------------
    # Data Source Extraction
    # -----------------------------------------------------

    def extract_data_sources(
        self,
        parsed_hcl: Dict[str, Any],
        file_path: Path
    ):


        data_sources = self.extract_blocks(
            parsed_hcl,
            "data"
        )


        for data_group in data_sources:


            for data_type, instances in data_group.items():


                for data_name, configuration in instances.items():


                    self.inventory["data_sources"].append(

                        {

                            "type":
                                data_type,


                            "name":
                                data_name,


                            "address":
                                f"data.{data_type}.{data_name}",


                            "configuration":
                                configuration,


                            "source_file":
                                str(file_path)

                        }

                    )



    # -----------------------------------------------------
    # Variable Extraction
    # -----------------------------------------------------

    def extract_variables(
        self,
        parsed_hcl: Dict[str, Any],
        file_path: Path
    ):


        variables = self.extract_blocks(
            parsed_hcl,
            "variable"
        )


        for variable in variables:


            for name, configuration in variable.items():


                self.inventory["variables"].append(

                    {

                        "name":
                            name,


                        "configuration":
                            configuration,


                        "source_file":
                            str(file_path)

                    }

                )



    # -----------------------------------------------------
    # Output Extraction
    # -----------------------------------------------------

    def extract_outputs(
        self,
        parsed_hcl: Dict[str, Any],
        file_path: Path
    ):


        outputs = self.extract_blocks(
            parsed_hcl,
            "output"
        )


        for output in outputs:


            for name, configuration in output.items():


                self.inventory["outputs"].append(

                    {

                        "name":
                            name,


                        "configuration":
                            configuration,


                        "source_file":
                            str(file_path)

                    }

                )



    # -----------------------------------------------------
    # Local Values Extraction
    # -----------------------------------------------------

    def extract_locals(
        self,
        parsed_hcl: Dict[str, Any],
        file_path: Path
    ):


        locals_blocks = self.extract_blocks(
            parsed_hcl,
            "locals"
        )


        for local_block in locals_blocks:


            self.inventory["locals"].append(

                {

                    "configuration":
                        local_block,


                    "source_file":
                        str(file_path)

                }

            )
        # -----------------------------------------------------
    # Process Single Terraform File
    # -----------------------------------------------------

    def process_file(
        self,
        file_path: Path
    ):
        """
        Complete processing pipeline for one .tf file.
        """

        logger.info(
            "Processing: %s",
            file_path
        )


        content = self.read_file(
            file_path
        )


        if not content.strip():

            logger.warning(
                "Empty terraform file skipped: %s",
                file_path
            )

            return



        parsed_hcl = self.parse_hcl(
            content,
            file_path
        )


        if not parsed_hcl:

            return



        self.inventory["terraform_files"].append(

            {

                "file":
                    str(file_path),


                "size":
                    file_path.stat().st_size

            }

        )



        self.extract_providers(
            parsed_hcl,
            file_path
        )


        self.extract_modules(
            parsed_hcl,
            file_path
        )


        self.extract_resources(
            parsed_hcl,
            file_path
        )


        self.extract_data_sources(
            parsed_hcl,
            file_path
        )


        self.extract_variables(
            parsed_hcl,
            file_path
        )


        self.extract_outputs(
            parsed_hcl,
            file_path
        )


        self.extract_locals(
            parsed_hcl,
            file_path
        )



    # -----------------------------------------------------
    # Resource Normalization
    # -----------------------------------------------------

    def normalize_resources(self):
        """
        Add enterprise metadata to resources.

        This layer prepares data for:
        - drift detection
        - modification engine
        - terraform writer
        """

        normalized = []


        for index, resource in enumerate(

            self.inventory["resources"],

            start=1

        ):


            normalized_resource = {


                "id":

                    index,



                "terraform_address":

                    resource.get(
                        "address"
                    ),



                "resource_type":

                    resource.get(
                        "type"
                    ),



                "resource_name":

                    resource.get(
                        "name"
                    ),



                "configuration":

                    resource.get(
                        "configuration"
                    ),



                "source":

                    {

                        "file":

                            resource.get(
                                "source_file"
                            )

                    }



            }



            normalized.append(
                normalized_resource
            )



        self.inventory["resources"] = normalized



    # -----------------------------------------------------
    # Resource Lookup Index
    # -----------------------------------------------------

    def build_resource_index(self):
        """
        Creates quick lookup map.

        Example:

        {
          "azurerm_resource.foo":
          {
             metadata
          }
        }

        """

        resource_index = {}



        for resource in self.inventory["resources"]:


            address = resource.get(
                "terraform_address"
            )


            resource_index[address] = resource



        self.inventory["resource_index"] = resource_index



    # -----------------------------------------------------
    # Duplicate Detection
    # -----------------------------------------------------

    def detect_duplicates(self):

        """
        Detect duplicate terraform addresses.
        """

        seen = set()

        duplicates = []


        for resource in self.inventory["resources"]:


            address = resource.get(
                "terraform_address"
            )


            if address in seen:

                duplicates.append(
                    address
                )


            else:

                seen.add(
                    address
                )



        self.inventory["duplicates"] = duplicates



        if duplicates:

            logger.warning(
                "Duplicate resources detected: %s",
                duplicates
            )



    # -----------------------------------------------------
    # Repository Processing
    # -----------------------------------------------------

    def parse_repository(self):
        """
        Main parser execution.
        """


        terraform_files = (
            self.discover_terraform_files()
        )


        for file_path in terraform_files:

            self.process_file(
                file_path
            )



        logger.info(
            "Normalizing resources..."
        )


        self.normalize_resources()



        logger.info(
            "Building resource index..."
        )


        self.build_resource_index()



        logger.info(
            "Checking duplicates..."
        )


        self.detect_duplicates()



        return self.inventory
    # -----------------------------------------------------
    # Save Inventory Report
    # -----------------------------------------------------

    def save_report(self):
        """
        Write terraform inventory JSON report.
        """

        try:

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

                    self.inventory,

                    file,

                    indent=4,

                    default=str

                )


            logger.info(
                "Terraform inventory created: %s",
                self.output_file
            )


        except Exception as error:

            logger.error(
                "Failed writing report: %s",
                error
            )

            raise



    # -----------------------------------------------------
    # Parser Execution
    # -----------------------------------------------------

    def execute(self):
        """
        Complete parser workflow.
        """


        logger.info(
            "Starting Terraform Parser"
        )


        self.parse_repository()



        self.save_report()



        logger.info(
            "Terraform Parser completed successfully"
        )


        return self.inventory



# ---------------------------------------------------------
# Command Line Interface
# ---------------------------------------------------------

def create_arguments():

    parser = argparse.ArgumentParser(

        description=
        "Enterprise Terraform Resource Parser"

    )


    parser.add_argument(

        "--repo",

        required=False,

        default=".",

        help=
        "Terraform repository path"

    )


    parser.add_argument(

        "--output",

        required=False,

        default=DEFAULT_OUTPUT,

        help=
        "Output JSON report path"

    )


    return parser.parse_args()



# ---------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------

def main():


    args = create_arguments()



    parser = TerraformParser(

        repository_path=args.repo,

        output_file=args.output

    )



    try:


        parser.execute()



        print(

            "\nTerraform parsing completed"

        )



        print(

            f"Report: {args.output}"

        )



    except Exception as error:


        logger.exception(

            "Terraform parsing failed: %s",

            error

        )


        exit(1)




if __name__ == "__main__":

    main()
