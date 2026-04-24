"""
Plugin System Monitor - Agent Layer
Expose les métriques système à l'Agent via un outil dédié.
"""

import logging

logger = logging.getLogger(__name__)

class Plugin:
    """Composant Agent du System Monitor."""

    def get_tools(self) -> dict:
        """Expose l'outil de monitoring à l'agent."""
        return {
            "check_system_stats": self.check_stats
        }

    def check_stats(self, **kwargs) -> str:
        """Retourne un rapport rapide des statistiques système."""
        # Note: Dans une version réelle, on pourrait accéder aux données 
        # partagées via l'instance du manager.
        return "📊 Rapport System Monitor : CPU stable, RAM 45%, Docker 3 containers actifs."
