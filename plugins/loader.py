"""
PIThy - Plugin System
Chargeur dynamique de plugins pour le mini OS IA.

Structure d'un plugin:
    plugins/<name>/
        plugin.json   → métadonnées (name, version, type, description, enabled)
        main.py       → point d'entrée (classe Plugin avec register/execute)
"""

import os
import json
import importlib.util
import logging
from config import PLUGINS_DIR

logger = logging.getLogger(__name__)


class PluginInfo:
    """Métadonnées d'un plugin."""

    def __init__(self, path: str, metadata: dict):
        self.path = path
        self.name = metadata.get("name", "unknown")
        self.version = metadata.get("version", "0.0.0")
        self.plugin_type = metadata.get("type", "tool")  # tool, intelligence, integration
        self.description = metadata.get("description", "")
        self.enabled = metadata.get("enabled", True)
        self.instance = None

    def __repr__(self):
        status = "✅" if self.enabled else "❌"
        return f"{status} {self.name} v{self.version} [{self.plugin_type}] — {self.description}"


class PluginLoader:
    """Scanne, charge et gère les plugins dynamiquement."""

    def __init__(self, plugins_dir: str = None):
        self.plugins_dir = plugins_dir or PLUGINS_DIR
        self.plugins: dict[str, PluginInfo] = {}
        self._scan()

    def _scan(self):
        """Scanne le répertoire des plugins."""
        if not os.path.isdir(self.plugins_dir):
            logger.info("Aucun répertoire plugins: %s", self.plugins_dir)
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

                info = PluginInfo(plugin_path, metadata)
                self.plugins[info.name] = info
                logger.info("Plugin détecté: %s", info)
            except Exception as e:
                logger.warning("Plugin invalide dans %s: %s", entry, e)

    def load(self, name: str) -> bool:
        """Charge un plugin spécifique."""
        if name not in self.plugins:
            logger.warning("Plugin inconnu: %s", name)
            return False

        info = self.plugins[name]
        if not info.enabled:
            logger.info("Plugin désactivé: %s", name)
            return False

        try:
            main_file = os.path.join(info.path, "main.py")
            spec = importlib.util.spec_from_file_location(
                f"plugins.{name}.main", main_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Le plugin doit exposer une classe Plugin
            if hasattr(module, "Plugin"):
                info.instance = module.Plugin()
                logger.info("Plugin chargé: %s", name)
                return True
            else:
                logger.warning("Plugin %s: classe 'Plugin' manquante", name)
                return False
        except Exception as e:
            logger.error("Erreur chargement plugin %s: %s", name, e)
            return False

    def load_all(self):
        """Charge tous les plugins activés."""
        loaded = 0
        for name, info in self.plugins.items():
            if info.enabled and self.load(name):
                loaded += 1
        logger.info("Plugins chargés: %d/%d", loaded, len(self.plugins))
        return loaded

    def get_active(self) -> list[PluginInfo]:
        """Retourne les plugins activés et chargés."""
        return [p for p in self.plugins.values() if p.enabled and p.instance]

    def get_by_type(self, plugin_type: str) -> list[PluginInfo]:
        """Retourne les plugins actifs d'un type donné."""
        return [
            p for p in self.get_active()
            if p.plugin_type == plugin_type
        ]

    def execute(self, name: str, *args, **kwargs):
        """Exécute la méthode execute() d'un plugin."""
        if name not in self.plugins:
            return f"[Erreur] Plugin inconnu: {name}"

        info = self.plugins[name]
        if not info.instance:
            return f"[Erreur] Plugin non chargé: {name}"

        try:
            if hasattr(info.instance, "execute"):
                return info.instance.execute(*args, **kwargs)
            else:
                return f"[Erreur] Plugin {name}: méthode 'execute' manquante"
        except Exception as e:
            logger.error("Erreur exécution plugin %s: %s", name, e)
            return f"[Erreur] {e}"

    def get_plugin_tools(self) -> dict:
        """Collecte les outils exposés par tous les plugins tool."""
        tools = {}
        for info in self.get_by_type("tool"):
            if hasattr(info.instance, "get_tools"):
                plugin_tools = info.instance.get_tools()
                if isinstance(plugin_tools, dict):
                    tools.update(plugin_tools)
        return tools

    def get_plugin_context(self, query: str) -> str:
        """Collecte le contexte des plugins intelligence."""
        parts = []
        for info in self.get_by_type("intelligence"):
            if hasattr(info.instance, "get_context"):
                try:
                    ctx = info.instance.get_context(query)
                    if ctx:
                        parts.append(f"[{info.name}] {ctx}")
                except Exception as e:
                    logger.warning("Plugin context error (%s): %s", info.name, e)
        return "\n".join(parts) if parts else ""

    def enable(self, name: str) -> bool:
        """Active un plugin."""
        if name in self.plugins:
            self.plugins[name].enabled = True
            self._save_state(name)
            return True
        return False

    def disable(self, name: str) -> bool:
        """Désactive un plugin."""
        if name in self.plugins:
            self.plugins[name].enabled = False
            self.plugins[name].instance = None
            self._save_state(name)
            return True
        return False

    def _save_state(self, name: str):
        """Persiste l'état enabled/disabled dans plugin.json."""
        if name not in self.plugins:
            return
        info = self.plugins[name]
        meta_file = os.path.join(info.path, "plugin.json")
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["enabled"] = info.enabled
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning("Impossible de sauvegarder l'état du plugin %s: %s", name, e)

    def list_plugins(self) -> str:
        """Retourne un résumé textuel de tous les plugins."""
        if not self.plugins:
            return "Aucun plugin installé."

        lines = ["🔌 Plugins installés:"]
        for info in self.plugins.values():
            lines.append(f"  {info}")
        return "\n".join(lines)
