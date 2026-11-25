from __future__ import annotations

import json
import math
import os
import hashlib
import logging
import re
import sqlite3
import ssl
from contextlib import closing
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import chromadb
import certifi
from chromadb.errors import NotFoundError


logger = logging.getLogger(__name__)
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())


class RagConfigurationError(RuntimeError):
    """Raised when semantic retrieval cannot be configured or completed."""


def _api_key() -> str:
    key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RagConfigurationError("Set LLM_API_KEY or OPENAI_API_KEY in .env before using the remote provider.")
    return key


def provider_configured() -> bool:
    return bool(os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))


def embedding_provider_configured() -> bool:
    """Return whether a compatible remote embeddings provider was explicitly set.

    Groq's OpenAI-compatible chat API does not provide the embeddings endpoint.
    Ignore an embedding model name when the configured base URL points to Groq
    and use the built-in local embeddings instead.
    """
    if not provider_configured() or not os.getenv("EMBEDDING_MODEL", "").strip():
        return False
    host = urlparse(os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")).hostname or ""
    return host != "api.groq.com" and not host.endswith(".groq.com")


def _embed(texts: list[str]) -> list[list[float]]:
    """Embed with the configured provider, retaining local retrieval on provider failures."""
    if not texts:
        return []
    if not embedding_provider_configured():
        return [_local_embed(text) for text in texts]
    payload = {"model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"), "input": texts}
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    request = Request(
        f"{base_url}/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=35, context=TLS_CONTEXT) as response:  # noqa: S310 - operator-configured API URL
            result = json.loads(response.read().decode("utf-8"))
        vectors = [item["embedding"] for item in sorted(result["data"], key=lambda item: item["index"])]
        if len(vectors) != len(texts) or not all(isinstance(vector, list) and vector for vector in vectors):
            raise ValueError("response contained incomplete embedding data")
        return vectors
    except (HTTPError, URLError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        # Project creation and evidence retrieval stay usable when a configured
        # provider rejects a model, credential, or request.
        logger.warning("Embedding provider unavailable; using local embeddings instead: %s", exc)
        return [_local_embed(text) for text in texts]


def _local_embed(text: str, dimensions: int = 384) -> list[float]:
    """Create stable local vectors so the prototype remains usable without a provider key."""
    vector = [0.0] * dimensions
    for token in re.findall(r"[a-z0-9]{2,}", text.lower()):
        bucket = int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:4], "big") % dimensions
        vector[bucket] += 1.0
    magnitude = sum(value * value for value in vector) ** 0.5
    return [value / magnitude for value in vector] if magnitude else vector


class VectorStore:
    """Persistent vectors, using SQLite locally and Chroma for remote embeddings."""

    def __init__(self) -> None:
        root = Path(os.getenv("VECTOR_DB_PATH", Path(os.getenv("APP_DATA_DIR", "data")) / "chroma"))
        root.mkdir(parents=True, exist_ok=True)
        self.root = root
        self.local_db_path = root / "local-vectors.sqlite3"
        # Chroma's native upsert crashes on some Windows/Python combinations.
        # Local hashed embeddings need no native index, so persist those rows
        # in SQLite and rank them with a small pure-Python cosine calculation.
        self.client = chromadb.PersistentClient(path=str(root)) if embedding_provider_configured() else None

    def _local_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.local_db_path, timeout=30)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """CREATE TABLE IF NOT EXISTS local_vectors (
                project_id TEXT NOT NULL,
                vector_id TEXT NOT NULL,
                document TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                PRIMARY KEY (project_id, vector_id)
            )"""
        )
        return connection

    def _index_local(self, project_id: str, ids: list[str], texts: list[str], metadata: list[dict[str, str]]) -> int:
        vectors = _embed(texts)
        try:
            with closing(self._local_connection()) as connection:
                with connection:
                    connection.executemany(
                        """INSERT INTO local_vectors (project_id, vector_id, document, metadata_json, embedding_json)
                           VALUES (?, ?, ?, ?, ?)
                           ON CONFLICT(project_id, vector_id) DO UPDATE SET
                             document=excluded.document,
                             metadata_json=excluded.metadata_json,
                             embedding_json=excluded.embedding_json""",
                        [
                            (project_id, vector_id, text, json.dumps(meta), json.dumps(vector))
                            for vector_id, text, meta, vector in zip(ids, texts, metadata, vectors, strict=True)
                        ],
                    )
        except sqlite3.Error as exc:
            raise RagConfigurationError("The local vector database could not index the project sources.") from exc
        return len(texts)

    def _retrieve_local(self, project_id: str, query: str, limit: int) -> list[dict]:
        query_vector = _embed([query])[0]
        try:
            with closing(self._local_connection()) as connection:
                rows = connection.execute(
                    "SELECT vector_id, document, metadata_json, embedding_json FROM local_vectors WHERE project_id = ?",
                    (project_id,),
                ).fetchall()
        except sqlite3.Error as exc:
            raise RagConfigurationError("The local vector database could not retrieve project evidence.") from exc

        query_norm = math.sqrt(math.fsum(value * value for value in query_vector))
        ranked: list[tuple[float, dict]] = []
        for vector_id, document, metadata_json, embedding_json in rows:
            vector = json.loads(embedding_json)
            vector_norm = math.sqrt(math.fsum(value * value for value in vector))
            similarity = (
                math.fsum(left * right for left, right in zip(query_vector, vector, strict=True))
                / (query_norm * vector_norm)
                if query_norm and vector_norm
                else 0.0
            )
            metadata = json.loads(metadata_json)
            ranked.append((similarity, {
                "id": metadata["chunk_id"],
                "text": document,
                "document_id": metadata["document_id"],
                "document_name": metadata["document_name"],
                "relevance": round(max(0.0, min(1.0, similarity)), 2),
                "source_url": metadata.get("source_url") or None,
                "source_version": metadata.get("source_version") or None,
                "effective_date": metadata.get("effective_date") or None,
            }))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item for _, item in ranked[:limit]]

    @staticmethod
    def _collection_name(project_id: str) -> str:
        return f"finreq_{project_id}"

    @staticmethod
    def configuration() -> dict[str, str]:
        """Return safe-to-display settings without exposing provider credentials."""
        return {
            "vector_database": "ChromaDB" if embedding_provider_configured() else "SQLite local vector index",
            "embedding_model": os.getenv("EMBEDDING_MODEL") if embedding_provider_configured() else "Local hashed embeddings (384 dimensions)",
            "llm_model": os.getenv("LLM_MODEL", "gpt-4o-mini") if provider_configured() else "Evidence-only fallback",
            "collection_scope": "One persistent collection per project",
        }

    def index(self, project_id: str, documents: list[dict]) -> int:
        ids: list[str] = []
        texts: list[str] = []
        metadata: list[dict[str, str]] = []
        for document in documents:
            for chunk in document.get("chunks", []):
                ids.append(f"{document['id']}:{chunk['id']}")
                texts.append(chunk["text"])
                metadata.append({
                    "document_id": document["id"], "document_name": document["name"], "chunk_id": chunk["id"],
                    "source_url": document.get("source_url", ""), "source_version": document.get("version", ""),
                    "effective_date": document.get("effective_date", ""),
                })
        if not texts:
            raise RagConfigurationError("No text chunks were available for semantic indexing.")
        if not embedding_provider_configured():
            return self._index_local(project_id, ids, texts, metadata)
        try:
            if self.client is None:
                raise RagConfigurationError("The remote vector database is unavailable.")
            collection = self.client.get_or_create_collection(
                self._collection_name(project_id), metadata={"hnsw:space": "cosine"}
            )
            collection.upsert(ids=ids, documents=texts, metadatas=metadata, embeddings=_embed(texts))
        except RagConfigurationError:
            raise
        except Exception as exc:
            raise RagConfigurationError("The vector database could not index the project sources.") from exc
        return len(texts)

    def retrieve(self, project_id: str, query: str, limit: int = 6) -> list[dict]:
        if not embedding_provider_configured():
            return self._retrieve_local(project_id, query, limit)
        try:
            if self.client is None:
                raise RagConfigurationError("The remote vector database is unavailable.")
            collection = self.client.get_collection(self._collection_name(project_id))
        except NotFoundError as exc:
            raise RagConfigurationError("The project's vector collection is unavailable. Recreate the project to index its sources.") from exc
        try:
            result = collection.query(
                query_embeddings=_embed([query]),
                n_results=min(limit, collection.count()),
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise RagConfigurationError("The vector database could not retrieve project evidence.") from exc
        documents = result.get("documents", [[]])[0]
        metadata = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            {
                "id": item["chunk_id"],
                "text": text,
                "document_id": item["document_id"],
                "document_name": item["document_name"],
                "relevance": round(max(0.0, 1 - (distance / 2)), 2),
                "source_url": item.get("source_url") or None,
                "source_version": item.get("source_version") or None,
                "effective_date": item.get("effective_date") or None,
            }
            for text, item, distance in zip(documents, metadata, distances, strict=True)
        ]
