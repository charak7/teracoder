# TerraCoder Web

A minimal Flask web application to generate Terraform code using the DeepSeek API.

## Quick start (local)

1. Python 3.10+
2. Install deps:

```bash
pip install -r requirements.txt
```

3. Set your API key (any of these):

- Env var: `export DEEPSEEK_API_KEY=your_key`
- File: `webapp/config.json` with `{"api_key": "your_key"}`
- File: `tera/config.json` or `~/.teracoder.json` with `{"DEEPSEEK_API_KEY": "your_key"}`
- Hardcode: set `HARDCODED_DEEPSEEK_API_KEY` env var

4. Run the app:

```bash
python webapp/app.py
```

Open `http://localhost:8000`.

## Docker

```bash
docker build -t terracoder-web .
docker run -p 8000:8000 -e DEEPSEEK_API_KEY=your_key terracoder-web
```

## Deploy

Deploy anywhere that can run a container (Fly.io, AWS App Runner, Cloud Run, Azure App Service, Heroku via container, etc.).

## Notes

- Optional: Check "Run terraform validate" to validate generated code if the server has `terraform` installed.
- Defaults: model `deepseek-chat`, temperature `0.0`, max tokens `1200`.