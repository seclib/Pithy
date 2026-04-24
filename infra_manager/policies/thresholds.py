"""
PIThy Infra Manager — Seuils de décision
Constantes et seuils pour le moteur de décision.
"""

# =========================
# CPU Thresholds (%)
# =========================

CPU_HIGH = 80.0          # Charge élevée
CPU_MEDIUM = 40.0        # Charge modérée
CPU_LOW = 20.0           # Charge faible
CPU_IDLE = 5.0           # Pratiquement inactif

# =========================
# Memory Thresholds (%)
# =========================

MEM_HIGH = 85.0          # Mémoire critique
MEM_MEDIUM = 60.0        # Mémoire modérée
MEM_LOW = 30.0           # Mémoire faible

# =========================
# Timing (secondes)
# =========================

IDLE_TIMEOUT_LOW = 300       # 5 min → passage en low_usage
IDLE_TIMEOUT_IDLE = 600      # 10 min → passage en idle
IDLE_TIMEOUT_SLEEP = 1800    # 30 min → passage en sleep

# Intervalle de vérification du scheduler
CHECK_INTERVAL = 30          # Vérifie l'état toutes les 30s

# Anti-flapping: temps minimum entre transitions
MIN_TRANSITION_INTERVAL = 60  # 1 minute

# =========================
# Protection
# =========================

MAX_RESTARTS_PER_HOUR = 10
COOLDOWN_AFTER_ERROR = 60    # secondes
