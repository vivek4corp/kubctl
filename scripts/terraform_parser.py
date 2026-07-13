import os
import json
import hcl2

ROOT = "modules"
OUTPUT = "reports/terraform_resources.json"

resources = []


def parse_tf(tf_file):

    with open(tf_file, "r", encoding="utf-8") as f:
        data = hcl2.load(f)

    if "resource" not in data:
        return

    for resource in data["resource"]:

        for resource_type, value in resource.items():

            for resource_name, body in value.items():

                resources.append({
                    "file": tf_file,
                    "resource_type": resource_type,
                    "resource_name": resource_name,
                    "attributes": body
                })


for root, dirs, files in os.walk(ROOT):

    for file in files:

        if file.endswith(".tf"):

            parse_tf(os.path.join(root, file))

os.makedirs("reports", exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(resources, f, indent=4)

print("=" * 60)
print("Terraform Resources")
print("=" * 60)

for r in resources:

    print(r["resource_type"], "->", r["resource_name"])

print("\nSaved:", OUTPUT)
