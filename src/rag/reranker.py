from __future__ import annotations

from sentence_transformers import CrossEncoder

_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_encoder: CrossEncoder | None = None


def _get_encoder() -> CrossEncoder:
    global _encoder
    if _encoder is None:
        _encoder = CrossEncoder(_MODEL_NAME)
    return _encoder


def reranquear(query: str, candidatos: list[dict], top_k: int) -> list[dict]:
    if not candidatos:
        return candidatos

    encoder = _get_encoder()
    pares = [(query, c["texto"]) for c in candidatos]
    scores = encoder.predict(pares)

    ranqueados = sorted(
        zip(scores, candidatos),
        key=lambda x: x[0],
        reverse=True,
    )

    return [
        {**c, "rerank_score": float(s)}
        for s, c in ranqueados[:top_k]
    ]
