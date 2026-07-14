"""
terraform_validator.py

Enterprise Terraform Validation Engine

Responsibilities:
- Execute terraform validation workflow
- Capture command output
- Generate validation report
- Provide CI/CD quality gate

Checks:
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
from datetime import datetime, timezone
from typing import Dict, Any



# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s | %(levelname)s | %(message)s"

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

                    datetime.now(
                        timezone.utc
                    ).isoformat(),


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
        command: list
    ):

        """
        Execute terraform command.
        """


        logger.info(

            "Running: %s",

            " ".join(command)

        )


        process = subprocess.run(

            command,

            cwd=self.terraform_path,

            capture_output=True,

            text=True

        )



        return {


            "command":

                " ".join(command),


            "success":

                process.returncode == 0,


            "return_code":

                process.returncode,


            "stdout":

                process.stdout,


            "stderr":

                process.stderr

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
        Add validation result.
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
        Validate terraform configuration.
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
        Execute validation workflow.
        """


        logger.info(

            "Starting terraform validation"

        )



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

    def validation_gate(self):

        """
        Decide pipeline status.
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
    # Terraform Directory Check
    # -----------------------------------------------------

    def validate_directory(self):

        """
        Ensure terraform files exist.
        """


        if not self.terraform_path.exists():


            logger.error(

                "Terraform directory missing"

            )


            return False



        files = list(

            self.terraform_path.rglob(

                "*.tf"

            )

        )



        if not files:


            logger.error(

                "No terraform files found"

            )


            return False



        return True



    # -----------------------------------------------------
    # Environment Information
    # -----------------------------------------------------

    def collect_environment_info(self):


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
    # Execute Validation
    # -----------------------------------------------------

    def execute_validation(self):


        logger.info(

            "Terraform validation started"

        )



        if not self.validate_directory():


            return False



        self.collect_environment_info()



        self.run_all_checks()



        return self.validation_gate()



    # -----------------------------------------------------
    # Save Report
    # -----------------------------------------------------

    def save_report(self):


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



        logger.info(

            "Validation report created: %s",

            self.report_file

        )



    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------

    def execute(self):


        status = self.execute_validation()



        self.save_report()



        return status





# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def create_arguments():


    parser = argparse.ArgumentParser(

        description=

        "Enterprise Terraform Validation Engine"

    )



    parser.add_argument(

        "--path",

        default=".",

        help="Terraform directory"

    )



    parser.add_argument(

        "--report",

        default=DEFAULT_REPORT,

        help="Validation report"

    )



    return parser.parse_args()





# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():


    args = create_arguments()



    validator = TerraformValidator(

        terraform_path=args.path,

        report_file=args.report

    )



    success = validator.execute()



    if success:


        print(

            "Terraform validation PASSED"

        )


        exit(0)



    else:


        print(

            "Terraform validation FAILED"

        )


        exit(1)




if __name__ == "__main__":

    main()
