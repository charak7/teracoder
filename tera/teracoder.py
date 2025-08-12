#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import requests

# --- Configuration ---
API_KEY = os.getenv("DEEPSEEK_API_KEY")  # Set your DeepSeek API key
MODEL = "deepseek-chat"                  # Adjust if you have a specific model
BASE_URL = "https://api.deepseek.com/v1/chat/completions"
# ----------------------

if not API_KEY:
    print("❌ Please set DEEPSEEK_API_KEY in your environment.")
    sys.exit(1)

# Prompt from CLI args or default
prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
    "Create a Terraform configuration for an AWS EC2 instance (Ubuntu 22.04), t3.micro, in us-east-1. Include provider block, security group allowing HTTP, and a simple user_data to install nginx."

# Instruction wrapper for HCL-only output
full_prompt = f"""
You are a Terraform code generator.
Generate valid Terraform HCL only (no explanation, no backticks).
Requirements:
- Provider: aws (region us-east-1 unless specified)
- Terraform >= 1.3 syntax
- Include provider block, security group, and an aws_instance with user_data installing nginx
- Use variables for region and instance_type
Request:
{prompt}
"""

# API request
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": full_prompt}],
    "max_tokens": 1200,
    "temperature": 0.0
}

print("⚙️  Requesting Terraform code from DeepSeek...")
resp = requests.post(BASE_URL, headers=headers, data=json.dumps(payload))
resp.raise_for_status()
result = resp.json()

# Extract code
tf_code = result["choices"][0]["message"]["content"].strip()

# Write to file
with open("main.tf", "w") as f:
    f.write(tf_code + "\n")

print("✅ Wrote main.tf")

# Run terraform init & validate
subprocess.run(["terraform", "init"], check=False)
val = subprocess.run(["terraform", "validate"], capture_output=True, text=True)

print("\n---- terraform validate output ----")
print(val.stdout)
print(val.stderr)
if val.returncode == 0:
    print("Terraform validate: SUCCESS ✅")
else:
    print("Terraform validate: FAILED ❌ (see output above)")
