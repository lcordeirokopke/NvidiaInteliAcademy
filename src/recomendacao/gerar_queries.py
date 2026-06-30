from __future__ import annotations

"""
Gera queries semânticas para o RAG e persiste em recomendacoes_nvidia.query.

Para cada startup elegível em empresas_uso_ia, chama o agente
query.py e faz upsert em recomendacoes_nvidia (coluna query).

Pré-requisitos:
  - Perfis com situacao_coleta elegível (ver verifica_situacao_coleta.py)
  - OPENROUTER_API_KEY e SUPABASE_* configurados no .env
  - Coluna query criada via sql/add_query_column.sql
"""

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

from agents.query import gerar_query  # noqa: E402
from recomendacao.verifica_situacao_coleta import SITUACOES_ELEGIVEIS  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_PAUSA_ENTRE_EMPRESAS = 1.5


def _supabase():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def _buscar_perfis(supabase, empresa_id: int | None = None) -> list[dict]:
    query = (
        supabase.table("empresas_uso_ia")
        .select("empresa_id, setor, produto, ia_tipo, nivel_maturidade_ia, ia_e_core_product, situacao_coleta")
        .in_("situacao_coleta", list(SITUACOES_ELEGIVEIS))
        .not_.is_("setor", "null")
        .not_.is_("produto", "null")
        .not_.is_("ia_tipo", "null")
    )
    if empresa_id is not None:
        query = query.eq("empresa_id", empresa_id)
    return query.execute().data


def _ja_tem_query(supabase, empresa_id: int) -> bool:
    resultado = (
        supabase.table("recomendacoes_nvidia")
        .select("empresa_id, query")
        .eq("empresa_id", empresa_id)
        .limit(1)
        .execute()
        .data
    )
    if not resultado:
        return False
    return bool(resultado[0].get("query"))


def _mapear_perfil(row: dict) -> dict:
    return {
        "setor": row.get("setor"),
        "produto": row.get("produto"),
        "ia_tipo": row.get("ia_tipo"),
        "maturidade": row.get("nivel_maturidade_ia"),
        "ia_core_product": row.get("ia_e_core_product"),
    }


def _salvar_query(supabase, empresa_id: int, query: str) -> None:
    supabase.table("recomendacoes_nvidia").upsert(
        {"empresa_id": empresa_id, "query": query},
        on_conflict="empresa_id",
    ).execute()
    logger.info("[%s] query salva em recomendacoes_nvidia", empresa_id)


def rodar(empresa_id: int | None = None, forcar: bool = False) -> None:
    """
    Gera e persiste queries semânticas para startups com perfil completo.

    Args:
        empresa_id: processa só essa empresa se informado; senão processa todas.
        forcar: se True, regera mesmo que já exista query no banco.
    """
    supabase = _supabase()
    perfis = _buscar_perfis(supabase, empresa_id)

    if not perfis:
        logger.info("Nenhum perfil completo encontrado.")
        return

    logger.info("%d empresa(s) para processar.", len(perfis))

    processadas = erros = puladas = 0

    for row in perfis:
        eid = row["empresa_id"]

        if not forcar and _ja_tem_query(supabase, eid):
            logger.info("[%s] query já existe — pulando", eid)
            puladas += 1
            continue

        perfil = _mapear_perfil(row)
        logger.info("[%s] gerando query | perfil: %s", eid, perfil)

        try:
            query = gerar_query(perfil)
            _salvar_query(supabase, eid, query)
            print(f"  [{eid}] {query}")
            processadas += 1
        except Exception as exc:  # noqa: BLE001
            logger.error("[%s] erro ao gerar query: %s", eid, exc)
            erros += 1

        time.sleep(_PAUSA_ENTRE_EMPRESAS)

    print(f"\nConcluído — processadas: {processadas} | puladas: {puladas} | erros: {erros}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gera queries semânticas e salva em recomendacoes_nvidia.")
    parser.add_argument("--empresa-id", type=int, default=None, help="Processa só essa empresa.")
    parser.add_argument("--forcar", action="store_true", help="Regera mesmo que já exista query no banco.")
    args = parser.parse_args()

    rodar(empresa_id=args.empresa_id, forcar=args.forcar)
