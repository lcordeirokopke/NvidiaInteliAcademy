"""Fallback de busca de notícias via newsdata.io (usado quando newsapi.org falha)."""
from __future__ import annotations

import os

import requests

_BASE_URL = "https://newsdata.io/api/1/news"

_DOMINIOS_BLOQUEADOS = {
    "nature.com", "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "sciencedirect.com",
    "springer.com", "wiley.com", "researchgate.net", "semanticscholar.org",
    "highsnobiety.com", "naturalnews.com",
}


def _dominio_bloqueado(url: str) -> bool:
    from urllib.parse import urlparse
    host = urlparse(url).netloc.lower().lstrip("www.")
    return any(host == d or host.endswith("." + d) for d in _DOMINIOS_BLOQUEADOS)


_cota_esgotada = False


def buscar(nome: str, debug: bool = False) -> list[dict]:
    """Busca artigos no newsdata.io e normaliza para o mesmo formato do newsapi.org.

    Retorna lista de dicts com: title, description, url, publishedAt.
    Retorna lista vazia em caso de erro.
    """
    global _cota_esgotada
    if _cota_esgotada:
        return []

    api_key = os.environ.get("NEWS_DATA_KEY", "")
    if not api_key:
        print("      [fallback] NEWS_DATA_KEY não definida, pulando newsdata.io")
        return []

    # plano gratuito não suporta OR/parênteses; múltiplos termos sem aspas são AND implícito.
    # Busca o nome + "inteligência" (sem exigir a frase exata completa) para ampliar recall.
    q = f'"{nome}" inteligência artificial'
    params: dict = {
        "apikey": api_key,
        "q": q,
        "language": "pt",
        "country": "br",
    }

    if debug:
        print(f"      [fallback/debug] query: {q}")

    try:
        r = requests.get(_BASE_URL, params=params, timeout=10)
        if r.status_code == 429:
            print("      [fallback/newsdata] cota diária esgotada — pulando para o restante da execução")
            _cota_esgotada = True
            return []
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
