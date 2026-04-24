"""
PIThy Infra Manager — Activity Tracker
Enregistre l'historique des requêtes et des usages pour le moteur prédictif.
"""

import time
import json
import os
import logging
from collections import deque

logger = logging.getLogger(__name__)

_HISTORY_FILE = "./data/logs/activity_history.json"
_MAX_EVENTS = 5000


class ActivityEvent:
    """Un événement d'activité horodaté."""

    def __init__(self, event_type: str, details: str = "",
                 timestamp: float = None):
        self.event_type = event_type  # "llm", "rag", "shell", "plugin", "cli"
        self.details = details
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> dict:
        return {
            "type": self.event_type,
            "details": self.details,
            "ts": self.timestamp,
            "hour": time.localtime(self.timestamp).tm_hour,
            "weekday": time.localtime(self.timestamp).tm_wday,
        }


class ActivityTracker:
    """Enregistre et analyse l'historique des activités et des ressources."""

    def __init__(self, history_file: str = None):
        self._file = history_file or _HISTORY_FILE
        self._events: deque[dict] = deque(maxlen=_MAX_EVENTS)
        self._resource_history: deque[dict] = deque(maxlen=100) # Historique court pour trends
        self._load()

    def _load(self):
        """Charge l'historique depuis le fichier."""
        try:
            if os.path.isfile(self._file):
                with open(self._file, "r") as f:
                    data = json.load(f)
                for ev in data[-_MAX_EVENTS:]:
                    self._events.append(ev)
                logger.info("Historique chargé: %d événements", len(self._events))
        except Exception as e:
            logger.warning("Impossible de charger l'historique: %s", e)

    def _save(self):
        """Persiste l'historique sur disque."""
        try:
            os.makedirs(os.path.dirname(self._file), exist_ok=True)
            with open(self._file, "w") as f:
                json.dump(list(self._events), f)
        except Exception as e:
            logger.warning("Impossible de sauvegarder l'historique: %s", e)

    def record(self, event_type: str, details: str = ""):
        """Enregistre un nouvel événement d'activité."""
        ev = ActivityEvent(event_type, details)
        self._events.append(ev.to_dict())

        # Sauvegarder périodiquement
        if len(self._events) % 50 == 0:
            self._save()

    def record_resources(self, cpu: float, ram_pct: float):
        """Enregistre l'usage des ressources pour analyse de trend."""
        self._resource_history.append({
            "ts": time.time(),
            "cpu": cpu,
            "ram": ram_pct
        })

    def get_resource_trend(self, window_size: int = 5) -> dict:
        """Calcule la tendance (pente) des ressources sur les N derniers relevés."""
        if len(self._resource_history) < window_size:
            return {"cpu_trend": 0.0, "ram_trend": 0.0}
        
        recent = list(self._resource_history)[-window_size:]
        cpu_delta = recent[-1]["cpu"] - recent[0]["cpu"]
        ram_delta = recent[-1]["ram"] - recent[0]["ram"]
        
        return {
            "cpu_trend": cpu_delta / window_size,
            "ram_trend": ram_delta / window_size
        }

    def get_action_sequence(self, length: int = 3) -> list[str]:
        """Retourne les types des N dernières actions."""
        # Filtrer pour ne garder que les actions utilisateur (cli, shell, etc.)
        actions = [e["type"] for e in self._events if e["type"] in ("cli", "shell", "rag", "llm")]
        return actions[-length:]

    def flush(self):
        """Force la sauvegarde."""
        self._save()

    def get_recent(self, seconds: int = 3600) -> list[dict]:
        """Retourne les événements des N dernières secondes."""
        cutoff = time.time() - seconds
        return [e for e in self._events if e.get("ts", 0) > cutoff]

    def get_hourly_distribution(self) -> dict[int, int]:
        """Distribution des événements par heure de la journée."""
        dist = {h: 0 for h in range(24)}
        for ev in self._events:
            h = ev.get("hour", 0)
            dist[h] = dist.get(h, 0) + 1
        return dist

    def get_type_frequency(self, seconds: int = 3600) -> dict[str, int]:
        """Fréquence des types d'événements récents."""
        recent = self.get_recent(seconds)
        freq = {}
        for ev in recent:
            t = ev.get("type", "unknown")
            freq[t] = freq.get(t, 0) + 1
        return freq

    def get_avg_interval(self, event_type: str = None,
                         last_n: int = 20) -> float:
        """Intervalle moyen entre événements (en secondes)."""
        events = list(self._events)
        if event_type:
            events = [e for e in events if e.get("type") == event_type]

        events = events[-last_n:]
        if len(events) < 2:
            return 0.0

        intervals = []
        for i in range(1, len(events)):
            delta = events[i].get("ts", 0) - events[i - 1].get("ts", 0)
            if delta > 0:
                intervals.append(delta)

        return sum(intervals) / len(intervals) if intervals else 0.0

    @property
    def total_events(self) -> int:
        return len(self._events)
