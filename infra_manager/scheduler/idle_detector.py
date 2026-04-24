"""
PIThy Infra Manager — Idle Detector
Détecte l'inactivité basée sur plusieurs signaux.
"""

import time
import logging
import requests

logger = logging.getLogger(__name__)


class IdleDetector:
    """Détecte l'inactivité du système via plusieurs signaux."""

    def __init__(self, ollama_url: str = "http://localhost:11434",
                 chroma_url: str = "http://localhost:8000"):
        self.ollama_url = ollama_url
        self.chroma_url = chroma_url
        self.last_ollama_check = 0
        self.last_chroma_check = 0
        self._ollama_active = False
        self._chroma_active = False

    def check_ollama_activity(self) -> bool:
        """Vérifie si Ollama traite des requêtes."""
        try:
            r = requests.get(
                f"{self.ollama_url}/api/ps",
                timeout=3,
            )
            if r.status_code == 200:
                data = r.json()
                models = data.get("models", [])
                self._ollama_active = len(models) > 0
                self.last_ollama_check = time.time()
                return self._ollama_active
        except Exception:
            pass
        return False

    def check_chroma_activity(self) -> bool:
        """Vérifie si ChromaDB est accessible."""
        try:
            r = requests.get(
                f"{self.chroma_url}/api/v1/heartbeat",
                timeout=3,
            )
            self._chroma_active = r.status_code == 200
            self.last_chroma_check = time.time()
            return self._chroma_active
        except Exception:
            self._chroma_active = False
            return False

    def is_system_idle(self, cpu_percent: float, idle_threshold: float = 10.0) -> bool:
        """
        Détermine si le système est idle en combinant:
        - CPU < seuil
        - Aucun modèle Ollama chargé
        """
        cpu_idle = cpu_percent < idle_threshold
        ollama_idle = not self.check_ollama_activity()
        return cpu_idle and ollama_idle

    def snapshot(self) -> dict:
        """Snapshot de l'état d'activité."""
        return {
            "timestamp": time.time(),
            "ollama_active": self._ollama_active,
            "chroma_active": self._chroma_active,
        }
