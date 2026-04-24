"""
PIThy - Outil Filesystem sécurisé
Opérations fichiers avec sandbox de chemin.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FilesystemTool:
    """Opérations fichiers sécurisées avec restriction de chemin."""

    def __init__(self, base_path: str = ".", safe_mode: bool = True):
        self.base_path = Path(base_path).resolve()
        self.safe_mode = safe_mode

    def is_safe_path(self, path: str) -> bool:
        """Vérifie que le chemin reste dans le répertoire autorisé."""
        full_path = (self.base_path / path).resolve()
        try:
            full_path.relative_to(self.base_path)
            return True
        except ValueError:
            return False

    def read_file(self, path: str, max_lines: int = 100) -> str:
        """Lit un fichier de manière sécurisée."""
        if self.safe_mode and not self.is_safe_path(path):
            return "[Erreur] Accès hors du répertoire autorisé"

        try:
            full_path = self.base_path / path

            if not full_path.exists():
                return "[Erreur] Fichier non trouvé"

            if not full_path.is_file():
                return "[Erreur] Ce n'est pas un fichier"

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[:max_lines]
                return "".join(lines)

        except Exception as e:
            logger.error("Erreur lecture: %s", e)
            return f"[Erreur] {e}"

    def list_directory(self, path: str = ".") -> str:
        """Liste les fichiers d'un répertoire."""
        if self.safe_mode and not self.is_safe_path(path):
            return "[Erreur] Accès hors du répertoire autorisé"

        try:
            full_path = self.base_path / path

            if not full_path.exists():
                return "[Erreur] Répertoire non trouvé"

            if not full_path.is_dir():
                return "[Erreur] Ce n'est pas un répertoire"

            items = sorted(full_path.iterdir())
            result = []

            for item in items:
                prefix = "📁" if item.is_dir() else "📄"
                result.append(f"{prefix} {item.name}")

            return "\n".join(result) if result else "[Vide]"

        except Exception as e:
            logger.error("Erreur listing: %s", e)
            return f"[Erreur] {e}"

    def write_file(self, path: str, content: str) -> str:
        """Écrit dans un fichier de manière sécurisée."""
        if self.safe_mode and not self.is_safe_path(path):
            return "[Erreur] Accès hors du répertoire autorisé"

        try:
            full_path = self.base_path / path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"[Succès] Fichier écrit: {path}"

        except Exception as e:
            logger.error("Erreur écriture: %s", e)
            return f"[Erreur] {e}"
