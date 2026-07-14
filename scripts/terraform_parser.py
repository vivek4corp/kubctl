import json
import os

INVENTORY_FILE = "reports/terraform_inventory.json"
OUTPUT_FILE = "reports/terraform_resources.json"


def load_json(path):

    if not os.path.exists(path):
        print(f"{path} not found")
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


inventory = load_json(INVENTORY_FILE)

resources = []

print("=" * 80)
print("Terraform Resource Parser")
print("=" * 80)

for item in inventory:

    resource = {

        "module": item["module"],

        "directory": item["directory"],

        "file": item["file"],

        "resource_type": item["resource_type"],

        "resource_name": item["resource_name"],

        "attributes": item["attributes"]

    }

    resources.append(resource)

    print()

    print(f"Module        : {item['module']}")
    print(f"Resource Type : {item['resource_type']}")
    print(f"Resource Name : {item['resource_name']}")
    print(f"File          : {item['file']}")

    print("-" * 80)

os.makedirs("reports", exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(resources, f, indent=4)

print()
print("=" * 80)
print(f"Resources Parsed : {len(resources)}")
print(f"Saved            : {OUTPUT_FILE}")
print("=" * 80)
