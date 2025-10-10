# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update && \
    apt-get install --no-install-recommends -y build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY agents ./agents
COPY utils ./utils
COPY models ./models
COPY supabase.sql ./supabase.sql

EXPOSE 8000

ENV ALLOWED_ORIGINS=http://localhost:5173

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
