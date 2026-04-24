"""
PIThy Infra Manager — Hook System
Système de hooks pour l'extensibilité du gestionnaire d'infrastructure.

Hooks disponibles:
    on_start        → service démarré
    on_stop         → service arrêté
    on_idle         → système entre en mode idle
    on_predict      → prédiction de scaling calculée
    on_scale_up     → scaling up déclenché
    on_scale_down   → scaling down déclenché
    on_transition   → changement d'état du système
    on_error        → erreur détectée
"""

import logging

logger = logging.getLogger(__name__)

VALID_HOOKS = [
    "on_start",
    "on_stop",
    "on_idle",
    "on_predict",
    "on_scale_up",
    "on_scale_down",
    "on_transition",
    "on_error",
]


class HookRegistry:
    """Registre centralisé des hooks."""

    def __init__(self):
        self._hooks: dict[str, list[callable]] = {h: [] for h in VALID_HOOKS}

    def register(self, hook_name: str, callback: callable, plugin_name: str = ""):
        """Enregistre un callback pour un hook donné."""
        if hook_name not in VALID_HOOKS:
            logger.warning("Hook invalide: '%s' (plugin: %s)", hook_name, plugin_name)
            return False

        self._hooks[hook_name].append({
            "callback": callback,
            "plugin": plugin_name,
        })
        logger.debug("Hook enregistré: %s → %s", hook_name, plugin_name)
        return True

    def unregister(self, hook_name: str, plugin_name: str):
        """Désenregistre tous les callbacks d'un plugin pour un hook."""
        if hook_name not in self._hooks:
            return

        self._hooks[hook_name] = [
            h for h in self._hooks[hook_name]
            if h["plugin"] != plugin_name
        ]

    def unregister_all(self, plugin_name: str):
        """Désenregistre tous les hooks d'un plugin."""
        for hook_name in VALID_HOOKS:
            self.unregister(hook_name, plugin_name)

    def trigger(self, hook_name: str, **kwargs) -> list:
        """
        Déclenche un hook. Retourne les résultats de tous les callbacks.
        Les erreurs de plugins sont isolées (pas de crash global).
        """
        if hook_name not in self._hooks:
            return []

        results = []
        for entry in self._hooks[hook_name]:
            try:
                result = entry["callback"](**kwargs)
                results.append({
                    "plugin": entry["plugin"],
                    "result": result,
                    "error": None,
                })
            except Exception as e:
                logger.error(
                    "Hook error: %s → %s: %s",
                    hook_name, entry["plugin"], e,
                )
                results.append({
                    "plugin": entry["plugin"],
                    "result": None,
                    "error": str(e),
                })

        return results

    def list_hooks(self) -> dict[str, int]:
        """Retourne le nombre de callbacks par hook."""
        return {h: len(cbs) for h, cbs in self._hooks.items()}
