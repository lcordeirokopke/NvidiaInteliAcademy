from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
if _ENV_PATH.exists():
    for _line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

_GEMINI_MODEL = "text-embedding-004"
_FALLBACK_MODEL = "paraphrase-multilingual-mpnet-base-v2"

_fallback_encoder = None


def _get_gemini_client() -> genai.Client:
    if not hasattr(_get_gemini_client, "_instance"):
        api_key = os.environ.get("GEMINI_API_KEY2")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY2 não configurada no .env")
        http = httpx.Client(verify=False)
        _get_gemini_client._instance = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(httpx_client=http),
        )
    return _get_gemini_client._instance


def _get_fallback_encoder():
    global _fallback_encoder
    if _fallback_encoder is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Carregando modelo fallback '%s'...", _FALLBACK_MODEL)
        _fallback_encoder = SentenceTransformer(_FALLBACK_MODEL)
    return _fallback_encoder


def _embedding_via_gemini(texto: str) -> list[float]:
    client = _get_gemini_client()
    result = client.models.embed_content(
        model=_GEMINI_MODEL,
        contents=texto,
    )
    return result.embeddings[0].values


def _embedding_via_fallback(texto: str) -> list[float]:
    encoder = _get_fallback_encoder()
    return encoder.encode(texto).tolist()


def gerar_embedding(texto: str) -> list[float]:
    try:
        return _embedding_via_gemini(texto)
    except Exception as exc:
        logger.warning("Gemini embedding falhou (%s). Usando fallback local.", exc)
        return _embedding_via_fallback(texto)


def gerar_embeddings(textos: list[str]) -> list[list[float]]:
    return [gerar_embedding(t) for t in textos]
