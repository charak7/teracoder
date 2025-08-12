from __future__ import annotations
import os
import json
import subprocess
from pathlib import Path
from typing import Optional

from flask import Flask, render_template, request, jsonify, make_response
import requests

app = Flask(__name__)

DEFAULT_MODEL = "deepseek-chat"
BASE_URL = "https://api.deepseek.com/v1/chat/completions"
HARDCODED_API_KEY = os.getenv("HARDCODED_DEEPSEEK_API_KEY", "")


def resolve_api_key(cli_key: Optional[str]) -> str:
    if cli_key:
        return cli_key.strip()

    env_key = os.getenv("DEEPSEEK_API_KEY")
    if env_key:
        return env_key

    for candidate in (
        Path("tera/config.json"),
        Path.home() / ".teracoder.json",
        Path("webapp/config.json"),
    ):
        try:
            if candidate.is_file():
                with open(candidate, "r") as f:
                    data = json.load(f)
                for k in ("DEEPSEEK_API_KEY", "deepseek_api_key", "api_key"):
                    if k in data and data[k]:
                        return str(data[k])
        except Exception:
            pass

    if HARDCODED_API_KEY:
        return HARDCODED_API_KEY

    return ""


@app.get("/")
def index():
    return render_template("index.html", default_model=DEFAULT_MODEL)


@app.post("/generate")
def generate():
    user_prompt = request.form.get("prompt", "").strip()
    api_key_input = request.form.get("api_key", "").strip()
    model = request.form.get("model", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    temperature_str = request.form.get("temperature", "0.0").strip()
    max_tokens_str = request.form.get("max_tokens", "1200").strip()

    try:
        temperature = float(temperature_str)
    except ValueError:
        temperature = 0.0

    try:
        max_tokens = int(max_tokens_str)
    except ValueError:
        max_tokens = 1200

    if not user_prompt:
        return render_template(
            "index.html",
            default_model=DEFAULT_MODEL,
            error="Prompt is required.",
        ), 400

    api_key = resolve_api_key(api_key_input)
    if not api_key:
        return render_template(
            "index.html",
            default_model=DEFAULT_MODEL,
            error=(
                "No API key provided. Enter it in the form, set DEEPSEEK_API_KEY, "
                "or add it to tera/config.json, webapp/config.json, or ~/.teracoder.json."
            ),
            prompt_value=user_prompt,
            model_value=model,
            temperature_value=str(temperature),
            max_tokens_value=str(max_tokens),
        ), 401

    full_prompt = f"""
You are a Terraform code generator.
Generate valid Terraform HCL only (no explanation, no backticks).
Requirements:
- Provider: aws (region us-east-1 unless specified)
- Terraform >= 1.3 syntax
- Include provider block, security group, and an aws_instance with user_data installing nginx
- Use variables for region and instance_type
Request:
{user_prompt}
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": full_prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    try:
        resp = requests.post(BASE_URL, headers=headers, data=json.dumps(payload), timeout=60)
        resp.raise_for_status()
        result = resp.json()
        tf_code = result["choices"][0]["message"]["content"].strip()
    except requests.HTTPError as e:
        return render_template(
            "index.html",
            default_model=DEFAULT_MODEL,
            error=f"API error: {e.response.status_code} {e.response.text[:500]}",
            prompt_value=user_prompt,
            model_value=model,
            temperature_value=str(temperature),
            max_tokens_value=str(max_tokens),
        ), 502
    except Exception as e:
        return render_template(
            "index.html",
            default_model=DEFAULT_MODEL,
            error=f"Unexpected error: {str(e)}",
            prompt_value=user_prompt,
            model_value=model,
            temperature_value=str(temperature),
            max_tokens_value=str(max_tokens),
        ), 500

    # Optional: terraform validate if checkbox provided and terraform exists
    validate_requested = request.form.get("validate", "") == "on"
    validation_output = None
    if validate_requested:
        try:
            # Write to a temp directory and run terraform there
            tmp_dir = Path("/tmp/teracode")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tf_file = tmp_dir / "main.tf"
            tf_file.write_text(tf_code + "\n", encoding="utf-8")

            subprocess.run(["terraform", "init"], cwd=str(tmp_dir), check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            proc = subprocess.run(["terraform", "validate"], cwd=str(tmp_dir), capture_output=True, text=True)
            validation_output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        except FileNotFoundError:
            validation_output = "Terraform CLI not found in server environment. Skipping validation."
        except Exception as e:
            validation_output = f"Validation encountered an error: {str(e)}"

    return render_template(
        "index.html",
        default_model=DEFAULT_MODEL,
        generated=tf_code,
        prompt_value=user_prompt,
        model_value=model,
        temperature_value=str(temperature),
        max_tokens_value=str(max_tokens),
        validation_output=validation_output,
    )


@app.post("/download")
def download():
    tf_code = request.form.get("generated", "").encode("utf-8")
    if not tf_code:
        return jsonify({"error": "Nothing to download"}), 400

    response = make_response(tf_code)
    response.headers.set("Content-Type", "text/plain; charset=utf-8")
    response.headers.set("Content-Disposition", "attachment", filename="main.tf")
    return response


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)