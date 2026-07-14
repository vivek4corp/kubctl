import os
import re
import json

ROOT = "."
OUTPUT = "reports/terraform_resources.json"

resources = []

for root, dirs, files in os.walk(ROOT):

    # Skip Terraform cache
    if ".terraform" in root:
        continue

    for file in files:

        if not file.endswith(".tf"):
            continue

        filepath = os.path.join(root, file)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = re.compile(
            r'resource\s+"([^"]+)"\s+"([^"]+)"',
            re.MULTILINE
        )

        for match in pattern.finditer(content):

            resources.append({
                "resource_type": match.group(1),
                "resource_name": match.group(2),
                "file": filepath
            })

os.makedirs("reports", exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(resources, f, indent=4)

print("=" * 70)
print("Terraform Resources")
print("=" * 70)

for r in resources:
    print(
        f'{r["resource_type"]} -> {r["resource_name"]} '
        f'({r["file"]})'
    )

print(f"\nSaved: {OUTPUT}")
