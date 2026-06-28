"""Fallback de busca de notícias via newsdata.io (usado quando newsapi.org falha)."""
from __future__ import annotations

import os

import requests

_API_KEY = os.environ.get("NEWS_DATA_KEY", "")
_BASE_URL = "https://newsdata.io/api/1/latest"

_DOMINIOS_BLOQUEADOS = {
    "nature.com", "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "sciencedirect.com",
    "springer.com", "wiley.com", "researchgate.net", "semanticscholar.org",
    "highsnobiety.com", "naturalnews.com",
}


def _dominio_bloqueado(url: str) -> bool:
    from urllib.parse import urlparse
    host = urlparse(url).netloc.lower().lstrip("www.")
    return any(host == d or host.endswith("." + d) for d in _DOMINIOS_BLOQUEADOS)


def buscar(nome: str, termos: str, lang: str = "pt", debug: bool = False) -> list[dict]:
    """Busca artigos no newsdata.io e normaliza para o mesmo formato do newsapi.org.

    Retorna lista de dicts com: title, description, url, publishedAt.
    Retorna lista vazia em caso de erro.
    """
    if not _API_KEY:
        print("      [fallback] NEWS_DATA_KEY não definida, pulando newsdata.io")
        return []

    params: dict = {
        "apikey": _API_KEY,
        "q": f'"{nome}" AND ({termos})',
        "language": lang,
    }
    # newsdata.io aceita country para filtrar; pt → br, en → us
    if lang == "pt":
        params["country"] = "br"

    if debug:
        print(f"      [fallback/debug] query [{lang}]: {params['q']}")

    try:
        r = requests.get(_BASE_URL, params=params, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"      [fallback/erro] newsdata.io: {e}")
        return []

    data = r.json()
    if data.get("status") != "success":
        print(f"      [fallback/erro] newsdata.io status: {data.get('message') or data.get('results')}")
        return []

    artigos = []
    for item in data.get("results") or []:
        url = item.get("link") or ""
        if _dominio_bloqueado(url):
            continue
        artigos.append({
            "title": item.get("title"),
            "description": item.get("description"),
            "url": url,
            # newsdata.io usa pubDate; normaliza para publishedAt
            "publishedAt": item.get("pubDate"),
        })

    return artigos
