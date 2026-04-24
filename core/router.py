"""
PIThy - Router intelligent avec analyse sémantique
Détermine l'intention via le LLM au lieu de simples mots-clés.

Modes:
    - chat      : conversation simple
    - code      : programmation / debug
    - system    : actions système (shell / filesystem)
    - memory    : stockage / rappel mémoire explicite
    - reasoning : analyse complexe / logique
    - light     : résumé rapide / question simple
"""

import logging
import requests
from config import OLLAMA_URL, LIGHT_MODEL

logger = logging.getLogger(__name__)

# Classification rapide par mots-clés (fallback si LLM indisponible)
_KEYWORD_MAP = {
    "code": [
        "code", "script", "bug", "error", "debug", "python", "javascript",
        "function", "class", "compile", "syntaxe", "programme", "algorithm",
        "api", "html", "css", "sql", "json", "regex", "exception",
        "traceback", "import", "module", "framework", "développe", "implement",
        "refactor",
    ],
    "system": [
        "exécute", "execute", "lance", "run", "commande", "command",
        "terminal", "shell", "bash", "système", "system", "fichier", "file",
        "dossier", "directory", "ls", "cat", "grep", "find", "mkdir",
        "chmod", "ps", "top", "df", "du", "apt", "pip", "docker", "git",
        "curl", "wget", "install", "disque", "cpu", "ram", "réseau",
        "network", "port", "service",
    ],
    "memory": [
        "souviens", "remember", "mémorise", "memorize", "retiens",
        "rappelle", "recall", "mémoire", "memory", "stocke", "store",
        "enregistre", "save", "note", "apprends", "learn",
    ],
    "reasoning": [
        "analyse", "analyze", "compare", "évalue", "evaluate", "pourquoi",
        "why", "comment", "how", "explique", "explain", "logique", "logic",
        "raisonne", "reason", "stratégie", "strategy", "planifie", "plan",
        "critique", "avantages", "inconvénients", "pros", "cons",
    ],
    "light": [
        "résume", "summarize", "court", "short", "bref", "brief",
        "en une phrase", "in one sentence", "tldr", "tl;dr", "vite",
        "quick", "rapide", "fast",
    ],
}

# Prompt système pour le routeur sémantique LLM
_ROUTER_PROMPT = """Tu es un classificateur d'intentions. Analyse la requête et réponds avec UN SEUL mot parmi:
- chat (conversation générale)
- code (programmation, debug, scripts)
- system (commandes système, fichiers, processus)
- memory (mémorisation, rappel de souvenirs)
- reasoning (analyse complexe, comparaison, logique)
- light (résumé rapide, question simple)

Requête: {query}

Intention:"""


class Router:
    """Route les requêtes vers le mode de traitement approprié via analyse sémantique."""

    VALID_MODES = {"chat", "code", "system", "memory", "reasoning", "light"}

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm

    def route(self, query: str, context: str = None) -> str:
        """
        Analyse la requête et retourne le mode approprié.

        Tente d'abord le routage LLM (sémantique), puis fallback sur les mots-clés.
        """
        if self.use_llm:
            mode = self._route_llm(query)
            if mode:
                return mode

        return self._route_keywords(query)

    def _route_llm(self, query: str) -> str | None:
        """Routage sémantique via LLM léger."""
        try:
            prompt = _ROUTER_PROMPT.format(query=query)
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": LIGHT_MODEL,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=15,
            )
            response.raise_for_status()
            raw = response.json().get("response", "").strip().lower()

            # Extraire le premier mot valide
            for word in raw.split():
                cleaned = word.strip(".,;:!?\"'")
                if cleaned in self.VALID_MODES:
                    logger.info("Route LLM: '%s' → %s", query[:50], cleaned)
                    return cleaned

            logger.debug("Route LLM: réponse non exploitable '%s'", raw[:50])
            return None
        except Exception as e:
            logger.debug("Route LLM indisponible (%s), fallback keywords", e)
            return None

    def _route_keywords(self, query: str) -> str:
        """Routage par scoring de mots-clés (fallback)."""
        q = query.lower()
        scores = {}

        for mode, keywords in _KEYWORD_MAP.items():
            scores[mode] = sum(1 for kw in keywords if kw in q)

        best = max(scores, key=scores.get)
        if scores[best] > 0:
            logger.debug("Route keywords: '%s' → %s (score=%d)", query[:50], best, scores[best])
            return best

        logger.debug("Route: '%s' → chat (défaut)", query[:50])
        return "chat"
