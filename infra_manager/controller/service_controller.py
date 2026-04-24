"""
PIThy Infra Manager — Service Controller
Gestion de haut niveau des services avec dépendances.
"""

import logging

logger = logging.getLogger(__name__)

# Graphe de dépendances des services
SERVICE_DEPENDENCIES = {
    "pithy": ["chroma"],   # pithy dépend de chroma
    "chroma": [],          # chroma est autonome
}

# Services critiques qui ne doivent JAMAIS être stoppés sans logique explicite
CRITICAL_SERVICES = {"chroma"}


class ServiceController:
    """Gestion intelligente des services avec respect des dépendances."""

    def __init__(self, docker_controller):
        self.docker = docker_controller

    def start_with_deps(self, service: str) -> bool:
        """Démarre un service et toutes ses dépendances."""
        deps = SERVICE_DEPENDENCIES.get(service, [])

        # Démarrer les dépendances d'abord
        for dep in deps:
            logger.info("Démarrage de la dépendance: %s", dep)
            if not self.docker.start_service(dep):
                logger.error("Impossible de démarrer la dépendance: %s", dep)
                return False

        # Démarrer le service principal
        return self.docker.start_service(service)

    def stop_safe(self, service: str) -> bool:
        """Arrête un service de manière sûre (vérifie les dépendants)."""
        # Vérifier si d'autres services dépendent de celui-ci
        dependents = self._get_dependents(service)
        if dependents:
            logger.warning(
                "Service '%s' a des dépendants actifs: %s — arrêt de la chaîne",
                service, dependents,
            )
            # Arrêter les dépendants d'abord
            for dep in dependents:
                self.docker.stop_service(dep)

        return self.docker.stop_service(service)

    def _get_dependents(self, service: str) -> list:
        """Retourne la liste des services qui dépendent du service donné."""
        dependents = []
        for svc, deps in SERVICE_DEPENDENCIES.items():
            if service in deps:
                dependents.append(svc)
        return dependents

    def ensure_running(self, services: list) -> bool:
        """S'assure que tous les services listés sont démarrés."""
        all_ok = True
        for svc in services:
            if not self.start_with_deps(svc):
                all_ok = False
        return all_ok

    def stop_non_essential(self, essential: list = None) -> int:
        """Arrête tous les services non essentiels."""
        essential = set(essential or [])
        stopped = 0

        for svc in SERVICE_DEPENDENCIES:
            if svc not in essential:
                if self.docker.stop_service(svc):
                    stopped += 1

        return stopped
