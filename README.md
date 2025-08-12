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

### REST API
- **POST/PUT** `/api/generate`
  - **Body (JSON)**:
    - `service` (string) – e.g., `ec2`, `s3`, `rds`, `lambda`, `vpc`
    - `region` (string) – e.g., `us-east-1`
    - `resourceName` (string) – base name used for tags and resource names
    - `additionalConfigText` (string, optional) – JSON or `key=value` per line
  - **Response**: `{ code: "...terraform hcl..." }`

Example with PUT:
```bash
curl -X PUT http://localhost:3000/api/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "service": "ec2",
    "region": "us-east-1",
    "resourceName": "demo-ec2",
    "additionalConfigText": "instance_type=t3.micro\npublic_ip=true"
  }'
```

### Notes
- The Additional configuration field accepts either JSON or `key=value` pairs (one per line). Basic types are inferred.
- The backend prompts the model to output only Terraform HCL suitable for a single `main.tf` file.
- A copy and a download button are provided to use the generated code directly.

### Security
- The API key is read from server-side environment variables and never exposed to the client.

### Disclaimer
- Always review generated infrastructure-as-code before applying it in production.