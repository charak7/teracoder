# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Install system deps (optional: terraform not installed here)
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY webapp/ ./webapp/

ENV PORT=8000
EXPOSE 8000

WORKDIR /app/webapp
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]