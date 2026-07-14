import json
import os
import subprocess
import sys

OUTPUT_FILE = "reports/validation.json"


def run_command(command):

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def terraform_fmt():

    print("=" * 80)
    print("Running terraform fmt")
    print("=" * 80)

    return run_command(
        [
            "terraform",
            "fmt",
            "-recursive"
        ]
    )


def terraform_validate():

    print("=" * 80)
    print("Running terraform validate")
    print("=" * 80)

    return run_command(
        [
            "terraform",
            "validate",
            "-json"
        ]
    )


def main():

    os.makedirs("reports", exist_ok=True)

    fmt_result = terraform_fmt()

    validate_result = terraform_validate()

    report = {
        "terraform_fmt": fmt_result,
        "terraform_validate": validate_result,
        "success": validate_result["returncode"] == 0
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print()
    print("=" * 80)

    if report["success"]:

        print("Terraform validation successful.")

    else:

        print("Terraform validation failed.")

    print("=" * 80)

    if not report["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
