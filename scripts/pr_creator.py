import json
import os
import sys
import requests

# -------------------------------------------------------
# Environment
# -------------------------------------------------------

TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    print("ERROR: GITHUB_TOKEN not found.")
    sys.exit(1)

REPOSITORY = os.getenv("GITHUB_REPOSITORY")

if not REPOSITORY:
    print("ERROR: GITHUB_REPOSITORY not found.")
    sys.exit(1)

OWNER, REPO = REPOSITORY.split("/")

# -------------------------------------------------------
# Read Git Information
# -------------------------------------------------------

with open("reports/git_info.json", "r", encoding="utf-8") as f:
    git = json.load(f)

feature_branch = git["feature_branch"]
base_branch = git["current_branch"]

# -------------------------------------------------------
# Read AI Summary
# -------------------------------------------------------

summary = ""

if os.path.exists("reports/summary.md"):
    with open("reports/summary.md", "r", encoding="utf-8") as f:
        summary = f.read()

# -------------------------------------------------------
# Pull Request Body
# -------------------------------------------------------

title = "AI Terraform Drift Auto Remediation"

body = f"""
## Terraform Drift Auto Remediation

This pull request was automatically created by the Terraform Drift Detection Agent.

### AI Analysis

{summary}

---

### Validation

- Terraform configuration updated
- Terraform validation completed
- Ready for manual review

> After approval, merge this PR and run the Terraform Apply workflow.
"""

# -------------------------------------------------------
# GitHub API
# -------------------------------------------------------

url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

payload = {
    "title": title,
    "head": feature_branch,
    "base": base_branch,
    "body": body
}

response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=60
)

print("Status Code:", response.status_code)

if not response.ok:
    print(response.text)
    response.raise_for_status()

pr = response.json()

print("=" * 70)
print("Pull Request Created Successfully")
print("=" * 70)
print("PR Number :", pr["number"])
print("PR URL    :", pr["html_url"])

os.makedirs("reports", exist_ok=True)

with open("reports/pr.json", "w", encoding="utf-8") as f:
    json.dump(pr, f, indent=4)

print("Saved: reports/pr.json")
