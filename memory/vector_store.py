"""
PIThy - Vector Store (ChromaDB)
Stockage et recherche vectorielle via le service ChromaDB Docker.
"""

import logging
import time
import uuid
import chromadb
from memory.embeddings import Embeddings
from config import CHROMA_URL

logger = logging.getLogger(__name__)


def _parse_chroma_url(url: str):
    """Extrait host et port depuis l'URL ChromaDB."""
    url = url.rstrip("/")
    if "://" in url:
        url = url.split("://", 1)[1]
    parts = url.split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 8000
    return host, port


class VectorStore:
    """Interface avec ChromaDB pour le stockage vectoriel."""

    COLLECTION_NAME = "pithy_memory"

    def __init__(self, max_retries: int = 5, retry_delay: int = 3):
        self.embedder = Embeddings()
        self.client = None
        self.collection = None
        self._connect(max_retries, retry_delay)

    def _connect(self, max_retries: int, retry_delay: int):
        """Connexion à ChromaDB avec retry."""
        host, port = _parse_chroma_url(CHROMA_URL)
        for attempt in range(1, max_retries + 1):
            try:
                self.client = chromadb.HttpClient(host=host, port=port)
                # Test de connexion
                self.client.heartbeat()
                self.collection = self.client.get_or_create_collection(
                    name=self.COLLECTION_NAME
                )
                logger.info(
                    "ChromaDB connecté (%s:%d) — collection '%s'",
                    host, port, self.COLLECTION_NAME,
                )
                return
            except Exception as e:
                logger.warning(
                    "ChromaDB tentative %d/%d échouée: %s",
                    attempt, max_retries, e,
                )
                if attempt < max_retries:
                    time.sleep(retry_delay)

        logger.error("Impossible de se connecter à ChromaDB après %d tentatives", max_retries)
        raise ConnectionError(f"ChromaDB non joignable ({host}:{port})")

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def add(self, text: str, doc_id: str = None):
        """Ajoute un document unique à la collection."""
        if not self.collection:
            return

        emb = self.embedder.embed(text)
        if not emb:
            logger.warning("Embedding vide, document non ajouté")
            return

        doc_id = doc_id or str(uuid.uuid4())
        try:
            self.collection.upsert(
                documents=[text],
                embeddings=[emb],
                ids=[doc_id],
            )
        except Exception as e:
            logger.error("Erreur ajout ChromaDB: %s", e)

    def add_texts(self, texts: list, metadatas: list = None):
        """Ajoute plusieurs documents à la collection."""
        if not self.collection or not texts:
            return

        ids = [str(uuid.uuid4()) for _ in texts]
        embeddings = []
        valid_texts = []
        valid_ids = []
        valid_metas = []

        for i, text in enumerate(texts):
            emb = self.embedder.embed(text)
            if emb:
                embeddings.append(emb)
                valid_texts.append(text)
                valid_ids.append(ids[i])
                if metadatas:
                    valid_metas.append(metadatas[i] if i < len(metadatas) else {})

        if not valid_texts:
            return

        try:
            kwargs = {
                "documents": valid_texts,
                "embeddings": embeddings,
                "ids": valid_ids,
            }
            if valid_metas:
                kwargs["metadatas"] = valid_metas
            self.collection.upsert(**kwargs)
            logger.info("Ajouté %d documents à ChromaDB", len(valid_texts))
        except Exception as e:
            logger.error("Erreur ajout batch ChromaDB: %s", e)

    def search(self, query: str, k: int = 3) -> list:
        """Recherche les k documents les plus proches."""
        if not self.collection:
            return []

        query_emb = self.embedder.embed(query)
        if not query_emb:
            return []

        try:
            results = self.collection.query(
                query_embeddings=[query_emb],
                n_results=k,
            )
            docs = results.get("documents", [[]])
            return docs[0] if docs else []
        except Exception as e:
            logger.error("Erreur recherche ChromaDB: %s", e)
            return []

    def get_context(self, query: str, max_tokens: int = 1000) -> str:
        """Retourne le contexte RAG formaté pour injection dans le prompt."""
        docs = self.search(query)
        if not docs:
            return ""

        context_parts = []
        total_len = 0
        for doc in docs:
            if total_len + len(doc) > max_tokens:
                break
            context_parts.append(doc)
            total_len += len(doc)

        return "\n---\n".join(context_parts)

    def count(self) -> int:
        """Retourne le nombre de documents dans la collection."""
        if not self.collection:
            return 0
        try:
            return self.collection.count()
        except Exception:
            return 0
