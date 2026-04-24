"""
PIThy Infra Manager — Docker Controller
Contrôle le cycle de vie des containers Docker (start/stop/restart).
"""

import subprocess
import logging
import time

logger = logging.getLogger(__name__)

# Protection anti-boucle: temps minimum entre deux actions sur le même service
_MIN_ACTION_INTERVAL = 30  # secondes


class DockerController:
    """Contrôle les containers Docker du projet PIThy."""

    def __init__(self, compose_dir: str = "."):
        self.compose_dir = compose_dir
        self._last_action: dict[str, float] = {}  # service -> timestamp

    def _throttle_check(self, service: str) -> bool:
        """Vérifie le throttle anti-boucle. Retourne True si l'action est autorisée."""
        now = time.time()
        last = self._last_action.get(service, 0)
        if now - last < _MIN_ACTION_INTERVAL:
            remaining = int(_MIN_ACTION_INTERVAL - (now - last))
            logger.warning(
                "Throttle: action sur '%s' bloquée (%ds restants)",
                service, remaining,
            )
            return False
        return True

    def _record_action(self, service: str):
        """Enregistre le timestamp de la dernière action."""
        self._last_action[service] = time.time()

    def _compose(self, *args, timeout: int = 60) -> tuple[bool, str]:
        """Exécute une commande docker compose."""
        cmd = ["docker", "compose", "-f",
               f"{self.compose_dir}/docker-compose.yml"] + list(args)
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
            )
            output = result.stdout + result.stderr
            success = result.returncode == 0
            if not success:
                logger.error("docker compose %s failed: %s", " ".join(args), output[:200])
            return success, output
        except subprocess.TimeoutExpired:
            logger.error("docker compose %s timeout (%ds)", " ".join(args), timeout)
            return False, "timeout"
        except Exception as e:
            logger.error("docker compose error: %s", e)
            return False, str(e)

    # ------------------------------------------------------------------
    # Actions sur les services
    # ------------------------------------------------------------------

    def start_service(self, service: str) -> bool:
        """Démarre un service spécifique."""
        if not self._throttle_check(service):
            return False

        logger.info("▶️  Démarrage de '%s'", service)
        success, _ = self._compose("up", "-d", service)
        if success:
            self._record_action(service)
            logger.info("✅ Service '%s' démarré", service)
        return success

    def stop_service(self, service: str) -> bool:
        """Arrête un service spécifique."""
        if not self._throttle_check(service):
            return False

        logger.info("⏹️  Arrêt de '%s'", service)
        success, _ = self._compose("stop", service)
        if success:
            self._record_action(service)
            logger.info("✅ Service '%s' arrêté", service)
        return success

    def restart_service(self, service: str) -> bool:
        """Redémarre un service spécifique."""
        if not self._throttle_check(service):
            return False

        logger.info("🔄 Redémarrage de '%s'", service)
        success, _ = self._compose("restart", service)
        if success:
            self._record_action(service)
            logger.info("✅ Service '%s' redémarré", service)
        return success

    def start_all(self) -> bool:
        """Démarre tous les services."""
        logger.info("▶️  Démarrage de tous les services")
        success, _ = self._compose("up", "-d")
        if success:
            for svc in ["chroma", "pithy"]:
                self._record_action(svc)
        return success

    def stop_all(self) -> bool:
        """Arrête tous les services."""
        logger.info("⏹️  Arrêt de tous les services")
        success, _ = self._compose("down")
        if success:
            for svc in ["chroma", "pithy"]:
                self._record_action(svc)
        return success

    def build(self) -> bool:
        """Reconstruit les images."""
        logger.info("🔨 Build des images")
        success, _ = self._compose("build", timeout=300)
        return success
