import json
import os
from copy import deepcopy

DRIFT_FILE = "reports/drift.json"
RESOURCE_FILE = "reports/terraform_resources.json"
OUTPUT_FILE = "reports/terraform_patch.json"

# Ignore provider-managed/computed attributes
IGNORE_ATTRIBUTES = {
    "id",
    "etag",
    "identity",
    "identity_ids",
    "principal_id",
    "tenant_id",
    "resource_guid",
    "timeouts",

    "primary_access_key",
    "secondary_access_key",

    "primary_connection_string",
    "secondary_connection_string",

    "primary_blob_connection_string",
    "secondary_blob_connection_string",

    "primary_blob_endpoint",
    "secondary_blob_endpoint",

    "primary_blob_host",
    "secondary_blob_host",

    "primary_file_endpoint",
    "secondary_file_endpoint",

    "primary_file_host",
    "secondary_file_host",

    "primary_queue_endpoint",
    "secondary_queue_endpoint",

    "primary_queue_host",
    "secondary_queue_host",

    "primary_table_endpoint",
    "secondary_table_endpoint",

    "primary_table_host",
    "secondary_table_host",

    "primary_web_endpoint",
    "secondary_web_endpoint",

    "primary_web_host",
    "secondary_web_host",

    "private_ip_address",
    "public_ip_address",

    "fqdn",
    "storage_uri",

    "creation_time",
    "last_modified",

    "blob_properties",
    "queue_properties",
    "share_properties",
}


def load_json(path):

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def should_ignore(attribute):

    if attribute in IGNORE_ATTRIBUTES:
        return True

    attribute = attribute.lower()

    ignore_keywords = [
        "endpoint",
        "connection_string",
        "access_key",
        "host",
        "password",
        "secret",
        "private_ip",
        "public_ip",
        "principal",
        "identity",
        "key_vault",
        "certificate",
    ]

    return any(word in attribute for word in ignore_keywords)


def compare_values(before, after, prefix=""):

    """
    Recursively compare two Terraform objects.
    Returns a list of changed attributes.
    """

    changes = []

    before = before or {}
    after = after or {}

    keys = set(before.keys()) | set(after.keys())

    for key in sorted(keys):

        if should_ignore(key):
            continue

        old = before.get(key)
        new = after.get(key)

        path = f"{prefix}.{key}" if prefix else key

        # Nested object
        if isinstance(old, dict) and isinstance(new, dict):

            changes.extend(
                compare_values(old, new, path)
            )
            continue

        # Skip complex lists in V1
        if isinstance(old, list) or isinstance(new, list):
            continue

        if old != new:

            changes.append(
                {
                    "attribute": path,
                    "operation": "replace",
                    "old": deepcopy(old),
                    "new": deepcopy(new)
                }
            )

    return changes


def find_tf_file(terraform_resources, resource_address):
    """
    Locate Terraform file from parser output.
    """

    for item in terraform_resources:

        address = item.get("resource_address") or item.get("resource")

        if address == resource_address:
            return item.get("file")

    return None
    ###############################################################################
# Build Terraform Patch
###############################################################################

def build_patch():

    print("=" * 80)
    print("Generating Terraform Patch")
    print("=" * 80)

    drift = load_json(DRIFT_FILE)
    resources = load_json(RESOURCE_FILE)

    patches = []

    for item in drift:

        before = item.get("before", {}) or {}
        after = item.get("after", {}) or {}

        resource_address = item.get("resource")
        actions = item.get("actions", [])

        tf_file = find_tf_file(resources, resource_address)

        if tf_file is None:

            print(f"WARNING : Terraform file not found for {resource_address}")
            continue

        operations = compare_values(before, after)

        #######################################################################
        # Skip resources without actual attribute changes
        #######################################################################

        if len(operations) == 0:
            continue

        #######################################################################
        # Build patch object
        #######################################################################

        patch = {
            "resource": resource_address,
            "type": item.get("type"),
            "name": item.get("name"),
            "file": tf_file,
            "actions": actions,
            "operations": operations,
            "changed_by": item.get("changed_by"),
            "time": item.get("time"),
            "risk": item.get("risk", ""),
            "recommendation": item.get("recommendation", "")
        }

        patches.append(patch)

        print()
        print(f"Resource : {resource_address}")
        print(f"Terraform File : {tf_file}")
        print(f"Detected Changes : {len(operations)}")

        for change in operations:

            print(
                f"  {change['attribute']} : "
                f"{change['old']} -> {change['new']}"
            )

    ###########################################################################
    # Save Patch
    ###########################################################################

    save_json(OUTPUT_FILE, patches)

    print()
    print("=" * 80)
    print(f"Generated {OUTPUT_FILE}")
    print(f"Resources : {len(patches)}")
    print("=" * 80)

    return patches
    ###############################################################################
# Main
###############################################################################

def main():

    patches = build_patch()

    if len(patches) == 0:

        print()
        print("=" * 80)
        print("No Terraform modifications required.")
        print("=" * 80)
        return

    total_resources = len(patches)
    total_operations = sum(
        len(resource["operations"])
        for resource in patches
    )

    print()
    print("=" * 80)
    print("Terraform Patch Summary")
    print("=" * 80)

    print(f"Resources Modified : {total_resources}")
    print(f"Operations Generated : {total_operations}")

    print()

    for resource in patches:

        print(resource["resource"])

        for operation in resource["operations"]:

            print(
                f"  - {operation['attribute']}"
                f" : {operation['old']} -> {operation['new']}"
            )

    print()
    print("=" * 80)
    print("Terraform Modifier completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
