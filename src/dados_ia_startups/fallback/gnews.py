"""Fallback de busca de notícias via GNews API (usado quando newsapi.org e newsdata.io falham)."""
from __future__ import annotations

import os

import requests

_BASE_URL = "https://gnews.io/api/v4/search"

# GNews não indexa os mesmos domínios da News API — usa blocklist em vez de allowlist
# para não descartar resultados válidos de fontes brasileiras que o GNews indexa
_DOMINIOS_BLOQUEADOS = {
    "nature.com", "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "sciencedirect.com",
    "springer.com", "wiley.com", "researchgate.net", "semanticscholar.org",
    "highsnobiety.com", "naturalnews.com",
}


def _dominio_bloqueado(url: str) -> bool:
    from urllib.parse import urlparse
    host = urlparse(url).netloc.lower().lstrip("www.")
    return any(host == d or host.endswith("." + d) for d in _DOMINIOS_BLOQUEADOS)


_api_indisponivel = False


def buscar(nome: str, debug: bool = False) -> list[dict]:
    """Busca artigos no GNews e normaliza para o mesmo formato do newsapi.org.

    Retorna lista de dicts com: title, description, url, publishedAt.
    Retorna lista vazia em caso de erro.
    """
    global _api_indisponivel
    if _api_indisponivel:
        return []

    api_key = os.environ.get("GNNEWS_API_KEY", "")
    if not api_key:
        print("      [fallback/gnews] GNNEWS_API_KEY não definida, pulando gnews")
        return []

    # parênteses garantem que o nome seja obrigatório em todas as alternativas;
    # operadores de exclusão (-"...") não são suportados no plano gratuito do GNews
    q = (
        f'"{nome}" '
        f'("inteligência artificial" OR "machine learning" OR "IA generativa"'
        f' OR "chatbot" OR "automação inteligente" OR "LLM")'
    )
    params = {
        "token": api_key,
        "q": q,
        "lang": "pt",
        "country": "br",
        "max": 10,
        "sortby": "relevance",
    }

    if debug:
        print(f"      [fallback/gnews/debug] query: {q}")

    try:
        r = requests.get(_BASE_URL, params=params, timeout=10)
        if r.status_code in (401, 403, 429):
            print(f"      [fallback/gnews] API indisponível ({r.status_code}) — pulando para o restante da execução")
            _api_indisponivel = True
            return []
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"      [fallback/gnews/erro] {e}")
        return []

    data = r.json()
    artigos = []
    for item in data.get("articles") or []:
        url = item.get("url") or ""
        if _dominio_bloqueado(url):
            continue
        artigos.append({
            "title": item.get("title"),
            "description": item.get("description"),
            "url": url,
            "publishedAt": item.get("publishedAt"),
        })

    return artigos
