from __future__ import annotations

import uuid

from qdrant_client.models import PointStruct

from src.rag.client import get_client
from src.rag.embedding import gerar_embedding
from src.rag.setup_qdrant import COLLECTION_NAME


def indexar_documento(texto: str, metadata: dict) -> str:
    """Gera embedding e insere um documento na collection. Retorna o ID gerado."""
    client = get_client()
    embedding = gerar_embedding(texto)
    doc_id = str(uuid.uuid4())

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=doc_id,
                vector=embedding,
                payload={"texto": texto, **metadata},
            )
        ],
    )
    return doc_id


def indexar_documentos(documentos: list[dict]) -> list[str]:
    """
    Indexa múltiplos documentos em lote.
    Cada documento deve ter 'texto' e opcionalmente outros campos de metadata.
    """
    ids = []
    for doc in documentos:
        texto = doc.pop("texto")
        doc_id = indexar_documento(texto, metadata=doc)
        ids.append(doc_id)
    return ids
