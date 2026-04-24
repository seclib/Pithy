"""
PIThy - Assistant local intelligent (version Docker)
Version: 0.2.0
Stack: Ollama + RAG + Docker + Python
"""

# =========================
# 📁 STRUCTURE DU PROJET
# =========================

"""
pithy/
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
│
├── main.py
├── config.py
│
├── core/
│   ├── agent.py
│   ├── brain.py
│   ├── router.py
│
├── llm/
│   ├── ollama_client.py
│
├── memory/
│   ├── vector_store.py
│   ├── embeddings.py
│
├── tools/
│   ├── shell.py
│   ├── filesystem.py
│
└── data/
    ├── db/
    ├── logs/
"""

# =========================
# 🐳 docker-compose.yml
# =========================

"""
version: '3.9'

services:

  pithy:
    build: .
    container_name: pithy_core
    restart: unless-stopped
    volumes:
      - .:/app
    working_dir: /app
    environment:
      - OLLAMA_URL=http://host.docker.internal:11434
    depends_on:
      - chroma

  chroma:
    image: chromadb/chroma:latest
    container_name: pithy_db
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data/db:/chroma/chroma
"""

# =========================
# 📦 Dockerfile
# =========================

"""
FROM python:3.11-slim

WORKDIR /app

# dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# dépendances python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
"""

# =========================
# 📦 requirements.txt
# =========================

"""
requests
chromadb
numpy
"""

# =========================
# ⚙️ .env
# =========================

"""
OLLAMA_URL=http://localhost:11434
DEFAULT_MODEL=dolphin-mistral:7b
CODE_MODEL=qwen2.5-coder:7b
EMBED_MODEL=nomic-embed-text
"""

# =========================
# ⚙️ config.py
# =========================

import os

OLLAMA_URL = os.getenv("OLLAMA_URL")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")
CODE_MODEL = os.getenv("CODE_MODEL")
EMBED_MODEL = os.getenv("EMBED_MODEL")

SAFE_MODE = True

# =========================
# 🤖 llm/ollama_client.py
# =========================

import requests
from config import OLLAMA_URL

class OllamaClient:
    def __init__(self, model):
        self.model = model

    def generate(self, prompt):
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False}
        )
        return response.json()["response"]

# =========================
# 🚀 main.py
# =========================

from core.agent import Agent

if __name__ == "__main__":
    agent = Agent()

    print("🧠 pithy (docker mode) ready")

    while True:
        query = input("\n>> ")
        if query == "exit":
            break

        print("\n🤖", agent.run(query))

# =========================
# 🧠 core/agent.py
# =========================

from llm.ollama_client import OllamaClient
from core.router import Router
from config import DEFAULT_MODEL, CODE_MODEL

class Agent:
    def __init__(self):
        self.router = Router()
        self.chat = OllamaClient(DEFAULT_MODEL)
        self.code = OllamaClient(CODE_MODEL)

    def run(self, query):
        mode = self.router.route(query)

        llm = self.code if mode == "code" else self.chat

        prompt = f"You are pithy, a local AI assistant.\nUser: {query}"
        return llm.generate(prompt)

# =========================
# 🧠 core/router.py
# =========================

class Router:
    def route(self, query):
        q = query.lower()
        if any(k in q for k in ["code", "script", "bug", "error"]):
            return "code"
        return "chat"

# =========================
# 🧰 tools/shell.py
# =========================

import subprocess
from config import SAFE_MODE

class ShellTool:
    def run(self, cmd):
        if SAFE_MODE:
            confirm = input(f"⚠️ Run: {cmd}? (y/n): ")
            if confirm != "y":
                return "cancelled"

        return subprocess.getoutput(cmd)

# =========================
# 🧠 NEXT STEP ROADMAP
# =========================

"""
🔥 PHASE 1 (DONE)
- Docker setup
- Ollama integration
- basic agent

🧠 PHASE 2
- RAG (ChromaDB fully integrated)
- embeddings pipeline

🧩 PHASE 3
- tool system (filesystem + shell)
- safe command execution layer

⚡ PHASE 4
- multi-agent routing
- VSCode integration
- voice interface (optional)
"""
