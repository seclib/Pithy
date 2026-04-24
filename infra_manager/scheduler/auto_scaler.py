"""
PIThy Infra Manager — Auto Scaler
Boucle principale du scheduler : observe, décide, agit.
"""

import time
import logging
import threading
from infra_manager.core.state_engine import StateEngine
from infra_manager.core.decision_engine import DecisionEngine
from infra_manager.monitor.system_monitor import SystemMonitor
from infra_manager.monitor.docker_monitor import DockerMonitor
from infra_manager.controller.docker_controller import DockerController
from infra_manager.controller.service_controller import ServiceController
from infra_manager.scheduler.idle_detector import IdleDetector
from infra_manager.predictor.scaling_engine import PredictiveScaler
from infra_manager.plugins.plugin_manager import InfraPluginManager
from infra_manager.policies.thresholds import CHECK_INTERVAL, MIN_TRANSITION_INTERVAL

logger = logging.getLogger(__name__)


class AutoScaler:
    """
    Boucle autonome d'observation → décision → action.
    Tourne en arrière-plan et gère les transitions d'état et le scaling prédictif.
    """

    def __init__(self, compose_dir: str = ".",
                 ollama_url: str = "http://localhost:11434",
                 chroma_url: str = "http://localhost:8000"):
        # Composants
        self.state_engine = StateEngine()
        self.decision_engine = DecisionEngine(self.state_engine)
        self.sys_monitor = SystemMonitor()
        self.docker_monitor = DockerMonitor()
        self.docker_controller = DockerController(compose_dir)
        self.service_controller = ServiceController(self.docker_controller)
        self.idle_detector = IdleDetector(ollama_url, chroma_url)
        
        # Extensions
        self.predictor = PredictiveScaler()
        self.plugin_manager = InfraPluginManager()
        self.plugin_manager.load_all()

        # Contrôle de la boucle
        self._running = False
        self._thread = None
        self._check_interval = CHECK_INTERVAL

    # ------------------------------------------------------------------
    # Boucle principale
    # ------------------------------------------------------------------

    def start(self):
        """Démarre le scheduler en arrière-plan."""
        if self._running:
            logger.warning("AutoScaler déjà en cours")
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("🚀 AutoScaler démarré (intervalle: %ds)", self._check_interval)

    def stop(self):
        """Arrête le scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("🛑 AutoScaler arrêté")

    def _loop(self):
        """Boucle principale observe → décide → agit."""
        while self._running:
            try:
                self._tick()
            except Exception as e:
                logger.error("AutoScaler tick error: %s", e)

            time.sleep(self._check_interval)

    def _tick(self):
        """Un cycle du scheduler."""
        # 1. Observer
        sys_snap = self.sys_monitor.snapshot()
        docker_snap = self.docker_monitor.snapshot()

        # Enregistrer les ressources pour l'analyse de tendance
        self.predictor.tracker.record_resources(
            cpu=sys_snap["cpu_percent"],
            ram_pct=sys_snap["memory"]["percent"]
        )

        # 2. Prédire (Predictive Scaling)
        prediction = self.predictor.predict()
        self.plugin_manager.trigger_hook("on_predict", prediction=prediction)
        
        # 2b. Hook on_tick pour monitoring continu
        self.plugin_manager.trigger_hook("on_tick", sys_snap=sys_snap, docker_snap=docker_snap)

        # Anticiper le démarrage des services si confiance élevée
        if prediction.likely_active:
            for svc in prediction.services_prestart:
                if not self.docker_monitor.is_container_running(f"pithy_{svc}"):
                    logger.info("🔮 Anticipation: démarrage de %s (%s)", svc, prediction.reason)
                    self.service_controller.start_with_deps(svc)
                    self.plugin_manager.trigger_hook("on_scale_up", service=svc, reason=prediction.reason)

        # 3. Décider (Logic réactive)
        decision = self.decision_engine.evaluate(sys_snap, docker_snap)

        if decision.action == "none":
            # Déclencher on_idle si on est déjà en mode éco
            if self.state_engine.current in ("idle", "sleep"):
                self.plugin_manager.trigger_hook("on_idle", idle_seconds=self.state_engine.idle_seconds)
            
            # Si aucune action réactive, on peut quand même appliquer le scaling prédictif
            # si le moteur recommande un mode plus léger (scale down)
            if prediction.recommended_mode in ("cold", "sleep") and self.state_engine.current == "active":
                 logger.info("🔮 Anticipation: passage en mode léger (%s)", prediction.reason)
                 # On laisse le DecisionEngine gérer la transition au tick suivant ou on force ici ?
                 # Pour la sécurité, on suit principalement le DecisionEngine réactif.
            return

        logger.info("📋 Décision: %s", decision)

        # 4. Agir
        self._execute(decision)

    def _execute(self, decision):
        """Exécute une décision."""
        # Transitions d'état
        if decision.action in ("transition", "activate"):
            if decision.target_state:
                old_state = self.state_engine.current
                if decision.action == "activate":
                    self.state_engine.force_active()
                else:
                    self.state_engine.transition(
                        decision.target_state,
                        min_interval=MIN_TRANSITION_INTERVAL,
                    )
                
                new_state = self.state_engine.current
                if old_state != new_state:
                    self.plugin_manager.trigger_hook("on_transition", from_state=old_state, to_state=new_state)

        # Démarrer des services
        for svc in decision.services_start:
            if self.service_controller.start_with_deps(svc):
                self.plugin_manager.trigger_hook("on_start", service=svc)

        # Arrêter des services
        for svc in decision.services_stop:
            if self.service_controller.stop_safe(svc):
                self.plugin_manager.trigger_hook("on_stop", service=svc)
                self.plugin_manager.trigger_hook("on_scale_down", service=svc, reason=decision.reason)

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def notify_activity(self):
        """Notifie le scheduler qu'une activité a été détectée."""
        decision = self.decision_engine.on_activity()
        if decision.action != "none":
            logger.info("⚡ Activité détectée: %s", decision.reason)
            self._execute(decision)

    def get_status(self) -> dict:
        """Retourne le status complet du système."""
        return {
            "state": self.state_engine.summary(),
            "system": self.sys_monitor.snapshot(),
            "docker": self.docker_monitor.snapshot(),
            "idle": self.idle_detector.snapshot(),
            "running": self._running,
        }

    @property
    def current_mode(self) -> str:
        """Mode opérationnel actuel."""
        return self.state_engine.current
