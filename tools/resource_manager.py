"""
PIThy - Resource Manager Tool
Outil permettant à l'Agent d'interagir avec sa propre infrastructure.
"""

import logging

logger = logging.getLogger(__name__)

class ResourceManagerTool:
    """Outil de contrôle de l'infrastructure pour l'Agent."""

    def __init__(self, infra_manager):
        self.infra = infra_manager

    def get_tools(self) -> dict:
        """Retourne les fonctions utilisables par l'agent."""
        return {
            "get_system_health": self.get_health,
            "scale_up": self.scale_up,
            "scale_down": self.scale_down,
            "get_prediction": self.get_prediction,
        }

    def get_health(self) -> str:
        """Donne l'état de santé du système."""
        return self.infra.status()

    def scale_up(self, service: str = None) -> str:
        """Déclenche manuellement un scale up."""
        if service:
            success = self.infra.scaler.service_controller.start_with_deps(service)
            return f"✅ Service {service} démarré" if success else f"❌ Échec démarrage {service}"
        
        self.infra.notify_activity()
        return "⚡ Activation globale de l'infrastructure déclenchée"

    def scale_down(self, mode: str = "idle") -> str:
        """Force un passage en mode économique."""
        if mode == "sleep":
            self.infra.scaler.state_engine.transition("sleep", min_interval=0)
            self.infra.scaler.service_controller.stop_non_essential()
            return "🌙 Système mis en veille"
        
        self.infra.scaler.state_engine.transition("idle", min_interval=0)
        self.infra.scaler.service_controller.stop_non_essential(essential=["chroma"])
        return "🟠 Système passé en mode IDLE"

    def get_prediction(self) -> str:
        """Retourne la prédiction du moteur de scaling."""
        pred = self.infra.scaler.predictor.predict()
        return str(pred)
