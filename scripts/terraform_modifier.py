import json
import os

DRIFT_FILE = "reports/drift.json"
RESOURCE_FILE = "reports/terraform_resources.json"
OUTPUT_FILE = "reports/change_request.json"


def load_json(path):
    if not os.path.exists(path):
        print(f"ERROR: {path} not found.")
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


drift = load_json(DRIFT_FILE)
resources = load_json(RESOURCE_FILE)

changes = []

print("=" * 80)
print("Preparing Terraform Changes")
print("=" * 80)

for item in drift:

    if "after" not in item:
        continue

    resource_type = item.get("type")

    matched = next(
        (
            r for r in resources
            if r["resource_type"] == resource_type
        ),
        None
    )

    if matched is None:
        print(f"No Terraform file found for {resource_type}")
        continue

    after = item.get("after") or {}

    change = {
        "resource_type": matched["resource_type"],
        "resource_name": matched["resource_name"],
        "file": matched["file"],
        "changes": after
    }

    changes.append(change)

    print(f"Resource : {matched['resource_type']}.{matched['resource_name']}")
    print(f"File     : {matched['file']}")
    print("-" * 80)

os.makedirs("reports", exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(changes, f, indent=4)

print()
print(f"Generated {OUTPUT_FILE}")
