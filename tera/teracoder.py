#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import requests
import argparse
from pathlib import Path

# --- Configuration ---
MODEL = "deepseek-chat"                  # Adjust if you have a specific model
BASE_URL = "https://api.deepseek.com/v1/chat/completions"
HARDCODED_API_KEY = ""  # Optional: put your API key here to hardcode it (not recommended for production)
# ----------------------


def resolve_api_key(cli_key: str | None) -> str:
    """Resolve API key from CLI, env, config files, or hardcoded fallback (in that order)."""
    if cli_key:
        return cli_key

    env_key = os.getenv("DEEPSEEK_API_KEY")
    if env_key:
        return env_key

    # Look for config files with an API key
    for candidate in (
        Path("tera/config.json"),
        Path.home() / ".teracoder.json",
    ):
        try:
            if candidate.is_file():
                with open(candidate, "r") as f:
                    data = json.load(f)
                for k in ("DEEPSEEK_API_KEY", "deepseek_api_key", "api_key"):
                    if k in data and data[k]:
                        return data[k]
        except Exception:
            # Ignore config read errors and continue
            pass

    if HARDCODED_API_KEY:
        return HARDCODED_API_KEY

    return ""


# CLI
parser = argparse.ArgumentParser(description="Generate Terraform code via DeepSeek")
parser.add_argument("prompt", nargs="*", help="Request for Terraform code")
parser.add_argument("--api-key", "-k", dest="api_key", help="DeepSeek API key to use")
args = parser.parse_args()

# Prompt from CLI args or default
prompt = " ".join(args.prompt) if args.prompt else \
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

# API key resolution and request
API_KEY = resolve_api_key(args.api_key)
if not API_KEY:
    print("❌ No API key provided. Use --api-key, set DEEPSEEK_API_KEY, or add it to tera/config.json or ~/.teracoder.json.")
    sys.exit(1)

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
