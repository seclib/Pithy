"""
PIThy - Outil Shell sécurisé
Exécution de commandes Linux avec validation et blacklist.
"""

import subprocess
import logging

logger = logging.getLogger(__name__)


class ShellTool:
    """Exécution sécurisée de commandes shell."""

    def __init__(self, safe_mode: bool = True):
        self.safe_mode = safe_mode

        # Blacklist de commandes/patterns dangereux
        self.dangerous_keywords = [
            "rm -rf /",
            "rm -rf /*",
            ":(){ :|:& };:",
            "mkfs",
            "dd if=",
            "shutdown",
            "reboot",
            "halt",
            "init 0",
            "init 6",
            "> /dev/sda",
            "chmod -R 777 /",
            "chown -R",
            "format",
            "fdisk",
            "parted",
            "wipefs",
        ]

    def is_safe(self, command: str) -> bool:
        """Vérifie qu'une commande n'est pas dans la blacklist."""
        cmd_lower = command.lower().strip()
        for bad in self.dangerous_keywords:
            if bad in cmd_lower:
                return False
        return True

    def run(self, command: str, timeout: int = 30) -> dict:
        """
        Exécute une commande shell.

        Retourne un dict avec:
            - stdout: sortie standard
            - stderr: sortie d'erreur
            - returncode: code de retour
            - status: 'ok', 'blocked', 'cancelled', 'error', 'timeout'
        """

        # Vérification blacklist
        if self.safe_mode and not self.is_safe(command):
            logger.warning("Commande bloquée (blacklist): %s", command)
            return {
                "stdout": "",
                "stderr": "Commande bloquée — pattern dangereux détecté",
                "returncode": -1,
                "status": "blocked",
            }

        # Validation utilisateur obligatoire en SAFE_MODE
        if self.safe_mode:
            try:
                confirm = input(f"\n⚠️  Exécuter: {command} ? (y/n): ")
                if confirm.strip().lower() != "y":
                    logger.info("Commande annulée par l'utilisateur: %s", command)
                    return {
                        "stdout": "",
                        "stderr": "Annulé par l'utilisateur",
                        "returncode": -1,
                        "status": "cancelled",
                    }
            except EOFError:
                return {
                    "stdout": "",
                    "stderr": "Entrée non disponible — commande annulée",
                    "returncode": -1,
                    "status": "cancelled",
                }

        # Exécution
        try:
            logger.info("Exécution shell: %s", command)
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "status": "ok",
            }
        except subprocess.TimeoutExpired:
            logger.error("Timeout commande (%ds): %s", timeout, command)
            return {
                "stdout": "",
                "stderr": f"Timeout après {timeout}s",
                "returncode": -1,
                "status": "timeout",
            }
        except Exception as e:
            logger.error("Erreur exécution shell: %s", e)
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "status": "error",
            }
