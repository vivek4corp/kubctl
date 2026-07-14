"""
activitylog.py

Terraform Drift Activity Log Enrichment

Reads:
    reports/drift.json

Updates:
    changed_by
    time

Keeps:
    metadata
    summary
    resources
"""


import json
import subprocess
import os


from pathlib import Path



# --------------------------------------------------
# Setup
# --------------------------------------------------

os.makedirs(
    "reports",
    exist_ok=True
)


DRIFT_FILE = Path(
    "reports/drift.json"
)



if not DRIFT_FILE.exists():

    raise FileNotFoundError(
        "reports/drift.json not found"
    )



# --------------------------------------------------
# Load Drift Report
# --------------------------------------------------

with open(
    DRIFT_FILE,
    "r",
    encoding="utf-8"
) as file:

    drift_report = json.load(file)



#
# New format support
#

if isinstance(
    drift_report,
    dict
):

    resources = drift_report.get(
        "resources",
        []
    )


else:

    resources = drift_report



print(
    f"Activity Log enrichment started for {len(resources)} resource(s)"
)




# --------------------------------------------------
# Activity Log Lookup
# --------------------------------------------------

for item in resources:


    resource = item.get(
        "resource"
    )


    print(
        f"Checking Activity Logs for {resource}"
    )


    try:


        cmd = [

            "az",

            "monitor",

            "activity-log",

            "list",

            "--resource-id",

            resource,

            "--max-events",

            "1",

            "--offset",

            "30d",

            "--output",

            "json"

        ]



        output = subprocess.check_output(

            cmd,

            stderr=subprocess.STDOUT

        ).decode()



        logs = json.loads(
            output
        )



        if logs:


            latest = logs[0]


            item["changed_by"] = latest.get(

                "caller",

                "Unknown"

            )


            item["time"] = latest.get(

                "eventTimestamp",

                "Unknown"

            )


        else:


            item["changed_by"] = "Unknown"


            item["time"] = "Unknown"



    except Exception as ex:


        print(
            f"Activity log lookup failed: {ex}"
        )


        item["changed_by"] = "Unknown"


        item["time"] = "Unknown"





# --------------------------------------------------
# Save Updated Report
# --------------------------------------------------

if isinstance(
    drift_report,
    dict
):

    drift_report["resources"] = resources


    output = drift_report


else:

    output = resources




with open(
    DRIFT_FILE,
    "w",
    encoding="utf-8"
) as file:


    json.dump(

        output,

        file,

        indent=4

    )



print(
    "Activity Log enrichment completed."
)
