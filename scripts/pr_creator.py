import json
import os
import sys
import requests

TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    print("GITHUB_TOKEN not found.")
    sys.exit(1)

REPOSITORY = os.getenv("GITHUB_REPOSITORY")

if not REPOSITORY:
    print("GITHUB_REPOSITORY not found.")
    sys.exit(1)

OWNER, REPO = REPOSITORY.split("/")

with open("reports/git_info.json") as f:
    git = json.load(f)

branch = git["branch"]

summary = ""

if os.path.exists("reports/summary.md"):
    with open("reports/summary.md") as f:
        summary = f.read()

title = "AI Terraform Drift Auto Remediation"

body = f"""
# Terraform Drift Auto Remediation

This Pull Request was automatically created.

## AI Summary

{summary}

---

Please review before merging.

Validation Completed

- terraform fmt
- terraform validate
- terraform plan

Manual approval required.
"""

url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

payload = {
    "title": title,
    "head": branch,
    "base": "main",
    "body": body,
    "maintainer_can_modify": True
}

response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=60
)

print(response.status_code)
print(response.text)

response.raise_for_status()

print("Pull Request Created Successfully")
