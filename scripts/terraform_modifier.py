import json
import os

DRIFT_FILE = "reports/drift.json"
RESOURCE_FILE = "reports/terraform_resources.json"
MODULE_FILE = "reports/module_mapping.json"
OUTPUT_FILE = "reports/terraform_changes.json"


def load(path):

    if not os.path.exists(path):
        print(f"{path} not found")
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


drift = load(DRIFT_FILE)
resources = load(RESOURCE_FILE)
modules = load(MODULE_FILE)

changes = []

print("=" * 80)
print("Preparing Terraform Changes")
print("=" * 80)

for item in drift:

    resource_address = item.get("resource")
    resource_type = item.get("type")
    after = item.get("after", {})
    actions = item.get("actions", [])

    if not after:
        continue

    ####################################################################
    # Find Resource Definition
    ####################################################################

    tf_resource = next(

        (
            r
            for r in resources
            if r["resource_type"] == resource_type
        ),

        None

    )

    if tf_resource is None:

        print(f"Terraform resource not found: {resource_type}")

        continue

    ####################################################################
    # Find Module
    ####################################################################

    module = next(

        (
            m
            for m in modules
            if resource_address.startswith("module." + m["module"])
        ),

        None

    )

    if module:

        directory = module["directory"]

    else:

        directory = os.path.dirname(tf_resource["file"])

    ####################################################################
    # Build Change Object
    ####################################################################

    change = {

        "resource": resource_address,

        "resource_type": resource_type,

        "resource_name": tf_resource["resource_name"],

        "file": tf_resource["file"],

        "module": directory,

        "actions": actions,

        "attributes": after

    }

    changes.append(change)

    print()
    print(f"Resource : {resource_address}")
    print(f"Type     : {resource_type}")
    print(f"File     : {tf_resource['file']}")
    print(f"Module   : {directory}")
    print("-" * 80)

os.makedirs("reports", exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

    json.dump(changes, f, indent=4)

print()
print(f"Generated {OUTPUT_FILE}")
