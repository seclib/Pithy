"""
PIThy Infra Manager — Predictive Scaling Engine
Prédit la charge future et anticipe le démarrage/arrêt des services.

Modes de scaling:
    HOT  → services actifs + prêts
    WARM → services en standby (chargés mais idle)
    COLD → services arrêtés
    SLEEP → infrastructure minimale
"""

import time
import logging
from infra_manager.predictor.activity_tracker import ActivityTracker

logger = logging.getLogger(__name__)


class ScalingMode:
    HOT = "hot"     # Services actifs et prêts
    WARM = "warm"   # Services en veille active (standby)
    COLD = "cold"   # Services arrêtés
    IDLE = "idle"   # Infrastructure minimale


class Prediction:
    """Résultat d'une prédiction de charge."""

    def __init__(self, likely_active: bool, confidence: float,
                 recommended_mode: str, reason: str,
                 services_prestart: list = None):
        self.likely_active = likely_active
        self.confidence = confidence         # 0.0 à 1.0
        self.recommended_mode = recommended_mode
        self.reason = reason
        self.services_prestart = services_prestart or []

    def __repr__(self):
        return (
            f"Prediction(mode={self.recommended_mode.upper()}, "
            f"conf={self.confidence:.0%}, reason={self.reason})"
        )


class PredictiveScaler:
    """
    Moteur de scaling prédictif optimisé.
    Analyse l'historique, les tendances de ressources et les séquences d'actions.
    """

    def __init__(self, tracker: ActivityTracker = None):
        self.tracker = tracker or ActivityTracker()

    def predict(self) -> Prediction:
        """
        Analyse globale pour prédire l'usage futur.
        """
        now = time.time()
        current_hour = time.localtime(now).tm_hour

        # 1. Activité récente
        recent_5min = self.tracker.get_recent(300)
        recent_count = len(recent_5min)

        # 2. Tendances ressources
        trends = self.tracker.get_resource_trend(window_size=10)
        cpu_trend = trends["cpu_trend"]

        # 3. Séquences d'actions
        sequence = self.tracker.get_action_sequence(length=3)
        
        # 4. Pattern horaire
        hourly_dist = self.tracker.get_hourly_distribution()
        max_h = max(hourly_dist.values()) if hourly_dist.values() else 1
        hour_score = hourly_dist.get(current_hour, 0) / max(max_h, 1)

        # 5. Intervalle moyen
        avg_interval = self.tracker.get_avg_interval(last_n=15)

        # --- Algorithme de décision ---
        score = 0.0
        reasons = []

        # Activité immédiate
        if recent_count > 0:
            score += 0.35
            reasons.append(f"Activité récente ({recent_count} ev)")

        # Tendance CPU positive (anticipation de charge)
        if cpu_trend > 0.5:
            score += 0.2
            reasons.append(f"Hausse CPU (trend={cpu_trend:.2f})")

        # Analyse de séquence (Heuristique: RAG -> LLM est fréquent)
        if len(sequence) >= 2 and sequence[-1] == "rag":
            score += 0.25
            reasons.append("Séquence détectée: RAG (anticipation LLM)")
        
        if "cli" in sequence or "shell" in sequence:
            score += 0.15
            reasons.append("Interaction CLI/Shell en cours")

        # Pattern horaire
        if hour_score > 0.6:
            score += 0.15
            reasons.append(f"Pattern horaire favorable ({current_hour}h)")

        # Intervalle (si très court, haute probabilité de continuation)
        if 0 < avg_interval < 30:
            score += 0.1
            reasons.append("Rafale de requêtes détectée")

        # Clamp
        confidence = min(1.0, score)

        # --- Détermination du mode ---
        if confidence > 0.75:
            mode = ScalingMode.HOT
            services = ["chroma", "pithy"]
        elif confidence > 0.45:
            mode = ScalingMode.WARM
            services = ["chroma"]
        elif confidence > 0.2:
            mode = ScalingMode.COLD
            services = []
        else:
            mode = ScalingMode.IDLE
            services = []

        return Prediction(
            likely_active=confidence > 0.5,
            confidence=confidence,
            recommended_mode=mode,
            reason=", ".join(reasons) if reasons else "Calme plat",
            services_prestart=services
        )
