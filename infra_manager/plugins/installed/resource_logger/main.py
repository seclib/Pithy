"""
Plugin Infra: Resource Logger
Log tous les événements d'infrastructure pour analyse.
"""

import time
import logging

logger = logging.getLogger(__name__)


class Plugin:
    """Plugin de logging des événements infra."""

    def __init__(self):
        self._log = []

    def register_hooks(self, registry):
        """Enregistre les hooks de ce plugin."""
        registry.register("on_start", self.on_start, "resource_logger")
        registry.register("on_stop", self.on_stop, "resource_logger")
        registry.register("on_transition", self.on_transition, "resource_logger")
        registry.register("on_scale_up", self.on_scale_up, "resource_logger")
        registry.register("on_scale_down", self.on_scale_down, "resource_logger")
        registry.register("on_idle", self.on_idle, "resource_logger")

    def _record(self, event_type: str, details: str):
        """Enregistre un événement."""
        entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": event_type,
            "details": details,
        }
        self._log.append(entry)
        logger.info("📊 [ResourceLogger] %s: %s", event_type, details)

    def on_start(self, **kwargs):
        service = kwargs.get("service", "unknown")
        self._record("START", f"Service démarré: {service}")

    def on_stop(self, **kwargs):
        service = kwargs.get("service", "unknown")
        self._record("STOP", f"Service arrêté: {service}")

    def on_transition(self, **kwargs):
        old = kwargs.get("from_state", "?")
        new = kwargs.get("to_state", "?")
        self._record("TRANSITION", f"{old} → {new}")

    def on_scale_up(self, **kwargs):
        self._record("SCALE_UP", str(kwargs))

    def on_scale_down(self, **kwargs):
        self._record("SCALE_DOWN", str(kwargs))

    def on_idle(self, **kwargs):
        seconds = kwargs.get("idle_seconds", 0)
        self._record("IDLE", f"Inactif depuis {seconds}s")

    def get_log(self) -> list:
        """Retourne l'historique des événements."""
        return list(self._log)
