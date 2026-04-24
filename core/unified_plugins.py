"""
PIThy AI Automation Platform — Unified Plugin Loader
Permet de charger des plugins "Full Stack" (Agent + Infra) depuis un seul dossier.
"""

import os
import json
import logging
import importlib.util

logger = logging.getLogger(__name__)

class UnifiedPluginLoader:
    """Chargeur de plugins unifié pour toute la plateforme PIThy."""

    def __init__(self, platform_core, plugins_dir="./plugins"):
        self.os = platform_core
        self.plugins_dir = plugins_dir
        self.loaded_plugins = {}

    def load_all(self):
        """Scanne et charge tous les plugins du répertoire /plugins."""
        if not os.path.isdir(self.plugins_dir):
            logger.warning(f"Répertoire plugins non trouvé: {self.plugins_dir}")
            return

        for entry in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, entry)
            if not os.path.isdir(plugin_path):
                continue

            meta_file = os.path.join(plugin_path, "plugin.json")
            if not os.path.isfile(meta_file):
                continue

            self._load_plugin(plugin_path)

    def _load_plugin(self, path):
        """Charge un plugin unique et distribue ses composants aux couches respectives."""
        try:
            with open(os.path.join(path, "plugin.json"), "r") as f:
                meta = json.load(f)
            
            name = meta.get("name", os.path.basename(path))
            enabled = meta.get("enabled", True)
            
            if not enabled:
                return

            logger.info(f"🔌 Chargement du plugin unifié: {name}")

            # 1. Composant AGENT (Tools)
            agent_file = os.path.join(path, "agent.py")
            if os.path.isfile(agent_file):
                self._load_agent_component(name, agent_file)

            # 2. Composant INFRA (Hooks)
            infra_file = os.path.join(path, "infra.py")
            if os.path.isfile(infra_file):
                self._load_infra_component(name, infra_file)

            self.loaded_plugins[name] = meta
            
        except Exception as e:
            logger.error(f"Erreur chargement plugin {path}: {e}")

    def _load_agent_component(self, name, file_path):
        """Charge la partie Agent du plugin."""
        try:
            spec = importlib.util.spec_from_file_location(f"plugins.{name}.agent", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "Plugin"):
                plugin_instance = module.Plugin()
                # Enregistre le plugin dans le loader de l'agent
                self.os.agent.plugins.register_plugin(name, plugin_instance)
                logger.info(f"  🤖 Composant Agent chargé pour {name}")
        except Exception as e:
            logger.error(f"  ❌ Erreur composant Agent ({name}): {e}")

    def _load_infra_component(self, name, file_path):
        """Charge la partie Infra du plugin."""
        try:
            spec = importlib.util.spec_from_file_location(f"plugins.{name}.infra", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "Plugin"):
                plugin_instance = module.Plugin()
                # Enregistre les hooks dans le registry de l'infra
                plugin_instance.register_hooks(self.os.infra.scaler.plugin_manager.hooks)
                logger.info(f"  ⚙️ Composant Infra chargé pour {name}")
        except Exception as e:
            logger.error(f"  ❌ Erreur composant Infra ({name}): {e}")
