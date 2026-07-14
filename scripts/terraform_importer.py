import json
import os
import subprocess
import sys

DRIFT_FILE = "reports/drift.json"

if not os.path.exists(DRIFT_FILE):
    print("No drift report found.")
    sys.exit(0)

with open(DRIFT_FILE, "r", encoding="utf-8") as f:
    drift = json.load(f)

if not drift:
    print("No drift detected.")
    sys.exit(0)

print("=" * 70)
print("Terraform Import")
print("=" * 70)

imports = []

for resource in drift:

    actions = resource.get("actions", [])

    # Import only if Terraform thinks it needs to create
    if actions != ["create"]:
        continue

    address = resource.get("resource")
    resource_id = resource.get("azure_resource_id")

    if not address or not resource_id:
        print(f"Skipping {address} (Azure Resource ID missing)")
        continue

    cmd = [
        "terraform",
        "import",
        address,
        resource_id
    ]

    print("Running:", " ".join(cmd))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    imports.append({
        "resource": address,
        "id": resource_id,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    })

    if result.returncode == 0:
        print("Imported successfully")
    else:
        print("Import failed")
        print(result.stderr)

os.makedirs("reports", exist_ok=True)

with open("reports/import_result.json", "w", encoding="utf-8") as f:
    json.dump(imports, f, indent=4)

print("=" * 70)
print("Import completed.")
