"""
PIThy - Agent principal
Orchestrateur central : routing sémantique → RAG → plugins → tools → multi-modèle → mémoire.
"""

import logging
from llm.ollama_client import OllamaClient
from core.router import Router
from core.brain import Brain
from core.orchestrator import Orchestrator
from memory.vector_store import VectorStore
from tools.shell import ShellTool
from tools.filesystem import FilesystemTool
from tools.resource_manager import ResourceManagerTool
from tools.log_analyzer import LogAnalyzerTool
from plugins.loader import PluginLoader
from config import DEFAULT_MODEL, CODE_MODEL, SAFE_MODE

# Mapping mode → rôle orchestrateur
_MODE_TO_ROLE = {
    "chat": "chat",
    "code": "code",
    "system": "chat",
    "memory": "chat",
    "reasoning": "reasoning",
    "light": "light",
}

logger = logging.getLogger(__name__)


class Agent:
    """Agent IA local avec routing sémantique, RAG, multi-modèle, plugins et outils système."""

    def __init__(self, infra_manager=None):
        self.infra = infra_manager
        
        # Router sémantique
        self.router = Router(use_llm=True)

        # Orchestrateur multi-modèle
        self.orchestrator = Orchestrator()

        # LLMs directs (pour accès rapide)
        self.chat_llm = OllamaClient(DEFAULT_MODEL)
        self.code_llm = OllamaClient(CODE_MODEL)

        # Mémoire / RAG
        try:
            self.memory = VectorStore()
            logger.info("RAG (ChromaDB) initialisé")
        except Exception as e:
            logger.warning("RAG non disponible: %s", e)
            self.memory = None

        # Brain
        self.brain = Brain(vector_store=self.memory)

        # Tools
        self.shell = ShellTool(safe_mode=SAFE_MODE)
        self.filesystem = FilesystemTool(safe_mode=SAFE_MODE)
        self.logs = LogAnalyzerTool()
        
        # Outil de gestion des ressources (si infra dispo)
        self.resource_manager = None
        if self.infra:
            self.resource_manager = ResourceManagerTool(self.infra)

        # Plugins
        self.plugins = PluginLoader()
        self.plugins.load_all()

    # ------------------------------------------------------------------
    # Pipeline principal
    # ------------------------------------------------------------------

    def run(self, query: str, strategy: str = "single") -> str:
        """
        Pipeline complet :
            1. Route la requête (sémantique + fallback keywords)
            2. Récupère le contexte RAG
            3. Collecte le contexte plugins
            4. Exécute les tools si nécessaire
            5. Construit le prompt enrichi via Brain
            6. Génère la réponse via orchestrateur multi-modèle
            7. Stocke en mémoire
        """
        try:
            # 1. Routing sémantique
            mode = self.router.route(query)
            logger.info("Mode détecté: %s", mode)

            # 2. Contexte RAG
            context = self.brain.get_context(query)

            # 3. Contexte plugins (intelligence plugins)
            plugin_context = self.plugins.get_plugin_context(query)

            # 4. Actions système si mode = system
            tool_output = None
            if mode == "system":
                tool_output = self._handle_system_query(query)

            # 5. Construction du prompt
            prompt = self.brain.build_prompt(
                query,
                context=context,
                mode=mode,
                tool_output=tool_output,
                plugin_context=plugin_context or None,
            )

            # 6. Génération multi-modèle
            role = _MODE_TO_ROLE.get(mode, "chat")
            response = self.orchestrator.run(prompt, strategy=strategy, role=role)

            # 7. Stockage mémoire
            if self.memory:
                try:
                    self.memory.add(
                        f"Q: {query}\nR: {response}",
                        doc_id=str(abs(hash(query))),
                    )
                except Exception as e:
                    logger.warning("Stockage mémoire échoué: %s", e)

            return response

        except Exception as e:
            logger.error("Erreur agent.run: %s", e)
            return f"[Erreur] Une erreur est survenue: {e}"

    # ------------------------------------------------------------------
    # Gestion des requêtes système
    # ------------------------------------------------------------------

    def _handle_system_query(self, query: str) -> str | None:
        """Détecte et exécute les opérations système demandées."""
        q = query.lower()

        # Détection de commandes shell explicites
        shell_prefixes = ["exécute ", "execute ", "lance ", "run ", "commande "]
        for prefix in shell_prefixes:
            if prefix in q:
                idx = q.index(prefix) + len(prefix)
                cmd = query[idx:].strip().strip("`'\"")
                if cmd:
                    result = self.shell.run(cmd)
                    if result["status"] == "ok":
                        output = result["stdout"] or result["stderr"] or "(pas de sortie)"
                        return f"$ {cmd}\n{output}"
                    else:
                        return f"$ {cmd}\n❌ {result['status']}: {result['stderr']}"

        # Détection listing de répertoire
        if any(kw in q for kw in ["liste", "list", "ls ", "dossier", "répertoire"]):
            return f"Contenu du répertoire:\n{self.filesystem.list_directory('.')}"

        return None

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def remember(self, content: str) -> str:
        """Mémorise du contenu explicitement."""
        if self.brain.remember(content):
            return "✅ Contenu mémorisé"
        return "❌ Impossible de mémoriser (RAG non disponible)"

    def recall(self, query: str) -> str:
        """Recherche dans la mémoire."""
        if not self.memory:
            return "❌ RAG non disponible"

        docs = self.memory.search(query, k=5)
        if not docs:
            return "Aucun souvenir trouvé pour cette requête."

        result = "🧠 Souvenirs trouvés:\n"
        for i, doc in enumerate(docs, 1):
            result += f"\n--- [{i}] ---\n{doc}\n"
        return result

    def run_plugin(self, plugin_name: str, command: str = None) -> str:
        """Exécute un plugin par nom."""
        return self.plugins.execute(plugin_name, command or "")

    def list_plugins(self) -> str:
        """Liste les plugins installés."""
        return self.plugins.list_plugins()
