"""
PIThy Infra Manager — State Engine
Machine à états pour le mode opérationnel du système.

Modes:
    ACTIVE     → utilisateur actif, performance maximale
    LOW_USAGE  → activité sporadique, services réduits
    IDLE       → aucune activité, services non essentiels arrêtés
    SLEEP      → infrastructure minimale, zero waste
"""

import time
import logging

logger = logging.getLogger(__name__)


class State:
    ACTIVE = "active"
    LOW_USAGE = "low_usage"
    IDLE = "idle"
    SLEEP = "sleep"

    ALL = [ACTIVE, LOW_USAGE, IDLE, SLEEP]

    # Transitions valides (de → vers)
    TRANSITIONS = {
        ACTIVE: [LOW_USAGE],
        LOW_USAGE: [ACTIVE, IDLE],
        IDLE: [ACTIVE, LOW_USAGE, SLEEP],
        SLEEP: [ACTIVE],
    }


class StateEngine:
    """Machine à états pour le mode opérationnel global."""

    def __init__(self, initial: str = State.ACTIVE):
        self.current = initial
        self.previous = None
        self.last_transition = time.time()
        self.last_activity = time.time()
        self.transition_count = 0
        self._history: list[tuple[float, str, str]] = []

    @property
    def idle_seconds(self) -> float:
        """Secondes depuis la dernière activité."""
        return time.time() - self.last_activity

    @property
    def seconds_in_state(self) -> float:
        """Secondes dans l'état actuel."""
        return time.time() - self.last_transition

    def record_activity(self):
        """Enregistre une activité utilisateur."""
        self.last_activity = time.time()

    def can_transition(self, target: str) -> bool:
        """Vérifie si la transition est valide."""
        if target == self.current:
            return False
        if target not in State.ALL:
            return False
        return target in State.TRANSITIONS.get(self.current, [])

    def transition(self, target: str, min_interval: float = 60) -> bool:
        """
        Effectue une transition d'état.
        Retourne True si la transition a eu lieu.
        """
        if not self.can_transition(target):
            return False

        # Anti-flapping
        elapsed = time.time() - self.last_transition
        if elapsed < min_interval:
            logger.debug(
                "Transition %s→%s bloquée (anti-flap: %ds restants)",
                self.current, target, int(min_interval - elapsed),
            )
            return False

        self.previous = self.current
        self.current = target
        self.last_transition = time.time()
        self.transition_count += 1
        self._history.append((time.time(), self.previous, self.current))

        # Garder l'historique limité
        if len(self._history) > 100:
            self._history = self._history[-50:]

        logger.info(
            "🔄 Transition: %s → %s (après %ds)",
            self.previous, self.current, int(elapsed),
        )
        return True

    def force_active(self):
        """Force le passage en mode ACTIVE (activité détectée)."""
        self.record_activity()
        if self.current != State.ACTIVE:
            # Transition directe vers ACTIVE depuis n'importe quel état
            self.previous = self.current
            self.current = State.ACTIVE
            self.last_transition = time.time()
            self.transition_count += 1
            self._history.append((time.time(), self.previous, self.current))
            logger.info("⚡ Force ACTIVE (depuis %s)", self.previous)

    def summary(self) -> dict:
        """Retourne un résumé de l'état actuel."""
        return {
            "current": self.current,
            "previous": self.previous,
            "idle_seconds": round(self.idle_seconds),
            "seconds_in_state": round(self.seconds_in_state),
            "transition_count": self.transition_count,
        }
