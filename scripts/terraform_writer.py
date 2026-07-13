import json
import os
import re

CHANGE_FILE = "reports/change_request.json"


def replace_attribute(block, key, value):
    """
    Replace an existing Terraform attribute or add it if missing.
    """

    pattern = rf'(^\s*{re.escape(key)}\s*=\s*).*$'

    if isinstance(value, str):
        new_value = f'"{value}"'
    elif isinstance(value, bool):
        new_value = str(value).lower()
    else:
        new_value = str(value)

    if re.search(pattern, block, flags=re.MULTILINE):
        block = re.sub(
            pattern,
            rf"\1{new_value}",
            block,
            flags=re.MULTILINE,
        )
    else:
        lines = block.splitlines()
        lines.insert(-1, f'  {key} = {new_value}')
        block = "\n".join(lines)

    return block


with open(CHANGE_FILE, "r") as f:
    changes = json.load(f)

for change in changes:

    tf_file = change["file"]

    if not os.path.exists(tf_file):
        print(f"{tf_file} not found")
        continue

    with open(tf_file, "r") as f:
        content = f.read()

    resource_type = change["resource_type"]
    resource_name = change["resource_name"]

    pattern = (
        rf'(resource\s+"{resource_type}"\s+"{resource_name}"\s*\{{'
        rf'[\s\S]*?\n\}})'
    )

    match = re.search(pattern, content)

    if not match:
        print(f"Resource not found: {resource_type}.{resource_name}")
        continue

    block = match.group(1)

    for key, value in change["changes"].items():
        block = replace_attribute(block, key, value)

    content = content.replace(match.group(1), block)

    with open(tf_file, "w") as f:
        f.write(content)

    print(f"Updated {tf_file}")

print("\nTerraform files updated.")
