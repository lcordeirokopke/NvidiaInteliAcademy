from __future__ import annotations

from src.rag.client import get_client
from src.rag.embedding import gerar_embedding
from src.rag.setup_qdrant import COLLECTION_NAME


def buscar(query: str, top_k: int = 10) -> list[dict]:
    """Busca vetorial: retorna os top_k chunks mais similares à query."""
    client = get_client()
    embedding = gerar_embedding(query)

    resultados = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=embedding,
        limit=top_k,
        with_payload=True,
    )

    return [
        {"score": r.score, "texto": r.payload.get("texto", ""), **r.payload}
        for r in resultados
    ]
