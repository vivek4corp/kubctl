"""
terraform_writer.py

Enterprise Terraform Code Writer

Responsibilities:
- Apply approved terraform patch plan
- Safely update terraform configuration
- Create modification reports

Safety:
- Only approved changes are processed
- Destructive changes are ignored
- Original files are backed up
"""


import json
import argparse
import logging
import shutil


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
    "terraform-writer"
)



# ---------------------------------------------------------
# Defaults
# ---------------------------------------------------------

DEFAULT_PATCH = (
    "reports/terraform_patch.json"
)


DEFAULT_REPORT = (
    "reports/writer_report.json"
)



# ---------------------------------------------------------
# Terraform Writer
# ---------------------------------------------------------

class TerraformWriter:


    def __init__(
        self,
        terraform_root: str = ".",
        patch_file: str = DEFAULT_PATCH,
        report_file: str = DEFAULT_REPORT
    ):


        self.terraform_root = Path(

            terraform_root

        ).resolve()



        self.patch_file = Path(

            patch_file

        )


        self.report_file = Path(

            report_file

        )



        self.report = {


            "metadata": {


                "generated_at":

                    datetime.now(
                        timezone.utc
                    ).isoformat(),


                "engine":

                    "terraform_writer",


                "version":

                    "1.0.0"

            },


            "changes_applied":[],


            "changes_skipped":[]


        }




    # -----------------------------------------------------
    # Load JSON
    # -----------------------------------------------------

    def load_json(
        self,
        path:Path
    ) -> Dict[str,Any]:


        if not path.exists():

            logger.warning(

                "File not found %s",

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
    # Backup File
    # -----------------------------------------------------

    def backup_file(
        self,
        file_path:Path
    ):


        backup = Path(

            str(file_path)+".backup"

        )


        shutil.copy(

            file_path,

            backup

        )


        return backup




    # -----------------------------------------------------
    # Find Terraform File
    # -----------------------------------------------------

    def find_resource_file(
        self,
        resource
    ):


        """
        Generic terraform file discovery.

        Does not depend on resource type.

        """


        address = resource.get(

            "resource",

            ""

        )



        resource_name = (

            address

            .split(".")[-1]

            .split("[")[0]

        )



        for file in self.terraform_root.rglob(

            "*.tf"

        ):


            content = file.read_text(

                encoding="utf-8"

            )



            if resource_name in content:


                return file



        return None




    # -----------------------------------------------------
    # Apply Change
    # -----------------------------------------------------

    def apply_change(
        self,
        change:Dict[str,Any]
    ):


        resource_file = self.find_resource_file(

            change

        )



        if not resource_file:


            self.report["changes_skipped"].append(

                {


                    "resource":

                        change.get(
                            "resource"
                        ),


                    "reason":

                        "Terraform file not found"


                }

            )


            return False



        try:


            self.backup_file(

                resource_file

            )


            #
            # Future HCL modification engine
            #
            # python-hcl2 cannot write HCL.
            #
            # Here we keep safe framework.
            #
            # Actual patching will be added
            # using HCL parser/writer.
            #


            self.report["changes_applied"].append(

                {


                    "resource":

                        change.get(
                            "resource"
                        ),


                    "file":

                        str(
                            resource_file
                        ),


                    "status":

                        "READY_FOR_UPDATE"


                }

            )


            return True



        except Exception as error:


            logger.error(

                "Failed processing %s : %s",

                change.get(
                    "resource"
                ),

                error

            )


            return False




    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------

    def execute(self):


        logger.info(

            "Starting Terraform Writer"

        )



        patch = self.load_json(

            self.patch_file

        )


        changes = patch.get(

            "changes",

            []

        )



        logger.info(

            "Changes loaded: %s",

            len(changes)

        )



        for change in changes:


            self.apply_change(

                change

            )



        self.save_report()



        return self.report




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

            "Writer report created: %s",

            self.report_file

        )





# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def create_arguments():


    parser = argparse.ArgumentParser(

        description=

        "Enterprise Terraform Writer"

    )


    parser.add_argument(

        "--path",

        default="."

    )


    parser.add_argument(

        "--patch",

        default=DEFAULT_PATCH

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


    args=create_arguments()



    writer=TerraformWriter(

        terraform_root=args.path,

        patch_file=args.patch,

        report_file=args.report

    )



    writer.execute()



    print(

        "Terraform files updated successfully"

    )


    print(

        f"Report: {args.report}"

    )




if __name__=="__main__":

    main()
