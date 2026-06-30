from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path

from google import genai

logger = logging.getLogger(__name__)

_ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if _ENV_PATH.exists():
    for _line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

_GEMINI_CHAT_MODEL = "gemini-2.5-flash"
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 5.0

_client_instance: genai.Client | None = None
_client_lock = threading.Lock()


def _get_client() -> genai.Client:
    global _client_instance
    if _client_instance is None:
        with _client_lock:
            if _client_instance is None:  # double-checked locking — mesmo padrão do reranker.py
                api_key = os.environ.get("GEMINI_API_KEY")
                if not api_key:
                    raise EnvironmentError("GEMINI_API_KEY não configurada no .env")
                _client_instance = genai.Client(api_key=api_key)
    return _client_instance


def chamar_gemini(prompt: str) -> str:
    """Chama o Gemini com retry exponencial. Levanta exceção após esgotar tentativas."""
    client = _get_client()
    last_exc: Exception | None = None

    for tentativa in range(1, _MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=_GEMINI_CHAT_MODEL,
                contents=prompt,
            )
            return (response.text or "").strip()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if tentativa < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2 ** (tentativa - 1))
                logger.warning(
                    "Gemini erro (tentativa %d/%d) — aguardando %.0fs: %s",
                    tentativa, _MAX_RETRIES, delay, exc,
                )
                time.sleep(delay)

    raise RuntimeError(f"Gemini falhou após {_MAX_RETRIES} tentativas") from last_exc
