import json
import os
import shutil
import subprocess

PATCH_FILE = "reports/terraform_patch.json"
OUTPUT_FILE = "reports/terraform_writer.json"


def terraform_value(value):
    """Convert Python value to Terraform syntax."""

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


def backup(file_path):
    backup_file = file_path + ".bak"

    if not os.path.exists(backup_file):
        shutil.copy(file_path, backup_file)


def replace_attribute(lines, attribute, value):

    for i, line in enumerate(lines):

        stripped = line.strip()

        if stripped.startswith(attribute + " ="):

            indent = line[: len(line) - len(line.lstrip())]

            lines[i] = f"{indent}{attribute} = {terraform_value(value)}\n"

            return True

    return False


def add_attribute(lines, attribute, value):

    resource_end = None

    brace = 0

    started = False

    for i, line in enumerate(lines):

        if "resource " in line:

            started = True

        if started:

            brace += line.count("{")
            brace -= line.count("}")

            if brace == 0:

                resource_end = i
                break

    if resource_end is None:
        return False

    indent = "  "

    lines.insert(
        resource_end,
        f"{indent}{attribute} = {terraform_value(value)}\n",
    )

    return True


def remove_attribute(lines, attribute):

    for i, line in enumerate(lines):

        if line.strip().startswith(attribute + " ="):

            del lines[i]

            return True

    return False


def update_file(change):

    tf_file = change["file"]

    if not os.path.exists(tf_file):

        print(f"Missing file {tf_file}")

        return {
            "file": tf_file,
            "status": "missing"
        }

    backup(tf_file)

    with open(tf_file, encoding="utf-8") as f:

        lines = f.readlines()

    modified = False

    for op in change["operations"]:

        operation = op["op"]

        attribute = op["attribute"]

        if operation == "replace":

            if replace_attribute(
                lines,
                attribute,
                op["value"],
            ):
                modified = True

        elif operation == "add":

            if add_attribute(
                lines,
                attribute,
                op["value"],
            ):
                modified = True

        elif operation == "remove":

            if remove_attribute(
                lines,
                attribute,
            ):
                modified = True

    if modified:

        with open(tf_file, "w", encoding="utf-8") as f:

            f.writelines(lines)

    return {
        "file": tf_file,
        "modified": modified,
    }


def terraform_fmt():

    try:

        subprocess.run(
            [
                "terraform",
                "fmt",
                "-recursive",
            ],
            check=True,
        )

        return True

    except Exception as ex:

        print(ex)

        return False


def main():

    if not os.path.exists(PATCH_FILE):

        print("terraform_patch.json not found")

        return

    with open(PATCH_FILE, encoding="utf-8") as f:

        patches = json.load(f)

    report = []

    print("=" * 80)
    print("Terraform Writer")
    print("=" * 80)

    for patch in patches:

        result = update_file(patch)

        report.append(result)

    terraform_fmt()

    os.makedirs("reports", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

        json.dump(report, f, indent=4)

    print()
    print("=" * 80)
    print("Terraform update completed.")
    print("=" * 80)


if __name__ == "__main__":

    main()
