import subprocess
import sys
import os

TF_DIR = "environments/dev"


def run(cmd):

    print(f"\nRunning: {cmd}")

    result = subprocess.run(
        cmd,
        cwd=TF_DIR,
        shell=True,
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.stderr:
        print(result.stderr)

    return result.returncode


print("=" * 60)
print("Terraform Validation")
print("=" * 60)

# ------------------------------------
# terraform fmt
# ------------------------------------

if run("terraform fmt -recursive") != 0:
    print("terraform fmt failed")
    sys.exit(1)

# ------------------------------------
# terraform validate
# ------------------------------------

if run("terraform validate") != 0:
    print("terraform validate failed")
    sys.exit(1)

# ------------------------------------
# terraform plan
# ------------------------------------

code = run("terraform plan -input=false")

if code != 0:
    print("terraform plan failed")
    sys.exit(1)

print("\nTerraform validation completed successfully.")
