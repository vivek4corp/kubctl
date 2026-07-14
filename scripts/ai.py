import json
import os
import sys
import requests

# ============================================================
# Configuration
# ============================================================

TOKEN = os.getenv("MODELS_PAT")

if not TOKEN:
    print("ERROR: MODELS_PAT environment variable not found.")
    sys.exit(1)

MODEL = "openai/gpt-4.1"

# ============================================================
# Read Drift Report
# ============================================================

try:
    with open("reports/drift.json", "r") as f:
        drift = json.load(f)
except FileNotFoundError:
    print("ERROR: reports/drift.json not found.")
    sys.exit(1)

# ============================================================
# Create Compact Summary
# (Avoid sending huge Terraform JSON)
# ============================================================

resources = []


# Support new drift report format

if isinstance(drift, dict):

    drift_resources = drift.get(
        "resources",
        []
    )

else:

    drift_resources = drift



for item in drift_resources:


    resource = {


        "resource":

            item.get(
                "resource"
            ),


        "type":

            item.get(
                "type"
            ),


        "actions":

            item.get(
                "actions",
                []
            ),


        "action":

            item.get(
                "action",
                ""
            ),


        "risk":

            item.get(
                "risk",
                "Unknown"
            ),


        "changed_by":

            item.get(
                "changed_by",
                "Unknown"
            ),


        "time":

            item.get(
                "time",
                "Unknown"
            )

    }



    after = item.get(
        "after"
    )


    if isinstance(
        after,
        dict
    ):


        resource["changed_properties"] = list(
            after.keys()
        )[:20]



    resources.append(
        resource
    )

# ============================================================
# Prompt
# ============================================================

prompt = f"""
You are an expert Azure DevOps, Terraform and Cloud Security Architect.

Analyze the Terraform drift.

For each resource provide:

- Resource Name
- Drift Type
- Risk
- Impact
- Recommendation
- Priority (High/Medium/Low)

Finally provide:

1. Executive Summary
2. Overall Risk
3. Suggested Terraform Actions
4. Best Practices

Terraform Drift:

{json.dumps(resources, indent=2)}
"""

# ============================================================
# GitHub Models Request
# ============================================================

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
    "Content-Type": "application/json"
}

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "system",
            "content": "You are a Terraform Drift Detection Expert."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": 0.2,
    "max_tokens": 1200
}

print("Calling GitHub Models...")

response = requests.post(
    "https://models.github.ai/inference/chat/completions",
    headers=headers,
    json=payload,
    timeout=120
)

print("Status Code:", response.status_code)

if not response.ok:
    print("Response:")
    print(response.text)
    response.raise_for_status()

result = response.json()

answer = result["choices"][0]["message"]["content"]

# ============================================================
# Save Report
# ============================================================

os.makedirs("reports", exist_ok=True)

with open("reports/summary.md", "w", encoding="utf-8") as f:
    f.write(answer)

print("AI summary written to reports/summary.md")

print("\n================ AI SUMMARY ================\n")
print(answer)
print("\n===========================================\n")
