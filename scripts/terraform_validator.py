import json
import os
import subprocess
import sys

TF_DIR = os.getenv("TF_WORKING_DIR", "environments/dev")

REPORT = "reports/validation.json"


def execute(command):

    print("=" * 80)
    print(command)
    print("=" * 80)

    result = subprocess.run(
        command,
        cwd=TF_DIR,
        shell=True,
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.stderr:
        print(result.stderr)

    return result


def main():

    os.makedirs("reports", exist_ok=True)

    report = []

    ####################################################################
    # Terraform fmt
    ####################################################################

    result = execute("terraform fmt -recursive")

    report.append({
        "step": "terraform fmt",
        "exit_code": result.returncode,
        "status": "PASS" if result.returncode == 0 else "FAIL"
    })

    if result.returncode != 0:

        with open(REPORT, "w") as f:
            json.dump(report, f, indent=4)

        sys.exit(1)

    ####################################################################
    # Terraform Validate
    ####################################################################

    result = execute("terraform validate")

    report.append({
        "step": "terraform validate",
        "exit_code": result.returncode,
        "status": "PASS" if result.returncode == 0 else "FAIL"
    })

    if result.returncode != 0:

        with open(REPORT, "w") as f:
            json.dump(report, f, indent=4)

        sys.exit(1)

    ####################################################################
    # Terraform Plan
    ####################################################################

    result = execute(
        "terraform plan -input=false -detailed-exitcode"
    )

    if result.returncode == 0:

        status = "PASS"

    elif result.returncode == 2:

        status = "DRIFT DETECTED"

    else:

        status = "FAIL"

    report.append({
        "step": "terraform plan",
        "exit_code": result.returncode,
        "status": status
    })

    with open(REPORT, "w") as f:
        json.dump(report, f, indent=4)

    print()
    print("=" * 80)
    print("Terraform Validation Summary")
    print("=" * 80)

    for item in report:

        print(
            f'{item["step"]:<25} {item["status"]}'
        )

    if result.returncode == 1:
        sys.exit(1)


if __name__ == "__main__":
    main()
