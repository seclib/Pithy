"""
PIThy - Brain (cerveau de l'agent)
Construction de prompts enrichis et logique RAG.
"""

import logging
from config import RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP

logger = logging.getLogger(__name__)

# Prompts système par mode
_SYSTEM_PROMPTS = {
    "chat": (
        "Tu es PIThy, un assistant IA local intelligent et utile. "
        "Réponds de manière claire, concise et pertinente."
    ),
    "code": (
        "Tu es un assistant expert en programmation. "
        "Fournis du code clair, fonctionnel et bien commenté avec des explications."
    ),
    "system": (
        "Tu es un assistant système Linux. "
        "Aide l'utilisateur avec des commandes et opérations système. "
        "Propose des commandes précises et sûres."
    ),
    "memory": (
        "Tu es PIThy, un assistant avec mémoire persistante. "
        "Utilise le contexte fourni pour répondre avec précision."
    ),
    "reasoning": (
        "Tu es un assistant spécialisé en analyse et raisonnement logique. "
        "Décompose les problèmes, évalue les options et fournis des conclusions argumentées."
    ),
    "light": (
        "Tu es PIThy. Réponds de manière très concise et directe. "
        "Va droit au but en une ou deux phrases maximum."
    ),
}


class Brain:
    """Logique de traitement des requêtes avec construction de prompts et RAG."""

    def __init__(self, vector_store=None):
        self.vector_store = vector_store
        if vector_store:
            logger.info("Brain initialisé avec RAG")
        else:
            logger.warning("Brain initialisé sans RAG")

    def build_prompt(self, query: str, context: str = None, mode: str = "chat",
                     tool_output: str = None, plugin_context: str = None) -> str:
        """Construit un prompt optimisé pour le LLM."""
        system = _SYSTEM_PROMPTS.get(mode, _SYSTEM_PROMPTS["chat"])
        prompt = f"{system}\n\n"

        if context:
            prompt += f"Contexte mémoire pertinent:\n{context}\n\n"

        if plugin_context:
            prompt += f"Contexte plugins:\n{plugin_context}\n\n"

        if tool_output:
            prompt += f"Résultat d'opération système:\n{tool_output}\n\n"

        prompt += f"Utilisateur: {query}\n\nRéponse:"
        return prompt

    def get_context(self, query: str) -> str | None:
        """Récupère le contexte pertinent via RAG."""
        if not self.vector_store:
            return None

        try:
            context = self.vector_store.get_context(query, max_tokens=1000)
            return context if context else None
        except Exception as e:
            logger.error("Erreur RAG get_context: %s", e)
            return None

    def remember(self, content: str, metadata: dict = None) -> bool:
        """Ajoute du contenu à la mémoire vectorielle."""
        if not self.vector_store:
            return False

        try:
            chunks = self._chunk_text(content)
            metas = [metadata or {}] * len(chunks)
            self.vector_store.add_texts(chunks, metadatas=metas)
            logger.info("Mémorisé: %d chunks", len(chunks))
            return True
        except Exception as e:
            logger.error("Erreur mémorisation: %s", e)
            return False

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list:
        """Découpe un texte en chunks chevauchants."""
        chunk_size = chunk_size or RAG_CHUNK_SIZE
        overlap = overlap or RAG_CHUNK_OVERLAP
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - overlap

        return chunks if chunks else [text]
