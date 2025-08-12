require('dotenv').config();
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY;

app.use(cors());
app.use(express.json({ limit: '1mb' }));
app.use(express.static(path.join(__dirname, 'public')));

function parseAdditionalConfig(input) {
  if (!input || typeof input !== 'string') return {};

  // Try JSON first
  try {
    const asJson = JSON.parse(input);
    if (asJson && typeof asJson === 'object') return asJson;
  } catch (_) {}

  // Fallback: parse key=value lines
  const config = {};
  input
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean)
    .forEach((line) => {
      const eqIdx = line.indexOf('=');
      if (eqIdx === -1) return;
      const key = line.slice(0, eqIdx).trim();
      const valueRaw = line.slice(eqIdx + 1).trim();
      let value = valueRaw;
      if (valueRaw === 'true') value = true;
      else if (valueRaw === 'false') value = false;
      else if (!isNaN(Number(valueRaw))) value = Number(valueRaw);
      config[key] = value;
    });
  return config;
}

function buildPrompt({ service, region, resourceName, additionalConfig }) {
  const configPairs = Object.entries(additionalConfig || {})
    .map(([k, v]) => `- ${k}: ${JSON.stringify(v)}`)
    .join('\n');

  const instructions = `
You are an expert Terraform engineer. Generate production-grade Terraform (HCL) for AWS.
Constraints:
- Output ONLY Terraform code. Do not include markdown fences or commentary.
- Use Terraform 1.5+ syntax and aws provider >= 5.0.
- Prefer variables and sensible defaults. Use small, safe defaults when unspecified.
- Set tags where supported: { Name = var.resource_name }.
- Use the provided AWS region via provider configuration.
- Ensure a single file main.tf is valid by itself.
- If the service requires IAM roles/policies, include minimal least-privilege inline.
- If dependencies (e.g., security groups, subnets) are needed and not provided, create minimal sane defaults.
- Use resource names derived from var.resource_name.

Service: ${service}
AWS Region: ${region}
Resource name (base): ${resourceName}
Additional configuration (user preferences):\n${configPairs || '- (none)'}

Deliver a complete, self-contained main.tf with provider, variables (with defaults), and resources.
  `.trim();

  return instructions;
}

async function generateHandler(req, res) {
  try {
    if (!DEEPSEEK_API_KEY) {
      return res.status(500).json({ error: 'Server not configured: missing DEEPSEEK_API_KEY' });
    }

    const { service, region, resourceName, additionalConfigText } = req.body || {};

    if (!service || !region || !resourceName) {
      return res.status(400).json({ error: 'Missing required fields: service, region, resourceName' });
    }

    const additionalConfig = parseAdditionalConfig(additionalConfigText || '');

    const prompt = buildPrompt({ service, region, resourceName, additionalConfig });

    const response = await axios.post(
      'https://api.deepseek.com/chat/completions',
      {
        model: 'deepseek-chat',
        temperature: 0.2,
        messages: [
          {
            role: 'system',
            content:
              'You are a senior cloud infrastructure engineer specializing in Terraform for AWS. Always output only Terraform HCL without code fences.'
          },
          { role: 'user', content: prompt }
        ]
      },
      {
        headers: {
          'Authorization': `Bearer ${DEEPSEEK_API_KEY}`,
          'Content-Type': 'application/json'
        },
        timeout: 60_000
      }
    );

    const content = response?.data?.choices?.[0]?.message?.content || '';

    // Strip markdown code fences if present
    const stripped = content.replace(/^```[a-z]*\n?|```$/gim, '');

    res.json({ code: stripped.trim() });
  } catch (error) {
    console.error('Generation error:', error?.response?.data || error.message);
    const status = error?.response?.status || 500;
    const data = error?.response?.data;
    res.status(status).json({ error: 'Failed to generate Terraform code', details: data || error.message });
  }
}

app.post('/api/generate', generateHandler);
app.put('/api/generate', generateHandler);

app.get('/health', (_req, res) => {
  res.json({ ok: true });
});

app.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});