"""
PIThy Infra Manager — Docker Monitor
Surveille l'état des containers Docker, leur santé et consommation.
"""

import json
import subprocess
import logging
import time

logger = logging.getLogger(__name__)


class ContainerInfo:
    """Informations sur un container Docker."""

    def __init__(self, data: dict):
        self.id = data.get("ID", "")[:12]
        self.name = data.get("Names", "unknown")
        self.status = data.get("Status", "unknown")
        self.state = data.get("State", "unknown")
        self.image = data.get("Image", "")
        self.ports = data.get("Ports", "")

    @property
    def is_running(self) -> bool:
        return self.state == "running"

    @property
    def is_healthy(self) -> bool:
        return "healthy" in self.status.lower()

    def __repr__(self):
        icon = "🟢" if self.is_running else "🔴"
        return f"{icon} {self.name} ({self.state})"


class DockerMonitor:
    """Monitore les containers Docker du projet PIThy."""

    PROJECT_PREFIX = "pithy_"

    def __init__(self):
        self._docker_available = self._check_docker()

    def _check_docker(self) -> bool:
        """Vérifie si Docker est disponible."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    @property
    def available(self) -> bool:
        return self._docker_available

    def list_containers(self, all_containers: bool = True) -> list[ContainerInfo]:
        """Liste les containers PIThy."""
        if not self._docker_available:
            return []

        try:
            cmd = ["docker", "ps", "--format", "{{json .}}"]
            if all_containers:
                cmd.insert(2, "-a")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return []

            containers = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    name = data.get("Names", "")
                    if name.startswith(self.PROJECT_PREFIX):
                        containers.append(ContainerInfo(data))
                except json.JSONDecodeError:
                    continue

            return containers
        except Exception as e:
            logger.error("Erreur listing containers: %s", e)
            return []

    def get_container_stats(self, container_name: str) -> dict:
        """Retourne les stats CPU/RAM d'un container."""
        if not self._docker_available:
            return {}

        try:
            result = subprocess.run(
                [
                    "docker", "stats", container_name,
                    "--no-stream", "--format",
                    '{"cpu":"{{.CPUPerc}}","mem":"{{.MemUsage}}","mem_pct":"{{.MemPerc}}"}',
                ],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return {}

            raw = result.stdout.strip()
            if not raw:
                return {}

            return json.loads(raw)
        except Exception as e:
            logger.debug("Stats error for %s: %s", container_name, e)
            return {}

    def is_container_running(self, name: str) -> bool:
        """Vérifie si un container spécifique est en cours d'exécution."""
        containers = self.list_containers()
        for c in containers:
            if c.name == name and c.is_running:
                return True
        return False

    def get_pithy_status(self) -> dict:
        """Retourne l'état de tous les services PIThy."""
        containers = self.list_containers()

        status = {
            "pithy_core": {"running": False, "healthy": False},
            "pithy_chroma": {"running": False, "healthy": False},
        }

        for c in containers:
            if c.name in status:
                status[c.name] = {
                    "running": c.is_running,
                    "healthy": c.is_healthy,
                    "status": c.status,
                }

        return status

    def snapshot(self) -> dict:
        """Snapshot complet de l'état Docker."""
        containers = self.list_containers()
        running = [c for c in containers if c.is_running]

        return {
            "timestamp": time.time(),
            "docker_available": self._docker_available,
            "total_containers": len(containers),
            "running_containers": len(running),
            "services": {c.name: c.is_running for c in containers},
        }
