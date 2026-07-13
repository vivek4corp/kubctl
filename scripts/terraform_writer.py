import json
import os
import re
import sys

CHANGE_FILE = "reports/change_request.json"


def terraform_value(value):
    """
    Convert Python values to Terraform syntax.
    """

    if isinstance(value, str):
        return f'"{value}"'

    if isinstance(value, bool):
        return str(value).lower()

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, list):
        return json.dumps(value)

    if isinstance(value, dict):
        return json.dumps(value)

    return json.dumps(value)


def replace_attribute(block, key, value):
    """
    Update an existing attribute or add it if it doesn't exist.
    """

    value = terraform_value(value)

    pattern = rf'(^\s*{re.escape(key)}\s*=\s*).*$'

    if re.search(pattern, block, flags=re.MULTILINE):

        block = re.sub(
            pattern,
            rf'\1{value}',
            block,
            flags=re.MULTILINE
        )

    else:

        lines = block.splitlines()

        # Insert before closing brace
        lines.insert(len(lines) - 1, f'  {key} = {value}')

        block = "\n".join(lines)

    return block


def update_resource(tf_file, resource_type, resource_name, changes):

    with open(tf_file, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = (
        rf'(resource\s+"{re.escape(resource_type)}"\s+"{re.escape(resource_name)}"\s*\{{'
        rf'[\s\S]*?\n\}})'
    )

    match = re.search(pattern, content)

    if not match:

        print(f"Resource not found : {resource_type}.{resource_name}")

        return

    resource_block = match.group(1)

    for key, value in changes.items():

        resource_block = replace_attribute(
            resource_block,
            key,
            value
        )

    content = content.replace(match.group(1), resource_block)

    with open(tf_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated : {tf_file}")


def main():

    if not os.path.exists(CHANGE_FILE):

        print(f"{CHANGE_FILE} not found")

        sys.exit(1)

    with open(CHANGE_FILE, "r", encoding="utf-8") as f:

        change_requests = json.load(f)

    if len(change_requests) == 0:

        print("No Terraform changes required.")

        return

    print("=" * 70)
    print("Terraform Writer")
    print("=" * 70)

    for change in change_requests:

        tf_file = change["file"]

        if not os.path.exists(tf_file):

            print(f"File not found : {tf_file}")

            continue

        update_resource(
            tf_file=tf_file,
            resource_type=change["resource_type"],
            resource_name=change["resource_name"],
            changes=change["changes"]
        )

    print("\nTerraform files updated successfully.")


if __name__ == "__main__":
    main()
