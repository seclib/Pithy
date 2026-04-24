import logging
import time
from core.agent import Agent
from infra_manager.core.manager import InfraManager
from core.unified_plugins import UnifiedPluginLoader

logger = logging.getLogger(__name__)

class PithyOS:
    """
    PIThy AI Automation Platform Core.
    Système unifié intégrant l'Agent Layer, l'Infra Layer et l'Extension Layer.
    """

    def __init__(self, compose_dir: str = "."):
        # 1. INFRA LAYER
        self.infra = InfraManager(compose_dir=compose_dir, auto_start=True)
        
        # 2. AGENT LAYER
        self.agent = Agent(infra_manager=self.infra)
        
        # 3. EXTENSION LAYER (Unified Plugins)
        self.plugins = UnifiedPluginLoader(self)
        self.plugins.load_all()
        
        # Pont de notification interne
        self._setup_notification_bridge()
        
        logger.info("💎 PIThy AI Automation Platform Core initialisé")

    def _setup_notification_bridge(self):
        """Configure les notifications de l'infrastructure vers la mémoire de l'agent."""
        
        def on_infra_transition(from_state, to_state):
            msg = f"Système : Transition d'état de l'infrastructure : {from_state} -> {to_state}"
            logger.info(f"🔔 Notification Infra: {msg}")
            # L'agent enregistre ce changement dans sa mémoire contextuelle
            if self.agent.memory:
                self.agent.memory.add(msg, doc_id=f"sys_transition_{int(time.time())}")

        # Enregistrement via le registre de hooks de l'infra
        self.infra.scaler.plugin_manager.hooks.register(
            "on_transition", on_infra_transition, "pithy_os_bridge"
        )

    def run(self, query: str, strategy: str = "single") -> str:
        """
        Implémentation de la boucle intelligente unifiée.
        """
        # --- 1. OBSERVER ---
        self.infra.notify_activity()
        self.infra.scaler.predictor.tracker.record("cli", query)
        sys_snap = self.infra.scaler.sys_monitor.snapshot()
        
        # --- 2. COMPRENDRE ---
        # Le router sémantique analyse l'intention
        mode = self.agent.router.route(query)
        logger.info(f"Loop: Intention comprise -> {mode}")

        # --- 3. DÉCIDER ---
        # L'infra décide du scaling (déjà géré par l'AutoScaler en parallèle)
        # L'agent prépare le prompt enrichi (RAG + Context)
        context = self.agent.brain.get_context(query)
        if context:
            self.infra.scaler.predictor.tracker.record("rag", "context_retrieved")
        
        # Injection de l'état système dans le contexte de compréhension
        system_context = f"État système actuel : {self.infra.mode} (CPU: {sys_snap['cpu_percent']}%)"
        
        # --- 4. AGIR ---
        # Exécution de la logique agent
        response = self.agent.run(query, strategy=strategy)

        # --- 5. OPTIMISER ---
        # Mise à jour de l'historique pour l'apprentissage prédictif
        self.infra.scaler.predictor.tracker.record("llm", f"mode:{mode}")
        
        return response

    def get_system_status(self) -> str:
        """Retourne l'état complet du système fusionné."""
        return self.infra.status() + "\n" + self._get_agent_info()

    def _get_agent_info(self) -> str:
        agent_info = "\n🤖 AGENT LAYER STATUS:\n"
        agent_info += f"   Routing: {self.agent.router.use_llm and 'Sémantique' or 'Keywords'}\n"
        agent_info += f"   Mémoire: {self.agent.memory and self.agent.memory.count() or 0} documents\n"
        agent_info += f"   Plugins: {len(self.agent.plugins.get_active())} actifs\n"
        return agent_info

    def shutdown(self):
        """Arrêt sécurisé de la couche opératoire."""
        logger.info("🛑 Arrêt de PIThy OS...")
        self.infra.stop()
