## Terraform Generator for AWS (DeepSeek)

Generate production-ready Terraform (HCL) for AWS services using a simple web UI backed by the DeepSeek API.

### Prerequisites
- Node.js 18+
- A DeepSeek API key

### Setup
1. Install dependencies:
```bash
npm install
```
2. Configure environment:
```bash
cp .env.example .env
# Edit .env and set DEEPSEEK_API_KEY
```

### Run
```bash
npm start
```
Open `http://localhost:3000` in your browser.

### Notes
- The Additional configuration field accepts either JSON or `key=value` pairs (one per line). Basic types are inferred.
- The backend prompts the model to output only Terraform HCL suitable for a single `main.tf` file.
- A copy and a download button are provided to use the generated code directly.

### Security
- The API key is read from server-side environment variables and never exposed to the client.

### Disclaimer
- Always review generated infrastructure-as-code before applying it in production.