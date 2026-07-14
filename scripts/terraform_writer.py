import json
import os
import re

CHANGE_FILE = "reports/change_request.json"


def tf_value(value):
    """Convert Python value to Terraform syntax."""

    if value is None:
        return "null"

    if isinstance(value, bool):
        return str(value).lower()

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, str):
        return f'"{value}"'

    return json.dumps(value)


def update_resource(tf_file, resource_type, resource_name, changes):

    if not os.path.exists(tf_file):
        print(f"File not found : {tf_file}")
        return

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

    block = match.group(1)

    for key, value in changes.items():

        # Skip nested objects/lists for now
        if isinstance(value, (dict, list)):
            continue

        attr_pattern = rf'(^\s*{re.escape(key)}\s*=\s*).*$'

        if re.search(attr_pattern, block, flags=re.MULTILINE):

            block = re.sub(
                attr_pattern,
                rf'\1{tf_value(value)}',
                block,
                flags=re.MULTILINE
            )

    content = content.replace(match.group(1), block)

    with open(tf_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated : {tf_file}")


def main():

    if not os.path.exists(CHANGE_FILE):
        print("No change_request.json found.")
        return

    with open(CHANGE_FILE, "r", encoding="utf-8") as f:
        requests = json.load(f)

    if len(requests) == 0:
        print("No Terraform changes required.")
        return

    print("=" * 80)
    print("Terraform Writer")
    print("=" * 80)

    for item in requests:

        update_resource(
            tf_file=item["file"],
            resource_type=item["resource_type"],
            resource_name=item["resource_name"],
            changes=item["changes"]
        )

    print("\nTerraform files updated successfully.")


if __name__ == "__main__":
    main()
