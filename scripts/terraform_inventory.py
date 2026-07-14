import os
import json
import hcl2


MODULE_ROOT = "modules"
OUTPUT_FILE = "reports/terraform_inventory.json"


inventory = []


print("=" * 80)
print("Terraform Inventory Scanner")
print("=" * 80)



def parse_tf_file(tf_file):

    try:

        with open(
            tf_file,
            "r",
            encoding="utf-8"
        ) as f:

            return hcl2.load(f)


    except Exception as ex:

        print(f"Unable to parse : {tf_file}")
        print(ex)

        return {}




if not os.path.exists(MODULE_ROOT):

    print(
        f"Modules directory not found: {MODULE_ROOT}"
    )

    exit(1)



for root_module, dirs, files in os.walk(MODULE_ROOT):


    module_path = root_module.replace(
        MODULE_ROOT,
        ""
    ).strip("/")


    if not module_path:

        module_name = "root"

    else:

        module_name = module_path.split("/")[0]



    print(
        f"\nScanning Module : {module_name}"
    )


    for file in files:


        if not file.endswith(".tf"):

            continue



        tf_file = os.path.join(
            root_module,
            file
        )


        data = parse_tf_file(tf_file)



        resources = data.get(
            "resource",
            []
        )



        for resource in resources:


            for resource_type, values in resource.items():


                for resource_name, attributes in values.items():


                    resource_id = (
                        f"{resource_type}.{resource_name}"
                    )


                    exists = any(
                        item["resource"] == resource_id
                        and item["file"] == tf_file
                        for item in inventory
                    )


                    if exists:

                        continue



                    inventory.append(

                        {

                            "module": module_name,

                            "module_path": root_module,

                            "file": tf_file,

                            "resource": resource_id,

                            "resource_type": resource_type,

                            "resource_name": resource_name,

                            "attributes": list(
                                attributes.keys()
                            )

                        }

                    )



                    print(
                        f"  {resource_id}"
                    )



os.makedirs(
    "reports",
    exist_ok=True
)



with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:


    json.dump(
        inventory,
        f,
        indent=4
    )



print()

print("=" * 80)

print(
    f"Resources Found : {len(inventory)}"
)

print(
    f"Inventory Saved : {OUTPUT_FILE}"
)

print("=" * 80)
