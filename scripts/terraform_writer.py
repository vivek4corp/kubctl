import json
import os
import shutil

CHANGE_FILE = "reports/terraform_changes.json"


def backup(file):

    backup_file = file + ".bak"

    if not os.path.exists(backup_file):

        shutil.copy(file, backup_file)


def tf_value(value):

    if value is None:
        return "null"

    if isinstance(value, bool):
        return str(value).lower()

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, str):
        return f'"{value}"'

    if isinstance(value, list):
        return json.dumps(value)

    if isinstance(value, dict):
        return json.dumps(value)

    return str(value)


def update_attribute(lines, key, value):

    for index, line in enumerate(lines):

        stripped = line.strip()

        if stripped.startswith(key + " ="):

            indent = line[:len(line) - len(line.lstrip())]

            lines[index] = f"{indent}{key} = {tf_value(value)}\n"

            return True

    return False


def process(change):

    file = change["file"]

    if not os.path.exists(file):

        print(f"Missing: {file}")

        return

    backup(file)

    with open(file, encoding="utf-8") as f:

        lines = f.readlines()

    changed = False

    for key, value in change["attributes"].items():

        if isinstance(value, (dict, list)):
            continue

        if update_attribute(lines, key, value):

            print(f"Updated {key}")

            changed = True

    if changed:

        with open(file, "w", encoding="utf-8") as f:

            f.writelines(lines)

        print(f"Saved {file}")

    else:

        print(f"No changes required in {file}")


def main():

    if not os.path.exists(CHANGE_FILE):

        print("terraform_changes.json not found")

        return

    with open(CHANGE_FILE, encoding="utf-8") as f:

        changes = json.load(f)

    print("=" * 70)
    print("Terraform Writer")
    print("=" * 70)

    for change in changes:

        process(change)

    print()
    print("Terraform update completed.")


if __name__ == "__main__":

    main()
