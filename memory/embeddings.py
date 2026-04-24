"""
PIThy - Module d'embeddings
Génération de vecteurs via le modèle nomic-embed-text sur Ollama.
"""

import logging
import requests
from config import OLLAMA_URL, EMBED_MODEL

logger = logging.getLogger(__name__)


class Embeddings:
    """Génère des embeddings via Ollama."""

    def __init__(self):
        self.model = EMBED_MODEL
        self.base_url = OLLAMA_URL

    def embed(self, text: str) -> list:
        """Retourne le vecteur d'embedding pour un texte donné."""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            embedding = data.get("embedding")
            if not embedding:
                logger.error("Embedding vide retourné par Ollama")
                return []
            return embedding
        except requests.ConnectionError:
            logger.error("Impossible de se connecter à Ollama pour les embeddings")
            return []
        except requests.Timeout:
            logger.error("Timeout lors de la génération d'embedding")
            return []
        except Exception as e:
            logger.error("Erreur embedding: %s", e)
            return []
