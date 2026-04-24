"""
PIThy Infra Manager — Manager principal
Point d'entrée du gestionnaire d'infrastructure.
"""

import logging
from infra_manager.scheduler.auto_scaler import AutoScaler

logger = logging.getLogger(__name__)

# Icônes par mode
_MODE_ICONS = {
    "active": "🟢",
    "low_usage": "🟡",
    "idle": "🟠",
    "sleep": "🔴",
}


class InfraManager:
    """
    Gestionnaire d'infrastructure PIThy.
    Interface de haut niveau pour le mini cloud OS IA.
    """

    def __init__(self, compose_dir: str = ".",
                 ollama_url: str = "http://localhost:11434",
                 chroma_url: str = "http://localhost:8000",
                 auto_start: bool = False):
        self.scaler = AutoScaler(compose_dir, ollama_url, chroma_url)

        if auto_start:
            self.start()

    def start(self):
        """Démarre le gestionnaire d'infrastructure."""
        logger.info("🧠 InfraManager démarré")
        self.scaler.start()

    def stop(self):
        """Arrête le gestionnaire d'infrastructure."""
        self.scaler.stop()
        logger.info("🧠 InfraManager arrêté")

    def notify_activity(self):
        """Notifie le système qu'une activité a lieu (réveille si nécessaire)."""
        self.scaler.notify_activity()

    @property
    def mode(self) -> str:
        """Mode opérationnel actuel."""
        return self.scaler.current_mode

    @property
    def predicted_mode(self) -> str:
        """Mode de scaling prédit par le moteur."""
        return self.scaler.predictor.get_recommended_mode()

    def status(self) -> str:
        """Retourne un résumé textuel de l'état."""
        data = self.scaler.get_status()
        state = data["state"]
        system = data["system"]
        docker = data["docker"]
        prediction = self.scaler.predictor.predict()

        icon = _MODE_ICONS.get(state["current"], "⚪")
        pred_icon = _MODE_ICONS.get(prediction.recommended_mode, "⚪")
        mem = system.get("memory", {})

        lines = [
            f"\n{icon} Mode: {state['current'].upper()}",
            f"   Inactif depuis: {state['idle_seconds']}s",
            f"   Dans cet état: {state['seconds_in_state']}s",
            f"   Transitions: {state['transition_count']}",
            f"",
            f"🔮 Prédiction: {pred_icon} {prediction.recommended_mode.upper()} (conf={prediction.confidence:.0%})",
            f"   Raison: {prediction.reason}",
            f"",
            f"   CPU: {system.get('cpu_percent', 0)}%",
            f"   RAM: {mem.get('used_mb', 0)}MB / {mem.get('total_mb', 0)}MB ({mem.get('percent', 0)}%)",
            f"   Docker: {'✅' if docker.get('docker_available') else '❌'}"
            f" ({docker.get('running_containers', 0)} containers actifs)",
        ]

        # Services
        services = docker.get("services", {})
        if services:
            lines.append("")
            for svc, running in services.items():
                svc_icon = "🟢" if running else "🔴"
                lines.append(f"   {svc_icon} {svc}")

        # Plugins
        infra_plugins = self.scaler.plugin_manager.list_plugins()
        lines.append(f"\n{infra_plugins}")

        return "\n".join(lines)
