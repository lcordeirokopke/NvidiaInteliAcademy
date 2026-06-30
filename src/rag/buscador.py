from __future__ import annotations

from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

from src.rag.client import get_client
from src.rag.embedding import gerar_embedding
from src.rag.setup_qdrant import COLLECTION_NAME


def _montar_filtro(filtros: dict) -> Filter | None:
    if not filtros:
        return None

    condicoes = []
    for campo, valor in filtros.items():
        if isinstance(valor, dict) and "$in" in valor:
            condicoes.append(FieldCondition(key=campo, match=MatchAny(any=valor["$in"])))
        else:
            condicoes.append(FieldCondition(key=campo, match=MatchValue(value=valor)))

    return Filter(must=condicoes)


_CATEGORIAS_PADRAO = ["produto", "caso_de_uso", "stack", "inception"]
_SCORE_THRESHOLD = 0.55


def buscar(
    query: str,
    filtros: dict | None = None,
    top_k: int = 10,
    reranking: bool = False,
    fator_candidatos: int = 3,
) -> list[dict]:
    client = get_client()
    embedding = gerar_embedding(query)

    filtros_efetivos = dict(filtros) if filtros else {}
    filtros_efetivos.setdefault("categoria", {"$in": _CATEGORIAS_PADRAO})

    limite = top_k * fator_candidatos if reranking else top_k

    resultados = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=embedding,
        query_filter=_montar_filtro(filtros_efetivos),
        limit=limite,
        score_threshold=_SCORE_THRESHOLD,
        with_payload=True,
    )

    candidatos = [
        {"score": r.score, "texto": r.payload.get("texto", ""), **r.payload}
        for r in resultados
    ]

    if reranking:
        from src.rag.reranker import reranquear
        candidatos = reranquear(query, candidatos, top_k)

    return candidatos
