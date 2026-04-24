"""
PIThy Infra Manager — Plugin Manager
Chargeur dynamique de plugins pour l'infra manager.

Structure d'un plugin infra:
    infra_manager/plugins/<name>/
        plugin.json   → métadonnées
        main.py       → classe Plugin avec register_hooks()
        hooks.py      → (optionnel) fonctions de hook
"""

import os
import json
import importlib.util
import logging
from infra_manager.plugins.hooks import HookRegistry

logger = logging.getLogger(__name__)

_PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "installed")


class InfraPluginInfo:
    """Métadonnées d'un plugin infra."""

    def __init__(self, path: str, metadata: dict):
        self.path = path
        self.name = metadata.get("name", "unknown")
        self.version = metadata.get("version", "0.0.0")
        self.plugin_type = metadata.get("type", "infra")
        self.description = metadata.get("description", "")
        self.enabled = metadata.get("enabled", True)
        self.instance = None

    def __repr__(self):
        status = "✅" if self.enabled else "❌"
        return f"{status} {self.name} v{self.version} [{self.plugin_type}]"


class InfraPluginManager:
    """Gestionnaire de plugins pour l'infra manager."""

    def __init__(self, plugins_dir: str = None):
        self.plugins_dir = plugins_dir or _PLUGINS_DIR
        self.hooks = HookRegistry()
        self.plugins: dict[str, InfraPluginInfo] = {}
        os.makedirs(self.plugins_dir, exist_ok=True)
        self._scan()

    def _scan(self):
        """Scanne le répertoire des plugins."""
        if not os.path.isdir(self.plugins_dir):
            return

        for entry in sorted(os.listdir(self.plugins_dir)):
            plugin_path = os.path.join(self.plugins_dir, entry)
            if not os.path.isdir(plugin_path):
                continue

            meta_file = os.path.join(plugin_path, "plugin.json")
            main_file = os.path.join(plugin_path, "main.py")

            if not os.path.isfile(meta_file) or not os.path.isfile(main_file):
                continue

            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                info = InfraPluginInfo(plugin_path, metadata)
                self.plugins[info.name] = info
                logger.info("Plugin infra détecté: %s", info)
            except Exception as e:
                logger.warning("Plugin infra invalide %s: %s", entry, e)

    def load(self, name: str) -> bool:
        """Charge un plugin et enregistre ses hooks."""
        if name not in self.plugins:
            return False

        info = self.plugins[name]
        if not info.enabled:
            return False

        try:
            main_file = os.path.join(info.path, "main.py")
            spec = importlib.util.spec_from_file_location(
                f"infra_plugins.{name}", main_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "Plugin"):
                info.instance = module.Plugin()

                # Enregistrer les hooks du plugin
                if hasattr(info.instance, "register_hooks"):
                    info.instance.register_hooks(self.hooks)

                logger.info("Plugin infra chargé: %s", name)
                return True
            else:
                logger.warning("Plugin %s: classe 'Plugin' manquante", name)
                return False
        except Exception as e:
            logger.error("Erreur chargement plugin infra %s: %s", name, e)
            return False

    def load_all(self) -> int:
        """Charge tous les plugins activés."""
        loaded = 0
        for name, info in self.plugins.items():
            if info.enabled and self.load(name):
                loaded += 1
        logger.info("Plugins infra chargés: %d/%d", loaded, len(self.plugins))
        return loaded

    def unload(self, name: str) -> bool:
        """Décharge un plugin et retire ses hooks."""
        if name not in self.plugins:
            return False

        info = self.plugins[name]
        if info.instance:
            self.hooks.unregister_all(name)
            info.instance = None
            logger.info("Plugin infra déchargé: %s", name)
        return True

    def trigger_hook(self, hook_name: str, **kwargs) -> list:
        """Déclenche un hook sur tous les plugins enregistrés."""
        return self.hooks.trigger(hook_name, **kwargs)

    def list_plugins(self) -> str:
        """Résumé textuel des plugins."""
        if not self.plugins:
            return "Aucun plugin infra installé."
        lines = ["🔌 Plugins Infra:"]
        for info in self.plugins.values():
            lines.append(f"  {info}")
        return "\n".join(lines)
