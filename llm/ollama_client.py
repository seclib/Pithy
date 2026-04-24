"""
PIThy - Client Ollama
Communication avec le serveur Ollama pour la génération LLM.
"""

import logging
import requests
from config import OLLAMA_URL

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client pour l'API Ollama (génération de texte)."""

    def __init__(self, model: str, timeout: int = 120):
        self.model = model
        self.timeout = timeout
        self.base_url = OLLAMA_URL

    def generate(self, prompt: str) -> str:
        """Génère une réponse via Ollama."""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "[Erreur] Réponse vide du LLM")
        except requests.ConnectionError:
            logger.error("Impossible de se connecter à Ollama (%s)", self.base_url)
            return f"[Erreur] Ollama non joignable ({self.base_url})"
        except requests.Timeout:
            logger.error("Timeout Ollama après %ds", self.timeout)
            return "[Erreur] Timeout — la génération a pris trop de temps"
        except requests.HTTPError as e:
            logger.error("Erreur HTTP Ollama: %s", e)
            return f"[Erreur] Ollama HTTP {e.response.status_code}"
        except Exception as e:
            logger.error("Erreur inattendue Ollama: %s", e)
            return f"[Erreur] {e}"

    def is_available(self) -> bool:
        """Vérifie la disponibilité du serveur Ollama."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list:
        """Liste les modèles disponibles sur Ollama."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=10)
            r.raise_for_status()
            data = r.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []
