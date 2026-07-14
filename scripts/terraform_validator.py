"""
terraform_validator.py

Enterprise Terraform Validation Engine

Responsibilities:
- Execute terraform validation workflow
- Capture command output
- Generate validation report
- Provide CI/CD quality gate

Supported checks:
- terraform fmt
- terraform init
- terraform validate
- terraform plan

No provider/resource assumptions.
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

    "terraform-validator"

)



# ---------------------------------------------------------
# Defaults
# ---------------------------------------------------------

DEFAULT_REPORT = (

    "reports/terraform_validation.json"

)



# ---------------------------------------------------------
# Terraform Validator Engine
# ---------------------------------------------------------

class TerraformValidator:


    def __init__(
        self,
        terraform_path: str = ".",
        report_file: str = DEFAULT_REPORT
    ):


        self.terraform_path = Path(

            terraform_path

        ).resolve()



        self.report_file = Path(

            report_file

        )



        self.report = {


            "metadata":

            {

                "generated_at":

                    datetime.utcnow().isoformat(),


                "engine":

                    "terraform_validator",


                "version":

                    "1.0.0"

            },


            "checks": [],


            "summary":

            {

                "passed": 0,

                "failed": 0

            }

        }



    # -----------------------------------------------------
    # Execute Command
    # -----------------------------------------------------

    def run_command(
        self,
        command: List[str]
    ) -> Dict[str, Any]:

        """
        Execute terraform command safely.
        """


        logger.info(

            "Running: %s",

            " ".join(command)

        )


        try:


            result = subprocess.run(

                command,

                cwd=self.terraform_path,

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
    # Add Check Result
    # -----------------------------------------------------

    def add_check_result(
        self,
        name: str,
        result: Dict[str, Any]
    ):

        """
        Add validation result to report.
        """


        check = {


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



        self.report["checks"].append(

            check

        )



        if result.get(

            "success"

        ):

            self.report["summary"]["passed"] += 1


        else:

            self.report["summary"]["failed"] += 1



    # -----------------------------------------------------
    # Terraform Format Check
    # -----------------------------------------------------

    def run_fmt(self):

        """
        Execute terraform fmt check.
        """


        result = self.run_command(

            [

                "terraform",

                "fmt",

                "-check",

                "-recursive"

            ]

        )



        self.add_check_result(

            "terraform_fmt",

            result

        )



        return result.get(

            "success"

        )



    # -----------------------------------------------------
    # Terraform Init
    # -----------------------------------------------------

    def run_init(self):

        """
        Initialize terraform.
        """


        result = self.run_command(

            [

                "terraform",

                "init",

                "-input=false"

            ]

        )



        self.add_check_result(

            "terraform_init",

            result

        )



        return result.get(

            "success"

        )



    # -----------------------------------------------------
    # Terraform Validate
    # -----------------------------------------------------

    def run_validate(self):

        """
        Validate terraform syntax.
        """


        result = self.run_command(

            [

                "terraform",

                "validate",

                "-json"

            ]

        )



        self.add_check_result(

            "terraform_validate",

            result

        )


        return result.get(

            "success"

        )



    # -----------------------------------------------------
    # Terraform Plan
    # -----------------------------------------------------

    def run_plan(self):

        """
        Execute terraform plan.
        """


        result = self.run_command(

            [

                "terraform",

                "plan",

                "-input=false",

                "-no-color"

            ]

        )



        self.add_check_result(

            "terraform_plan",

            result

        )


        return result.get(

            "success"

        )



    # -----------------------------------------------------
    # Run Validation Pipeline
    # -----------------------------------------------------

    def run_all_checks(self):

        """
        Execute complete validation flow.
        """


        logger.info(

            "Starting terraform validation"

        )



        self.run_fmt()



        init_success = self.run_init()



        if init_success:


            self.run_validate()


            self.run_plan()



        else:


            logger.error(

                "Terraform init failed. Skipping remaining checks."

            )
            # -----------------------------------------------------
    # Validation Gate
    # -----------------------------------------------------

    def validation_gate(self) -> bool:
        """
        Decide pipeline status.

        Used by CI/CD.
        """

        failed_checks = []


        for check in self.report["checks"]:


            if not check.get(

                "success"

            ):

                failed_checks.append(

                    check["name"]

                )



        if failed_checks:


            self.report["gate"] = {


                "status":

                    "FAILED",


                "failed_checks":

                    failed_checks

            }


            logger.error(

                "Validation failed: %s",

                failed_checks

            )


            return False



        self.report["gate"] = {


            "status":

                "PASSED",


            "failed_checks":

                []

        }



        logger.info(

            "Validation gate passed"

        )


        return True



    # -----------------------------------------------------
    # Terraform Working Directory Check
    # -----------------------------------------------------

    def validate_directory(self) -> bool:

        """
        Ensure terraform files exist.
        """


        if not self.terraform_path.exists():


            logger.error(

                "Terraform directory not found: %s",

                self.terraform_path

            )


            return False



        terraform_files = list(

            self.terraform_path.rglob(

                "*.tf"

            )

        )



        if not terraform_files:


            logger.error(

                "No terraform files found"

            )


            return False



        return True



    # -----------------------------------------------------
    # Environment Information
    # -----------------------------------------------------

    def collect_environment_info(self):

        """
        Add execution metadata.
        """


        self.report["environment"] = {


            "terraform_directory":

                str(

                    self.terraform_path

                ),



            "terraform_files":

                len(

                    list(

                        self.terraform_path.rglob(

                            "*.tf"

                        )

                    )

                ),



            "runner":

                os.environ.get(

                    "RUNNER_NAME",

                    "local"

                )

        }



    # -----------------------------------------------------
    # Execute Validation Workflow
    # -----------------------------------------------------

    def execute_validation(self):

        """
        Complete validation workflow.
        """


        logger.info(

            "Terraform validation started"

        )



        if not self.validate_directory():


            self.report["gate"] = {


                "status":

                    "FAILED",


                "reason":

                    "Invalid terraform directory"

            }


            return False



        self.collect_environment_info()



        self.run_all_checks()



        return self.validation_gate()
