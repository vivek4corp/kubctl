import json
import os
import subprocess
import sys

TF_DIR = os.getenv("TF_WORKING_DIR", "environments/dev")

IMPORT_FILE = "reports/import_required.json"


def run(cmd):

    print("=" * 80)
    print(cmd)
    print("=" * 80)

    result = subprocess.run(
        cmd,
        cwd=TF_DIR,
        shell=True,
        text=True,
        capture_output=True
    )

    print(result.stdout)

    if result.stderr:
        print(result.stderr)

    return result.returncode


def get_resource_id(resource):

    resource_type = resource["type"]
    name = resource["name"]

    #
    # Add new resource types here
    #

    commands = {

        "azurerm_resource_group":
        f'az group show --name "{name}" --query id -o tsv',

        "azurerm_container_registry":
        f'az acr show --name "{name}" --query id -o tsv',

        "azurerm_kubernetes_cluster":
        f'az aks show '
        f'--resource-group rg-micro-dev '
        f'--name "{name}" '
        f'--query id -o tsv'

    }

    if resource_type not in commands:

        print(f"Unsupported resource type : {resource_type}")

        return None

    result = subprocess.run(
        commands[resource_type],
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print(result.stderr)

        return None

    return result.stdout.strip()


def main():

    if not os.path.exists(IMPORT_FILE):

        print("Nothing to import.")

        return

    with open(IMPORT_FILE) as f:

        imports = json.load(f)

    if len(imports) == 0:

        print("No imports required.")

        return

    print("=" * 80)
    print("Terraform Import")
    print("=" * 80)

    for resource in imports:

        resource_id = get_resource_id(resource)

        if resource_id is None:

            continue

        command = (
            f'terraform import '
            f'"{resource["resource"]}" '
            f'"{resource_id}"'
        )

        code = run(command)

        if code == 0:

            print(f"Imported : {resource['resource']}")

        else:

            print(f"Failed : {resource['resource']}")

    print("\nTerraform Import Completed")


if __name__ == "__main__":
    main()
