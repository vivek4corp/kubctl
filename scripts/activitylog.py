import json
import subprocess
import os

os.makedirs("reports", exist_ok=True)

with open("reports/drift.json", "r") as f:
    drift = json.load(f)

for item in drift:

    resource = item["resource"]

    print(f"Checking Activity Logs for {resource}")

    try:

        cmd = [
            "az",
            "monitor",
            "activity-log",
            "list",
            "--max-events",
            "1",
            "--offset",
            "30d",
            "--output",
            "json"
        ]

        output = subprocess.check_output(cmd).decode()

        logs = json.loads(output)

        if logs:

            item["changed_by"] = logs[0].get("caller", "Unknown")
            item["time"] = logs[0].get("eventTimestamp", "Unknown")

        else:

            item["changed_by"] = "Unknown"
            item["time"] = "Unknown"

    except Exception as ex:

        print(ex)

        item["changed_by"] = "Unknown"
        item["time"] = "Unknown"

with open("reports/drift.json", "w") as f:
    json.dump(drift, f, indent=4)

print("Activity Log enrichment completed.")
