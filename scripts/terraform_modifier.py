import json
import os

DRIFT_FILE = "reports/drift.json"
RESOURCE_FILE = "reports/terraform_resources.json"
MODULE_FILE = "reports/module_mapping.json"
OUTPUT_FILE = "reports/terraform_changes.json"


def load_json(path):
    if not os.path.exists(path):
        print(f"{path} not found")
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


drift = load_json(DRIFT_FILE)
resources = load_json(RESOURCE_FILE)
modules = load_json(MODULE_FILE)

changes = []

print("=" * 80)
print("Terraform Change Generator")
print("=" * 80)

for drift_resource in drift:

    resource_address = drift_resource.get("resource")
    resource_type = drift_resource.get("type")
    actions = drift_resource.get("actions", [])
    after = drift_resource.get("after", {})

    if not resource_address:
        continue

    ###########################################################
    # Find Terraform Resource
    ###########################################################

    tf_resource = None

    for resource in resources:

        if resource["resource_type"] == resource_type:
            tf_resource = resource
            break

    if tf_resource is None:
        print(f"Skipping {resource_address}")
        continue

    ###########################################################
    # Find Module
    ###########################################################

    module_name = None
    module_directory = None

    for module in modules:

        if resource_address.startswith(f"module.{module['module']}"):

            module_name = module["module"]
            module_directory = module["directory"]
            break

    ###########################################################
    # Prepare Attribute Changes
    ###########################################################

    attribute_changes = []

    for key, value in after.items():

        if isinstance(value, (dict, list)):
            continue

        attribute_changes.append({
            "attribute": key,
            "value": value
        })

    ###########################################################
    # Build Change Object
    ###########################################################

    change = {
        "resource": resource_address,
        "resource_type": resource_type,
        "resource_name": tf_resource["resource_name"],
        "module": module_name,
        "directory": module_directory,
        "file": tf_resource["file"],
        "actions": actions,
        "changes": attribute_changes
    }

    changes.append(change)

    print()
    print(f"Resource : {resource_address}")
    print(f"Module   : {module_name}")
    print(f"File     : {tf_resource['file']}")
    print(f"Changes  : {len(attribute_changes)}")
    print("-" * 80)

###########################################################
# Save
###########################################################

os.makedirs("reports", exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(changes, f, indent=4)

print()
print("=" * 80)
print(f"Changes Generated : {len(changes)}")
print(f"Saved             : {OUTPUT_FILE}")
print("=" * 80)
