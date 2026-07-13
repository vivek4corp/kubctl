import json
import os

os.makedirs("reports", exist_ok=True)

with open("environments/dev/tfplan.json") as f:
    plan = json.load(f)

changes = []

for resource in plan.get("resource_changes", []):

    actions = resource["change"]["actions"]

    if actions != ["no-op"]:

        changes.append({
            "resource": resource["address"],
            "action": ", ".join(actions),
            "changed_by": "Unknown",
            "time": "Unknown"
        })

with open("reports/drift.json", "w") as f:
    json.dump(changes, f, indent=4)

print(f"Detected {len(changes)} drifted resources.")
print("Saved reports/drift.json")
