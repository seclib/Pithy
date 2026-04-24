"""
PIThy - Log Analyzer Tool
Outil permettant à l'Agent d'analyser les logs du système et des services.
"""

import os
import logging

logger = logging.getLogger(__name__)

class LogAnalyzerTool:
    """Analyse les logs du projet (data/logs)."""

    def __init__(self, logs_dir: str = "./data/logs"):
        self.logs_dir = logs_dir
        os.makedirs(self.logs_dir, exist_ok=True)

    def get_tools(self) -> dict:
        """Retourne les outils d'analyse de logs."""
        return {
            "read_logs": self.read_logs,
            "list_log_files": self.list_logs,
            "tail_logs": self.tail_logs,
        }

    def list_logs(self) -> list:
        """Liste les fichiers de logs disponibles."""
        try:
            return [f for f in os.listdir(self.logs_dir) if f.endswith(".log") or f.endswith(".json")]
        except Exception as e:
            return [f"Erreur: {e}"]

    def read_logs(self, filename: str, lines: int = 100) -> str:
        """Lit le contenu d'un fichier de log."""
        path = os.path.join(self.logs_dir, filename)
        if not os.path.isfile(path):
            return f"Fichier non trouvé: {filename}"
        
        try:
            with open(path, "r") as f:
                content = f.readlines()
                return "".join(content[-lines:])
        except Exception as e:
            return f"Erreur lecture: {e}"

    def tail_logs(self, filename: str, n: int = 20) -> str:
        """Affiche les N dernières lignes d'un log."""
        return self.read_logs(filename, lines=n)
