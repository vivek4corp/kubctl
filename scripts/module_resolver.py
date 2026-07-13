import json
import os
import re
import sys

# Terraform modules metadata
MODULES_JSON = os.path.join(
    "environments",
    "dev",
    ".terraform",
    "modules",
    "modules.json"
)

# Drift report
DRIFT_JSON = os.path.join(
    "reports",
    "drift.json"
)

OUTPUT_JSON = os.path.join(
    "reports",
    "module_mapping.json"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_module_name(resource):
    """
    Example:

    module.aks.azurerm_kubernetes_cluster.aks["aks-dev"]

    returns

    aks
    """

    match = re.match(r"module\.([^.]+)", resource)

    if match:
        return match.group(1)

    return None


def main():

    if not os.path.exists(MODULES_JSON):
        print(f"ERROR: {MODULES_JSON} not found")
        print("Run terraform init first.")
        sys.exit(1)

    if not os.path.exists(DRIFT_JSON):
        print(f"ERROR: {DRIFT_JSON} not found")
        sys.exit(1)

    modules_data = load_json(MODULES_JSON)
    drift_data = load_json(DRIFT_JSON)

    modules = modules_data.get("Modules", [])

    output = []

    for drift in drift_data:

        resource = drift["resource"]

        module_name = get_module_name(resource)

        if module_name is None:
            continue

        found = None

        for module in modules:

            if module.get("Key") == module_name:

                found = {
                    "resource": resource,
                    "module_key": module.get("Key"),
                    "source": module.get("Source"),
                    "directory": module.get("Dir"),
                    "version": module.get("Version")
                }

                break

        if found:
            output.append(found)

    os.makedirs("reports", exist_ok=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)

    print("=" * 70)
    print("Resolved Modules")
    print("=" * 70)

    if not output:
        print("No modules resolved.")
    else:
        for item in output:
            print(f"Resource  : {item['resource']}")
            print(f"Module    : {item['module_key']}")
            print(f"Source    : {item['source']}")
            print(f"Directory : {item['directory']}")
            print(f"Version   : {item['version']}")
            print("-" * 70)

    print(f"\nOutput written to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
