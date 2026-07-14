import json
import os

DRIFT_FILE = "reports/drift.json"
RESOURCE_FILE = "reports/terraform_resources.json"
MODULE_FILE = "reports/module_mapping.json"

OUTPUT_FILE = "reports/terraform_patch.json"


def load_json(file):

    if not os.path.exists(file):
        return []

    with open(file, encoding="utf-8") as f:
        return json.load(f)


drift = load_json(DRIFT_FILE)
resources = load_json(RESOURCE_FILE)
modules = load_json(MODULE_FILE)

patches = []

print("=" * 80)
print("Generating Terraform Patch")
print("=" * 80)

for item in drift:

    resource_address = item.get("resource")
    resource_type = item.get("type")

    after = item.get("after", {})
    before = item.get("before", {})

    tf_resource = next(
        (
            r
            for r in resources
            if r["resource_type"] == resource_type
        ),
        None,
    )

    if tf_resource is None:
        continue

    module = next(
        (
            m
            for m in modules
            if resource_address.startswith(f"module.{m['module']}")
        ),
        None,
    )

    operations = []

    ############################################################
    # Replace / Add
    ############################################################

    for key, value in after.items():

        if isinstance(value, (list, dict)):
            continue

        if before is None:

            operations.append(
                {
                    "op": "add",
                    "attribute": key,
                    "value": value,
                }
            )

            continue

        if key not in before:

            operations.append(
                {
                    "op": "add",
                    "attribute": key,
                    "value": value,
                }
            )

            continue

        if before[key] != value:

            operations.append(
                {
                    "op": "replace",
                    "attribute": key,
                    "value": value,
                }
            )

    ############################################################
    # Remove
    ############################################################

    if before:

        for key in before:

            if key not in after:

                operations.append(
                    {
                        "op": "remove",
                        "attribute": key,
                    }
                )

    patches.append(
        {
            "resource": resource_address,
            "module": module["module"] if module else None,
            "directory": module["directory"] if module else None,
            "file": tf_resource["file"],
            "resource_type": resource_type,
            "resource_name": tf_resource["resource_name"],
            "operations": operations,
        }
    )

with open(OUTPUT_FILE, "w") as f:
    json.dump(patches, f, indent=4)

print()
print(f"Generated {OUTPUT_FILE}")
