import json
import os
import sys
import requests

TOKEN = os.getenv("MODELS_PAT")

if not TOKEN:
    print("ERROR: MODELS_PAT environment variable not found.")
    sys.exit(1)

MODEL = "openai/gpt-4.1"

with open("reports/drift.json", "r") as f:
    drift = json.load(f)

prompt = f"""
You are a Terraform Drift Analysis Agent.

Analyze the following Terraform drift and provide:

1. Summary
2. Risk
3. Impact
4. Recommendation
5. Priority (High/Medium/Low)

Terraform Drift:

{json.dumps(drift, indent=2)}
"""

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
            "role": "user",
            "content": prompt
        }
    ]
}

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

print(json.dumps(result, indent=2))

answer = result["choices"][0]["message"]["content"]

os.makedirs("reports", exist_ok=True)

with open("reports/summary.md", "w") as f:
    f.write(answer)

print("AI summary written to reports/summary.md")
