import subprocess
import sys
import os

TF_DIR = os.getenv("TF_WORKING_DIR", "environments/dev")


def run(cmd):

    print("=" * 70)
    print(f"Running: {cmd}")
    print("=" * 70)

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


def main():

    # terraform fmt
    if run("terraform fmt -recursive") != 0:
        print("terraform fmt failed")
        sys.exit(1)

    # terraform validate
    if run("terraform validate") != 0:
        print("terraform validate failed")
        sys.exit(1)

    # terraform plan
    code = run("terraform plan -input=false")

    if code != 0:
        print("terraform plan failed")
        sys.exit(1)

    print("\nTerraform validation completed successfully.")


if __name__ == "__main__":
    main()
