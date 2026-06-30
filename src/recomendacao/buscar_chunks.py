from __future__ import annotations

"""
Passo 2 do pipeline: busca semântica no Qdrant.

Lê a query gerada pelo passo 1 (recomendacoes_nvidia.query), gera o embedding,
busca chunks relevantes no Qdrant com reranking e salva as referências em
recomendacoes_nvidia.chunks_reranqueados.

Pré-requisitos:
  - Passo 1 concluído (recomendacoes_nvidia.query preenchida)
  - Qdrant indexado com a base de conhecimento NVIDIA
  - SUPABASE_* configurados no .env
"""

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

_RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_RAIZ / "src"))
load_dotenv(_RAIZ / ".env")

from agents.query import resolver_setor_qdrant  # noqa: E402
from rag import buscador  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_TOP_K = 5
_FATOR_CANDIDATOS = 3
_PAUSA_ENTRE_EMPRESAS = 1.0


def _supabase():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def _buscar_pendentes(supabase, empresa_id: int | None = None) -> list[dict]:
    """Retorna linhas com query preenchida mas chunks ainda não buscados."""
    query = (
        supabase.table("recomendacoes_nvidia")
        .select("empresa_id, query")
        .not_.is_("query", "null")
        .is_("chunks_reranqueados", "null")
    )
    if empresa_id is not None:
        query = query.eq("empresa_id", empresa_id)
    return query.execute().data


def _buscar_setor(supabase, empresa_id: int) -> str | None:
    resultado = (
        supabase.table("empresas_uso_ia")
        .select("setor")
        .eq("empresa_id", empresa_id)
        .limit(1)
        .execute()
        .data
    )
    return resultado[0]["setor"] if resultado else None


def _serializar_chunks(chunks: list[dict]) -> list[dict]:
    resultado = []
    for i, c in enumerate(chunks):
        resultado.append({
            "chunk_index": i,
            "tecnologia": c.get("tecnologia"),
            "url": c.get("url"),
            "rerank_score": round(c.get("rerank_score", c.get("score", 0)), 4),
            "texto": c.get("texto"),
        })
    return resultado


def _salvar_chunks(supabase, empresa_id: int, chunks: list[dict]) -> None:
    supabase.table("recomendacoes_nvidia").upsert(
        {
            "empresa_id": empresa_id,
            "chunks_reranqueados": chunks,
            "versao_base_conhecimento": datetime.utcnow().strftime("%Y-%m-%d"),
        },
        on_conflict="empresa_id",
    ).execute()
    logger.info("[%s] %d chunk(s) salvo(s) em chunks_reranqueados", empresa_id, len(chunks))


def rodar(empresa_id: int | None = None, forcar: bool = False) -> None:
    """
    Executa a busca semântica para todas as empresas com query pendente.

    Args:
        empresa_id: processa só essa empresa se informado; senão processa todas.
        forcar: se True, rebusca mesmo que chunks_reranqueados já esteja preenchido.
    """
    supabase = _supabase()

    if forcar and empresa_id is not None:
        # com --forcar, busca independente de chunks_reranqueados estar preenchido
        rows = (
            supabase.table("recomendacoes_nvidia")
            .select("empresa_id, query")
            .eq("empresa_id", empresa_id)
            .not_.is_("query", "null")
            .execute()
            .data
        )
    elif forcar:
        rows = (
            supabase.table("recomendacoes_nvidia")
            .select("empresa_id, query")
            .not_.is_("query", "null")
            .execute()
            .data
        )
    else:
        rows = _buscar_pendentes(supabase, empresa_id)

    if not rows:
        logger.info("Nenhuma empresa pendente de busca.")
        return

    logger.info("%d empresa(s) para processar.", len(rows))

    processadas = erros = 0

    for row in rows:
        eid = row["empresa_id"]
        query_texto = row["query"]

        setor = _buscar_setor(supabase, eid)
        setores_qdrant = resolver_setor_qdrant(setor)
        filtros = {"setor": {"$in": setores_qdrant}}

        logger.info("[%s] buscando chunks | query: %s", eid, query_texto)

        try:
            chunks = buscador.buscar(
                query=query_texto,
                filtros=filtros,
                top_k=_TOP_K,
                reranking=True,
                fator_candidatos=_FATOR_CANDIDATOS,
            )

            if not chunks:
                logger.warning("[%s] nenhum chunk retornado.", eid)
                erros += 1
                continue

            refs = _serializar_chunks(chunks)
            _salvar_chunks(supabase, eid, refs)

            for r in refs:
                print(f"  [{eid}] [{r['rerank_score']:.4f}] {r['tecnologia']} — {r['url']}")

            processadas += 1

        except Exception as exc:  # noqa: BLE001
            logger.error("[%s] erro na busca: %s", eid, exc)
            erros += 1

        time.sleep(_PAUSA_ENTRE_EMPRESAS)

    print(f"\nConcluído — processadas: {processadas} | erros: {erros}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Busca chunks no Qdrant e salva em recomendacoes_nvidia.")
    parser.add_argument("--empresa-id", type=int, default=None, help="Processa só essa empresa.")
    parser.add_argument("--forcar", action="store_true", help="Rebusca mesmo que chunks já existam.")
    args = parser.parse_args()

    rodar(empresa_id=args.empresa_id, forcar=args.forcar)
