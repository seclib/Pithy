"""
Plugin Infra: VSCode Bridge
Simule l'envoi de notifications à VSCode lors des événements d'infrastructure.
"""

import logging
import json

logger = logging.getLogger(__name__)

class Plugin:
    """Plugin d'intégration simulant un pont avec VSCode."""

    def register_hooks(self, registry):
        """Enregistre les hooks pour surveiller le cycle de vie de l'infra."""
        registry.register("on_scale_up", self.notify_vsc_scale_up, "vsc_bridge")
        registry.register("on_scale_down", self.notify_vsc_scale_down, "vsc_bridge")
        registry.register("on_predict", self.notify_vsc_prediction, "vsc_bridge")

    def _send_to_vsc(self, message_type: str, payload: dict):
        """Simule l'envoi d'un message via un pipe ou socket JSON-RPC."""
        msg = {
            "source": "pithy-infra",
            "type": message_type,
            "payload": payload
        }
        # Ici on log en INFO pour simuler la sortie vers l'extension VSC
        logger.info(f"🔌 [VSC-BRIDGE] Sending to VSCode: {json.dumps(msg)}")

    def notify_vsc_scale_up(self, **kwargs):
        service = kwargs.get("service", "unknown")
        reason = kwargs.get("reason", "manual")
        self._send_to_vsc("notification", {
            "title": f"PIThy: Scaling Up {service}",
            "message": f"Démarrage anticipé pour {service} ({reason})",
            "severity": "info"
        })

    def notify_vsc_scale_down(self, **kwargs):
        service = kwargs.get("service", "unknown")
        self._send_to_vsc("notification", {
            "title": f"PIThy: Scaling Down",
            "message": f"Service {service} arrêté pour économiser des ressources",
            "severity": "warn"
        })

    def notify_vsc_prediction(self, **kwargs):
        prediction = kwargs.get("prediction")
        if prediction and prediction.confidence > 0.8:
            self._send_to_vsc("status_bar", {
                "text": f"$(zap) PIThy: Charge prévue imminente",
                "tooltip": prediction.reason
            })
