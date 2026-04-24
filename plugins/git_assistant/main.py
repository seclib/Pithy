"""
Plugin: Git Assistant
Fournit des commandes Git simplifiées.
"""

import subprocess


class Plugin:
    """Plugin d'intégration Git."""

    def get_tools(self) -> dict:
        """Retourne les outils disponibles."""
        return {
            "status": self.git_status,
            "log": self.git_log,
            "branch": self.git_branch,
            "diff": self.git_diff,
        }

    def execute(self, command: str = "status") -> str:
        """Point d'entrée principal."""
        tools = self.get_tools()
        if command in tools:
            return tools[command]()
        return f"Commande inconnue: {command}. Disponibles: {', '.join(tools.keys())}"

    def git_status(self) -> str:
        """git status."""
        try:
            return subprocess.getoutput("git status --short 2>&1")
        except Exception as e:
            return f"[Erreur] {e}"

    def git_log(self) -> str:
        """Derniers commits."""
        try:
            return subprocess.getoutput(
                "git log --oneline -10 2>&1"
            )
        except Exception as e:
            return f"[Erreur] {e}"

    def git_branch(self) -> str:
        """Branches locales."""
        try:
            return subprocess.getoutput("git branch -a 2>&1")
        except Exception as e:
            return f"[Erreur] {e}"

    def git_diff(self) -> str:
        """Diff des changements non commités."""
        try:
            return subprocess.getoutput("git diff --stat 2>&1")
        except Exception as e:
            return f"[Erreur] {e}"
