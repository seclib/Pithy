"""
Plugin System Monitor - Infra Layer
Collecte les métriques et gère les alertes de seuils.
"""

import logging

logger = logging.getLogger(__name__)

class Plugin:
    """Composant Infra du System Monitor."""

    def __init__(self):
        self.cpu_threshold = 80.0
        self.ram_threshold = 85.0
        self.alert_count = 0

    def register_hooks(self, registry):
        """Enregistre les hooks système."""
        registry.register("on_start", self.on_start, "system_monitor")
        registry.register("on_tick", self.on_tick, "system_monitor")
        registry.register("on_idle", self.on_idle, "system_monitor")

    def on_start(self, **kwargs):
        logger.info("📊 System Monitor démarré (Seuils: CPU=%s%%, RAM=%s%%)", 
                    self.cpu_threshold, self.ram_threshold)

    def on_tick(self, **kwargs):
        """Vérifie les métriques à chaque cycle."""
        sys_snap = kwargs.get("sys_snap", {})
        docker_snap = kwargs.get("docker_snap", {})
        
        cpu = sys_snap.get("cpu_percent", 0)
        ram = sys_snap.get("memory", {}).get("percent", 0)
        
        # Check thresholds
        if cpu > self.cpu_threshold:
            logger.warning("🚨 [ALERT] Usage CPU critique: %s%%", cpu)
            self.alert_count += 1
            
        if ram > self.ram_threshold:
            logger.warning("🚨 [ALERT] Usage RAM critique: %s%%", ram)
            self.alert_count += 1

    def on_idle(self, **kwargs):
        """Actions en mode inactif."""
        idle_secs = kwargs.get("idle_seconds", 0)
        if idle_secs % 60 == 0: # Log toutes les minutes d'idle
            logger.debug("💤 System Monitor en veille (Système inactif depuis %ss)", idle_secs)
