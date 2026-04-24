"""
PIThy - Orchestrateur multi-modèle
Permet d'appeler plusieurs modèles et de fusionner/comparer les résultats.
"""

import logging
from llm.ollama_client import OllamaClient
from config import MODEL_REGISTRY

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestre plusieurs modèles LLM pour une seule requête.

    Stratégies :
        - single   : un seul modèle (par défaut)
        - compare  : deux modèles, le meilleur est choisi
        - pipeline : A génère → B critique → C résume
    """

    def __init__(self):
        self._clients = {}

    def _get_client(self, role: str) -> OllamaClient:
        """Retourne un client Ollama pour le rôle donné (cache les instances)."""
        if role not in self._clients:
            model = MODEL_REGISTRY.get(role, MODEL_REGISTRY["chat"])
            self._clients[role] = OllamaClient(model)
        return self._clients[role]

    # ------------------------------------------------------------------
    # Stratégie : single
    # ------------------------------------------------------------------

    def single(self, prompt: str, role: str = "chat") -> str:
        """Génération simple avec un seul modèle."""
        client = self._get_client(role)
        return client.generate(prompt)

    # ------------------------------------------------------------------
    # Stratégie : compare
    # ------------------------------------------------------------------

    def compare(self, prompt: str, roles: list = None) -> dict:
        """
        Génère avec plusieurs modèles et retourne toutes les réponses.

        Retourne: {"role": "response", ...}
        """
        roles = roles or ["chat", "reasoning"]
        results = {}

        for role in roles:
            client = self._get_client(role)
            logger.info("Orchestrator compare: génération avec '%s'", role)
            results[role] = client.generate(prompt)

        return results

    # ------------------------------------------------------------------
    # Stratégie : pipeline (generate → critique → summarize)
    # ------------------------------------------------------------------

    def pipeline(self, query: str) -> str:
        """
        Pipeline multi-modèle :
            1. Modèle A génère une réponse
            2. Modèle B critique la réponse
            3. Modèle C produit la synthèse finale
        """
        # Étape 1 : Génération
        gen_client = self._get_client("chat")
        logger.info("Pipeline étape 1: génération")
        draft = gen_client.generate(
            f"Réponds à cette question de manière complète:\n{query}"
        )

        if draft.startswith("[Erreur]"):
            return draft

        # Étape 2 : Critique
        critic_client = self._get_client("reasoning")
        logger.info("Pipeline étape 2: critique")
        critique = critic_client.generate(
            f"Analyse critique de cette réponse. Identifie les erreurs, "
            f"imprécisions ou améliorations possibles:\n\n"
            f"Question: {query}\n\n"
            f"Réponse à évaluer:\n{draft}"
        )

        if critique.startswith("[Erreur]"):
            # Si la critique échoue, on retourne le draft
            return draft

        # Étape 3 : Synthèse finale
        synth_client = self._get_client("light")
        logger.info("Pipeline étape 3: synthèse")
        final = synth_client.generate(
            f"Produis une réponse finale optimale en tenant compte "
            f"de la réponse initiale et de sa critique:\n\n"
            f"Question: {query}\n\n"
            f"Réponse initiale:\n{draft}\n\n"
            f"Critique:\n{critique}\n\n"
            f"Réponse finale améliorée:"
        )

        return final if not final.startswith("[Erreur]") else draft

    # ------------------------------------------------------------------
    # Choix automatique de stratégie
    # ------------------------------------------------------------------

    def run(self, prompt: str, strategy: str = "single", role: str = "chat") -> str:
        """Point d'entrée principal — sélectionne la stratégie."""
        if strategy == "compare":
            results = self.compare(prompt)
            # Retourne la plus longue réponse (heuristique simple)
            best_role = max(results, key=lambda r: len(results[r]))
            return results[best_role]
        elif strategy == "pipeline":
            return self.pipeline(prompt)
        else:
            return self.single(prompt, role=role)
