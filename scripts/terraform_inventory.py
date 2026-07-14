import os
import json
import hcl2

MODULE_ROOT = "modules"
OUTPUT_FILE = "reports/terraform_inventory.json"

inventory = []

print("=" * 80)
print("Terraform Inventory")
print("=" * 80)

if not os.path.exists(MODULE_ROOT):
    print("Modules directory not found.")
    exit(1)

for module_name in sorted(os.listdir(MODULE_ROOT)):

    module_dir = os.path.join(MODULE_ROOT, module_name)

    if not os.path.isdir(module_dir):
        continue

    print(f"\nScanning Module : {module_name}")

    for root, dirs, files in os.walk(module_dir):

        for file in files:

            if not file.endswith(".tf"):
                continue

            tf_file = os.path.join(root, file)

            try:

                with open(tf_file, "r", encoding="utf-8") as f:
                    data = hcl2.load(f)

            except Exception as ex:

                print(f"Unable to parse {tf_file}")
                print(ex)
                continue

            resources = data.get("resource", [])

            for resource in resources:

                for resource_type, values in resource.items():

                    for resource_name, attributes in values.items():

                        inventory.append(
                            {
                                "module": module_name,
                                "directory": module_dir,
                                "file": tf_file,
                                "resource_type": resource_type,
                                "resource_name": resource_name,
                                "attributes": list(attributes.keys())
                            }
                        )

                        print(f"  {resource_type}.{resource_name}")

os.makedirs("reports", exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(inventory, f, indent=4)

print()
print("=" * 80)
print(f"Resources Found : {len(inventory)}")
print(f"Inventory Saved : {OUTPUT_FILE}")
print("=" * 80)
