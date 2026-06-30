from __future__ import annotations

"""
Passo 4 do pipeline: extrai as top 3 tecnologias do reranking.

Lê chunks_reranqueados (já ordenados por rerank_score) de recomendacoes_nvidia,
extrai os nomes das 3 tecnologias mais relevantes e salva em recomendacoes (text[]).

Nenhuma chamada de LLM — processamento local puro.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

_RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_RAIZ / "src"))
load_dotenv(_RAIZ / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_TOP_N = 3
_PAUSA_ENTRE_EMPRESAS = 0.5
_DIR_JSON = Path(__file__).resolve().parent.parent.parent / "data" / "jsons" / "recomendacoes_nvidia"


def _supabase():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def _buscar_pendentes(supabase, empresa_id: int | None = None) -> list[dict]:
    """Retorna linhas com chunks prontos mas recomendacoes ainda não extraídas."""
    query = (
        supabase.table("recomendacoes_nvidia")
        .select("empresa_id, chunks_reranqueados")
        .not_.is_("chunks_reranqueados", "null")
        .is_("recomendacoes", "null")
    )
    if empresa_id is not None:
        query = query.eq("empresa_id", empresa_id)
    return query.execute().data


def _buscar_forcar(supabase, empresa_id: int | None = None) -> list[dict]:
    query = (
        supabase.table("recomendacoes_nvidia")
        .select("empresa_id, chunks_reranqueados")
        .not_.is_("chunks_reranqueados", "null")
    )
    if empresa_id is not None:
        query = query.eq("empresa_id", empresa_id)
    return query.execute().data


def _extrair_top3(chunks: list[dict]) -> tuple[list[str], list[dict]]:
    """Deduplica por tecnologia mantendo a ordem de rerank_score.

    Retorna:
        nomes   — lista de strings para salvar no banco (text[])
        top_chunks — lista de dicts completos para salvar no JSON
    """
    vistos: set[str] = set()
    nomes: list[str] = []
    top_chunks: list[dict] = []
    for chunk in chunks:
        nome = chunk.get("tecnologia")
        if nome and nome not in vistos:
            vistos.add(nome)
            nomes.append(nome)
            top_chunks.append(chunk)
        if len(nomes) == _TOP_N:
            break
    return nomes, top_chunks


def _salvar_banco(supabase, empresa_id: int, recomendacoes: list[str]) -> None:
    supabase.table("recomendacoes_nvidia").upsert(
        {"empresa_id": empresa_id, "recomendacoes": recomendacoes},
        on_conflict="empresa_id",
    ).execute()
    logger.info("[%s] recomendacoes salvas no banco: %s", empresa_id, recomendacoes)


def _salvar_json(empresa_id: int, top_chunks: list[dict]) -> None:
    _DIR_JSON.mkdir(parents=True, exist_ok=True)
    caminho = _DIR_JSON / f"{empresa_id}.json"
    caminho.write_text(
        json.dumps({"empresa_id": empresa_id, "top3": top_chunks}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("[%s] JSON salvo em %s", empresa_id, caminho)


def rodar(empresa_id: int | None = None, forcar: bool = False) -> None:
    supabase = _supabase()
    rows = _buscar_forcar(supabase, empresa_id) if forcar else _buscar_pendentes(supabase, empresa_id)

    if not rows:
        logger.info("Nenhuma empresa pendente.")
        return

    logger.info("%d empresa(s) para processar.", len(rows))

    processadas = erros = 0

    for row in rows:
        eid = row["empresa_id"]
        chunks = row.get("chunks_reranqueados") or []

        if not chunks:
            logger.warning("[%s] chunks_reranqueados vazio — pulando.", eid)
            erros += 1
            continue

        nomes, top_chunks = _extrair_top3(chunks)

        if not nomes:
            logger.warning("[%s] nenhuma tecnologia encontrada nos chunks — pulando.", eid)
            erros += 1
            continue

        _salvar_banco(supabase, eid, nomes)
        _salvar_json(eid, top_chunks)
        top3 = nomes
        print(f"  [{eid}] {top3}")
        processadas += 1

        time.sleep(_PAUSA_ENTRE_EMPRESAS)

    print(f"\nConcluído — processadas: {processadas} | erros: {erros}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extrai top 3 tecnologias do reranking.")
    parser.add_argument("--empresa-id", type=int, default=None)
    parser.add_argument("--forcar", action="store_true")
    args = parser.parse_args()

    rodar(empresa_id=args.empresa_id, forcar=args.forcar)
