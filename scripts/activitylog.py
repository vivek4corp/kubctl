import subprocess

resource_id="/subscriptions/.../resourceGroups/demo/providers/..."

cmd=f"az monitor activity-log list --resource-id {resource_id}"

print(subprocess.check_output(cmd,shell=True).decode())
