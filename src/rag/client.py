from __future__ import annotations

from qdrant_client import QdrantClient

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url="http://localhost:6333")
    return _client
