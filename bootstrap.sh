#!/bin/bash

set -e

echo "🧠 Initializing pithy AI Automation Platform..."

PROJECT="pithy"

mkdir -p $PROJECT
cd $PROJECT

# core structure
mkdir -p cli core llm memory infra tools plugins scheduler api data/db config tests scripts

# CLI
touch cli/main.py
touch cli/__init__.py

# Core
touch core/agent.py core/router.py core/orchestrator.py core/intent.py

# LLM
touch llm/client.py llm/models.py

# Memory (RAG)
touch memory/vector_store.py memory/retriever.py memory/embeddings.py memory/ingest.py

# Infra
touch infra/manager.py infra/docker_controller.py infra/monitor.py infra/scaling.py infra/state_engine.py

# Tools
touch tools/shell.py tools/filesystem.py tools/security.py tools/logger.py

# Plugins
mkdir -p plugins/example_plugin
touch plugins/loader.py plugins/registry.py
touch plugins/example_plugin/plugin.json plugins/example_plugin/main.py

# Scheduler
touch scheduler/predictor.py scheduler/analyzer.py scheduler/profiler.py

# API
touch api/server.py api/routes.py

# Config
touch config/settings.py config/models.yaml config/policies.json

# Docker
touch docker-compose.yml Dockerfile requirements.txt

# Scripts
touch scripts/setup.sh scripts/run_local.sh scripts/reset.sh

# root files
touch README.md .gitignore .env.example LICENSE

echo "📦 Writing base docker-compose..."

cat > docker-compose.yml << 'EOF'
version: "3.9"

services:

  pithy:
    build: .
    container_name: pithy_core
    restart: "no"
    volumes:
      - .:/app
      - ./data:/app/data
    working_dir: /app

  chroma:
    image: chromadb/chroma:latest
    container_name: pithy_chroma
    restart: "no"
    ports:
      - "8000:8000"
    volumes:
      - ./data/db:/chroma/chroma
EOF

echo "🐳 Writing Dockerfile..."

cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "cli/main.py"]
EOF

echo "📦 Writing requirements..."

cat > requirements.txt << 'EOF'
requests
psutil
chromadb
numpy
EOF

echo "📘 Writing README..."

cat > README.md << 'EOF'
# 🧠 pithy AI Automation Platform

Local AI automation system with:
- LLM (Ollama)
- RAG memory (ChromaDB)
- Infra manager (Docker)
- Plugin system
- CLI controller

## 🚀 Run

```bash
docker compose up --build