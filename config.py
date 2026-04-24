"""
PIThy - Configuration centralisée
Mini OS IA local — charge les variables d'environnement avec des valeurs par défaut.
"""

import os
import logging

# =========================
# 🔗 Connexions externes
# =========================

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CHROMA_URL = os.getenv("CHROMA_URL", "http://localhost:8000")

# =========================
# 🤖 Modèles LLM
# =========================

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "dolphin-mistral:7b")
CODE_MODEL = os.getenv("CODE_MODEL", "qwen2.5-coder:7b")
REASONING_MODEL = os.getenv("REASONING_MODEL", "dolphin-mistral:7b")
LIGHT_MODEL = os.getenv("LIGHT_MODEL", "dolphin-mistral:7b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# Registre des modèles disponibles par rôle
MODEL_REGISTRY = {
    "chat": DEFAULT_MODEL,
    "code": CODE_MODEL,
    "reasoning": REASONING_MODEL,
    "light": LIGHT_MODEL,
}

# =========================
# 🔐 Sécurité
# =========================

SAFE_MODE = os.getenv("SAFE_MODE", "true").lower() in ("true", "1", "yes")

# =========================
# 🧠 RAG
# =========================

RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "500"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))

# =========================
# 🔌 Plugins
# =========================

PLUGINS_DIR = os.getenv("PLUGINS_DIR", "./plugins")

# =========================
# 📁 Chemins
# =========================

DATA_DIR = os.getenv("DATA_DIR", "./data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
DB_DIR = os.path.join(DATA_DIR, "db")

# Création des répertoires si nécessaire
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(PLUGINS_DIR, exist_ok=True)

# =========================
# 📝 Logging
# =========================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "pithy.log"), encoding="utf-8"),
    ],
)
