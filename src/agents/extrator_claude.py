from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
if _ENV_PATH.exists():
    for _line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 150


def _get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY não configurada no .env")
    try:
        import anthropic  # type: ignore
    except ImportError as exc:
        raise ImportError("Instale o pacote anthropic: pip install anthropic") from exc
    return anthropic.Anthropic(api_key=api_key)


def resumir_produto(textos: list[str], nome_empresa: str) -> str | None:
    """Resume textos coletados do site em 1-2 frases descrevendo o produto principal.

    Retorna None se a API não estiver disponível ou a resposta vier vazia.
    """
    conteudo = "\n\n".join(f"[Fonte {i+1}]\n{t}" for i, t in enumerate(textos) if t)
    if not conteudo.strip():
        return None

    try:
        client = _get_client()
    except (EnvironmentError, ImportError) as exc:
        logger.warning("Claude indisponível: %s", exc)
        return None

    try:
        resposta = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Com base nos trechos abaixo do site da empresa '{nome_empresa}', "
                        "escreva UMA frase (máximo 2) descrevendo o produto ou serviço principal. "
                        "Seja objetivo e use linguagem de negócios. Responda apenas a frase, sem explicações.\n\n"
                        + conteudo
                    ),
                }
            ],
        )
        texto = resposta.content[0].text.strip() if resposta.content else ""
        return texto or None
    except Exception as exc:  # noqa: BLE001
        logger.error("Erro na API Claude (resumir_produto): %s", exc)
        return None


def inferir_produto(nome_empresa: str, dominio: str) -> str | None:
    """Infere o produto da empresa a partir do conhecimento do modelo, sem conteúdo do site.

    Retorna None se o modelo não reconhecer a empresa ou a API não estiver disponível.
    """
    try:
        client = _get_client()
    except (EnvironmentError, ImportError) as exc:
        logger.warning("Claude indisponível: %s", exc)
        return None

    try:
        resposta = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Qual é o produto ou serviço principal da empresa '{nome_empresa}' "
                        f"(domínio: {dominio})? "
                        "Se você conhecer essa empresa, descreva em UMA frase objetiva o que ela oferece. "
                        "Se não tiver certeza, responda exatamente: NAO_ENCONTRADO"
                    ),
                }
            ],
        )
        texto = resposta.content[0].text.strip() if resposta.content else ""
        if not texto or texto == "NAO_ENCONTRADO":
            return None
        return texto
    except Exception as exc:  # noqa: BLE001
        logger.error("Erro na API Claude (inferir_produto): %s", exc)
        return None
