"""
drift.py

Enterprise Terraform Drift Detection Engine

Input:
- terraform show -json tfplan.json

Output:
- reports/drift.json

Features:
- Detect create/update/delete/replace
- Risk classification
- Change generator compatible output
"""


import json
import os

from pathlib import Path
from datetime import datetime, timezone



# --------------------------------------------------
# Paths
# --------------------------------------------------

REPORT_DIR = Path("reports")

REPORT_DIR.mkdir(
    exist_ok=True
)


PLAN_FILE = Path(
    "environments/dev/tfplan.json"
)


OUTPUT_FILE = Path(
    "reports/drift.json"
)



# --------------------------------------------------
# Validate Plan
# --------------------------------------------------

if not PLAN_FILE.exists():

    raise FileNotFoundError(
        f"{PLAN_FILE} not found"
    )



# --------------------------------------------------
# Load Terraform Plan
# --------------------------------------------------

with PLAN_FILE.open(
    "r",
    encoding="utf-8"
) as file:

    plan = json.load(file)



# --------------------------------------------------
# Risk Engine
# --------------------------------------------------

def calculate_risk(actions):


    if "delete" in actions and "create" in actions:

        return "HIGH"


    if "replace" in actions:

        return "HIGH"


    if "delete" in actions:

        return "HIGH"


    if "update" in actions:

        return "MEDIUM"


    if "create" in actions:

        return "LOW"


    return "LOW"





# --------------------------------------------------
# Drift Detection
# --------------------------------------------------

resources = []


for resource in plan.get(
    "resource_changes",
    []
):


    actions = resource.get(
        "change",
        {}
    ).get(
        "actions",
        []
    )


    if actions == ["no-op"]:

        continue



    if not actions:

        continue



    action_string = ",".join(
        actions
    )



    item = {


        "resource":

            resource.get(
                "address"
            ),



        "type":

            resource.get(
                "type"
            ),



        "name":

            resource.get(
                "name"
            ),



        "provider":

            resource.get(
                "provider_name",
                ""
            ),



        #
        # Used by change_generator
        #

        "action":

            action_string,



        "actions":

            actions,



        "before":

            resource.get(
                "change",
                {}
            ).get(
                "before"
            ),



        "after":

            resource.get(
                "change",
                {}
            ).get(
                "after"
            ),



        "risk":

            calculate_risk(
                actions
            ),



        "changed_by":

            "",



        "time":

            "",



        "recommendation":

            ""

    }



    resources.append(
        item
    )





# --------------------------------------------------
# Final Report
# --------------------------------------------------

report = {


    "metadata": {


        "generated_at":

            datetime.now(
                timezone.utc
            ).isoformat(),


        "engine":

            "terraform_drift_detector",


        "version":

            "2.0.0"

    },


    "summary": {


        "total_changes":

            len(resources),


        "high_risk":

            len(
                [
                    r for r in resources
                    if r["risk"] == "HIGH"
                ]
            ),


        "medium_risk":

            len(
                [
                    r for r in resources
                    if r["risk"] == "MEDIUM"
                ]
            ),


        "low_risk":

            len(
                [
                    r for r in resources
                    if r["risk"] == "LOW"
                ]
            )

    },


    "resources":

        resources

}





# --------------------------------------------------
# Save
# --------------------------------------------------

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8"
) as outfile:


    json.dump(
        report,
        outfile,
        indent=4
    )





# --------------------------------------------------
# Console
# --------------------------------------------------

print("=" * 70)


if not resources:


    print(
        "✅ No drift detected."
    )


else:


    print(
        f"✅ Drift detected in {len(resources)} resource(s)\n"
    )


    for item in resources:


        print(
            f"Resource : {item['resource']}"
        )


        print(
            f"Type     : {item['type']}"
        )


        print(
            f"Action   : {item['action']}"
        )


        print(
            f"Risk     : {item['risk']}"
        )


        print(
            "-" * 70
        )



print(
    "\nDrift report written to reports/drift.json"
)
