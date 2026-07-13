import json

with open("terraform/tfplan.json") as f:
    plan = json.load(f)

changes = plan.get("resource_changes", [])

print("="*60)

for resource in changes:

    actions = resource["change"]["actions"]

    if actions != ["no-op"]:

        print(resource["address"])
        print(actions)
        print("-"*40)
