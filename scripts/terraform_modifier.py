import json
import os

DRIFT_FILE = "reports/drift.json"
RESOURCE_FILE = "reports/terraform_resources.json"
MODULE_FILE = "reports/module_mapping.json"
OUTPUT_FILE = "reports/change_request.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


drift = load_json(DRIFT_FILE)
resources = load_json(RESOURCE_FILE)
modules = load_json(MODULE_FILE)

changes = []

for d in drift:

    resource_type = d["type"]
    resource_name = d["name"]

    resource = next(
        (
            r for r in resources
            if r["resource_type"] == resource_type
            and r["resource_name"] == resource_name
        ),
        None,
    )

    if resource is None:
        continue

    change = {
        "resource_type": resource_type,
        "resource_name": resource_name,
        "file": resource["file"],
        "changes": {}
    }

    before = d.get("before") or {}
    after = d.get("after") or {}

    for key, value in after.items():
        if before.get(key) != value:
            change["changes"][key] = value

    if change["changes"]:
        changes.append(change)

os.makedirs("reports", exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(changes, f, indent=4)

print("=" * 60)
print("Change Requests")
print("=" * 60)

for c in changes:
    print(f"Resource : {c['resource_type']}.{c['resource_name']}")
    print(f"File     : {c['file']}")
    print("Changes  :")
    for k, v in c["changes"].items():
        print(f"  {k} = {v}")
    print("-" * 60)

print(f"\nSaved: {OUTPUT_FILE}")
