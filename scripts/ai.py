import json
import os
import requests

TOKEN = os.environ["MODELS_PAT"]

MODEL = "openai/gpt-4.1"

with open("reports/drift.json") as f:
    drift = json.load(f)

prompt = f"""
You are a Terraform Drift Analysis Agent.

Analyze the following infrastructure drift.

Explain:

1. Risk
2. Impact
3. Recommendation
4. Priority

Drift:

{json.dumps(drift, indent=2)}
"""

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

body = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": 0.2
}

response = requests.post(
    "https://models.inference.ai.azure.com/chat/completions",
    headers=headers,
    json=body,
    timeout=60
)

response.raise_for_status()

answer = response.json()["choices"][0]["message"]["content"]

print(answer)

with open("reports/summary.md", "w") as f:
    f.write(answer)
