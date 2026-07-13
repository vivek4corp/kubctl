import json
import os
import re
import sys

MODULES_FILE = ".terraform/modules/modules.json"
DRIFT_FILE = "reports/drift.json"
OUTPUT_FILE = "reports/module_mapping.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_module_name(resource_address):
    """
    Example:

    module.aks.azurerm_kubernetes_cluster.aks["aks-dev"]

    returns

    aks
    """

    match = re.search(r"module\.([^.]+)", resource_address)

    if match:
        return match.group(1)

    return None


def resolve_module(module_name, modules):

    for module in modules:

        key = module.get("Key")

        if key == module_name:

            return {
                "key": key,
                "source": module.get("Source"),
                "dir": module.get("Dir"),
                "version": module.get("Version")
            }

    return None


def detect_source(source):

    if source is None:
        return "unknown"

    source = source.lower()

    if source.startswith("git::"):
        return "git"

    if source.startswith("../") or source.startswith("./") or source.startswith("/"):
        return "local"

    if "github.com" in source:
        return "git"

    if "dev.azure.com" in source:
        return "azure-devops"

    if "/" in source:
        return "terraform-registry"

    return "unknown"


def main():

    if not os.path.exists(MODULES_FILE):
        print("ERROR : modules.json not found")
        print("Run terraform init first.")
        sys.exit(1)

    drift = load_json(DRIFT_FILE)

    module_data = load_json(MODULES_FILE)

    modules = module_data.get("Modules", [])

    results = []

    for item in drift:

        resource = item["resource"]

        module_name = extract_module_name(resource)

        module = resolve_module(module_name, modules)

        if module:

            module["resource"] = resource
            module["source_type"] = detect_source(module["source"])

            results.append(module)

    os.makedirs("reports", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print("\nResolved Modules\n")

    for module in results:

        print("=" * 60)
        print("Resource    :", module["resource"])
        print("Module Key  :", module["key"])
        print("Source Type :", module["source_type"])
        print("Source      :", module["source"])
        print("Directory   :", module["dir"])
        print("Version     :", module["version"])


if __name__ == "__main__":
    main()
