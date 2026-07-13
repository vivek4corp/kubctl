import json
import os
from pathlib import Path

# Create reports directory
os.makedirs("reports", exist_ok=True)

# Terraform plan JSON location
PLAN_FILE = Path("environments/dev/tfplan.json")

if not PLAN_FILE.exists():
    raise FileNotFoundError(f"{PLAN_FILE} not found")

with PLAN_FILE.open("r") as f:
    plan = json.load(f)

drift_report = []

for resource in plan.get("resource_changes", []):

    actions = resource["change"]["actions"]

    # Ignore resources with no changes
    if actions == ["no-op"]:
        continue

    before = resource["change"].get("before")
    after = resource["change"].get("after")

    drift = {
        "resource": resource["address"],
        "type": resource["type"],
        "name": resource["name"],
        "provider": resource.get("provider_name", ""),
        "actions": actions,
        "before": before,
        "after": after,
        "changed_by": "",
        "time": "",
        "risk": "",
        "recommendation": ""
    }

    drift_report.append(drift)

# Save JSON report
with open("reports/drift.json", "w") as outfile:
    json.dump(drift_report, outfile, indent=4)

print("=" * 70)

if not drift_report:
    print("✅ No drift detected.")
else:
    print(f"✅ Drift detected in {len(drift_report)} resource(s)\n")

    for item in drift_report:
        print(f"Resource : {item['resource']}")
        print(f"Type     : {item['type']}")
        print(f"Action   : {', '.join(item['actions'])}")
        print("-" * 70)

print("\nDrift report written to reports/drift.json")
