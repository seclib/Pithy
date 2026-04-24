"""
PIThy Infra Manager — Decision Engine
Moteur de décision : observe les métriques, décide des transitions et actions.
"""

import logging
from infra_manager.core.state_engine import State, StateEngine
from infra_manager.policies.thresholds import (
    CPU_LOW, CPU_IDLE,
    IDLE_TIMEOUT_LOW, IDLE_TIMEOUT_IDLE, IDLE_TIMEOUT_SLEEP,
    MIN_TRANSITION_INTERVAL,
)

logger = logging.getLogger(__name__)


class Decision:
    """Résultat d'une décision."""

    def __init__(self, action: str = "none", target_state: str = None,
                 services_start: list = None, services_stop: list = None,
                 reason: str = ""):
        self.action = action            # "none", "transition", "start", "stop"
        self.target_state = target_state
        self.services_start = services_start or []
        self.services_stop = services_stop or []
        self.reason = reason

    def __repr__(self):
        return f"Decision({self.action}, state={self.target_state}, reason={self.reason})"


# Services requis par mode
_MODE_SERVICES = {
    State.ACTIVE: ["chroma", "pithy"],
    State.LOW_USAGE: ["chroma"],
    State.IDLE: [],
    State.SLEEP: [],
}


class DecisionEngine:
    """Observe → Comprend → Décide."""

    def __init__(self, state_engine: StateEngine):
        self.state = state_engine

    def evaluate(self, sys_snapshot: dict, docker_snapshot: dict) -> Decision:
        """
        Évalue les métriques et décide de l'action à prendre.

        Args:
            sys_snapshot: snapshot du SystemMonitor
            docker_snapshot: snapshot du DockerMonitor
        """
        cpu = sys_snapshot.get("cpu_percent", 0)
        idle_s = self.state.idle_seconds
        current = self.state.current

        # --- Mode ACTIVE ---
        if current == State.ACTIVE:
            if idle_s > IDLE_TIMEOUT_LOW and cpu < CPU_LOW:
                return Decision(
                    action="transition",
                    target_state=State.LOW_USAGE,
                    services_stop=["pithy"],
                    reason=f"Inactif {int(idle_s)}s, CPU {cpu}%",
                )

        # --- Mode LOW_USAGE ---
        elif current == State.LOW_USAGE:
            if idle_s > IDLE_TIMEOUT_IDLE and cpu < CPU_IDLE:
                return Decision(
                    action="transition",
                    target_state=State.IDLE,
                    services_stop=["chroma"],
                    reason=f"Inactif {int(idle_s)}s, CPU {cpu}%",
                )

        # --- Mode IDLE ---
        elif current == State.IDLE:
            if idle_s > IDLE_TIMEOUT_SLEEP:
                return Decision(
                    action="transition",
                    target_state=State.SLEEP,
                    reason=f"Inactif {int(idle_s)}s → sleep",
                )

        # --- Mode SLEEP ---
        elif current == State.SLEEP:
            pass  # On ne fait rien, on attend une activation externe

        return Decision(action="none", reason="Aucun changement nécessaire")

    def on_activity(self) -> Decision:
        """Appelée quand une activité utilisateur est détectée."""
        self.state.record_activity()

        if self.state.current != State.ACTIVE:
            needed = _MODE_SERVICES[State.ACTIVE]
            return Decision(
                action="activate",
                target_state=State.ACTIVE,
                services_start=needed,
                reason=f"Activité détectée (depuis {self.state.current})",
            )

        return Decision(action="none", reason="Déjà en mode active")

    def get_required_services(self) -> list:
        """Retourne les services requis pour le mode actuel."""
        return _MODE_SERVICES.get(self.state.current, [])
