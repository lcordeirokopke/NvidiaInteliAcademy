from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from supabase import create_client

from dados_ia_startups.fallback import gnews as _fallback_gnews
from dados_ia_startups.fallback import newsdata_io as _fallback

_RAIZ = Path(__file__).resolve().parent.parent.parent
load_dotenv(_RAIZ / ".env")

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

_NEWS_API_KEY = os.environ["NEWS_API_KEY"]
_NEWS_API_URL = "https://newsapi.org/v2/everything"

_QUERIES = [
    # 1 — ação + produto com IA: empresa fez algo concreto ou tem produto com IA
    (
        '(implementou OR lançou OR integrou OR desenvolveu OR automatizou'
        ' OR "com IA" OR "assistente virtual" OR chatbot OR copilot)'
        ' AND ("inteligência artificial" OR "machine learning" OR "IA generativa"'
        ' OR "modelo de linguagem" OR "GPT" OR "LLM")'
    ),
    # 2 — aporte/investimento com foco em IA: veículos BR cobrem rodadas extensamente
    (
        '("aporte" OR "rodada" OR "captou" OR "investimento" OR "Series A" OR "seed")'
        ' AND ("inteligência artificial" OR "IA" OR "machine learning")'
    ),
]

_MAX_ARTIGOS_POR_EMPRESA = 5

_DOMINIOS_BR = (
    "valor.globo.com,exame.com,startups.com.br,neofeed.com,"
    "folha.uol.com.br,estadao.com.br,infomoney.com.br,"
    "tecmundo.com.br,olhardigital.com.br,canarinho.vc,"
    "forbes.com.br,pegn.globo.com,revistapegn.globo.com,"
    "epocanegocios.globo.com,braziljournal.com,siliconvalleybrasil.com.br,"
    "canaltech.com.br,computerworld.com.br,startupi.com.br"
)

_DOMINIOS_BR_SET = set(_DOMINIOS_BR.replace("\n", "").split(","))

_DOMINIOS_BLOQUEADOS = {
    "nature.com", "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "sciencedirect.com",
    "springer.com", "wiley.com", "researchgate.net", "semanticscholar.org",
    "highsnobiety.com", "naturalnews.com",
}

_SAIDA = _RAIZ / "data" / "imprensa"

# Flag de sessão: quando True, pula News API para todas as empresas restantes
# para não desperdiçar tentativas após cota diária esgotada (429)
_news_api_esgotada = False


def _buscar(nome: str, termos: str, lang: str = "pt", debug: bool = False) -> list[dict]:
    global _news_api_esgotada

    if debug:
        q = f'"{nome}" AND ({termos})'
        print(f"      [debug] query [{lang}]: {q}")

    usar_fallback = False
    if _news_api_esgotada:
        usar_fallback = True
    else:
        params = {
            "q": f'"{nome}" AND ({termos})',
            "language": lang,
            "sortBy": "relevancy",
            "pageSize": 10,
            "apiKey": _NEWS_API_KEY,
            "domains": _DOMINIOS_BR,
        }
        try:
            r = requests.get(_NEWS_API_URL, params=params, timeout=10)
            if r.status_code == 429:
                print("      [erro] News API: cota diária esgotada — usando apenas fallbacks pelo restante da execução")
                _news_api_esgotada = True
                usar_fallback = True
            else:
                r.raise_for_status()
                data = r.json()
                if data.get("status") != "ok":
                    print(f"      [erro] News API: {data.get('message')} — tentando fallback")
                    usar_fallback = True
                else:
                    return data.get("articles", [])
        except requests.RequestException as e:
            print(f"      [erro] News API: {e} — tentando fallback")
            usar_fallback = True

    if usar_fallback:
        resultado = _fallback.buscar(nome, termos, lang=lang, debug=debug)
        if resultado:
            return resultado
        return _fallback_gnews.buscar(nome, debug=debug)

    return []


def _dominio_bloqueado(url: str) -> bool:
    from urllib.parse import urlparse
    host = urlparse(url).netloc.lower().lstrip("www.")
    return any(host == d or host.endswith("." + d) for d in _DOMINIOS_BLOQUEADOS)


def _dominio_brasileiro(url: str) -> bool:
    from urllib.parse import urlparse
    host = urlparse(url).netloc.lower().lstrip("www.")
    return host in _DOMINIOS_BR_SET


def _filtrar(artigos: list[dict], nome: str) -> list[dict]:
    """Mantém só artigos onde o nome exato aparece no TÍTULO e o domínio é brasileiro."""
    padrao = re.compile(r'\b' + re.escape(nome.lower()) + r'\b')
    relevantes = []
    for a in artigos:
        url = a.get("url") or ""
        if _dominio_bloqueado(url):
            continue
        if not _dominio_brasileiro(url):
            continue
        titulo = (a.get("title") or "").lower()
        if padrao.search(titulo):
            relevantes.append(a)
    return relevantes[:_MAX_ARTIGOS_POR_EMPRESA]


def _salvar_json(registros: list[dict]) -> None:
    _SAIDA.mkdir(parents=True, exist_ok=True)
    caminho = _SAIDA / "noticias_encontradas.json"

    existentes: list[dict] = []
    if caminho.exists():
        existentes = json.loads(caminho.read_text(encoding="utf-8"))

    urls_existentes = {r["fonte_url"] for r in existentes if r.get("fonte_url")}
    novos = [r for r in registros if r.get("fonte_url") not in urls_existentes]

    caminho.write_text(
        json.dumps(existentes + novos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[json] {len(novos)} registro(s) novo(s) salvo(s) em {caminho}")


def _ja_checado(empresa_id: int) -> bool:
    """Retorna True se já existe qualquer linha de imprensa para essa empresa."""
    resultado = (
        supabase.table("sinais_ia")
        .select("id")
        .eq("empresa_id", empresa_id)
        .eq("camada", "imprensa")
        .limit(1)
        .execute()
    )
    return len(resultado.data) > 0


def pesquisar(debug: bool = False, nome: str | None = None) -> None:
    query = supabase.table("empresas").select("id, nome")
    if nome:
        query = query.eq("nome", nome)
    empresas = query.execute().data
    print(f"[info] {len(empresas)} empresa(s) carregada(s) do Supabase\n")

    todos_registros: list[dict] = []

    for empresa in empresas:
        empresa_id = empresa["id"]
        nome = empresa["nome"]
        print(f"[→] {nome}")

        if _ja_checado(empresa_id):
            print(f"    [skip] já checado anteriormente")
            continue

        vistos: set[str] = set()
        todos_artigos: list[dict] = []
        for termos, lang in zip(_QUERIES, ["pt", "pt"]):
            for artigo in _buscar(nome, termos, lang=lang, debug=debug):
                url = artigo.get("url", "")
                if url and url not in vistos:
                    vistos.add(url)
                    todos_artigos.append(artigo)
            time.sleep(1)

        relevantes = _filtrar(todos_artigos, nome)

        if relevantes:
            for artigo in relevantes:
                titulo = artigo.get("title") or ""
                descricao = artigo.get("description") or ""
                evidencia = f"{titulo} — {descricao}".strip(" —")

                published_at = artigo.get("publishedAt")

                supabase.table("sinais_ia").insert({
                    "empresa_id": empresa_id,
                    "camada": "imprensa",
                    "encontrado": True,
                    "evidencia": evidencia,
                    "fonte_url": artigo.get("url"),
                    "publicado_em": published_at,
                }).execute()

                todos_registros.append({
                    "empresa_id": empresa_id,
                    "nome_empresa": nome,
                    "evidencia": evidencia,
                    "fonte_url": artigo.get("url"),
                    "publicado_em": published_at,
                    "encontrado": True,
                    "coletado_em": datetime.now(timezone.utc).isoformat(),
                })

            print(f"    [✓] {len(relevantes)} notícia(s) encontrada(s)")
        else:
            supabase.table("sinais_ia").insert({
                "empresa_id": empresa_id,
                "camada": "imprensa",
                "encontrado": False,
                "evidencia": None,
                "fonte_url": None,
                "publicado_em": None,
            }).execute()

            todos_registros.append({
                "empresa_id": empresa_id,
                "nome_empresa": nome,
                "evidencia": None,
                "fonte_url": None,
                "publicado_em": None,
                "encontrado": False,
                "coletado_em": datetime.now(timezone.utc).isoformat(),
            })

            print(f"    [✗] nenhuma notícia encontrada")

    if todos_registros:
        _salvar_json(todos_registros)

    positivos = sum(1 for r in todos_registros if r["encontrado"])
    print(f"\n[resumo] {positivos}/{len(empresas)} empresa(s) com notícias de IA")


if __name__ == "__main__":
    import sys
    debug = "--debug" in sys.argv
    pesquisar(debug=debug)
