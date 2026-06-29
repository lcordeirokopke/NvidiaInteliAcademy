from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

from . import define_maturidade
from .identidade import enriquece_identidade
from .outros import define_setor, descobre_ia_core_product, descobre_modelo_negocio, descobre_produto, descobre_produto_ia_lancado, descobre_uso_ia

_RAIZ = Path(__file__).resolve().parent.parent.parent
load_dotenv(_RAIZ / ".env")

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def _seed_aprovadas(nome: str | None = None) -> int:
    """Cria linhas em empresas_uso_ia para todas as aprovadas que ainda não estão lá."""
    aprovadas = (
        supabase.table("avaliacoes_ia")
        .select("empresa_id")
        .eq("veredito", True)
        .execute()
        .data
    )
    if not aprovadas:
        print("[info] nenhuma empresa aprovada em avaliacoes_ia")
        return 0

    ids_aprovadas = [int(r["empresa_id"]) for r in aprovadas]

    if nome:
        row = supabase.table("empresas").select("id").eq("nome", nome).limit(1).execute().data
        if row:
            target_id = int(row[0]["id"])
            ids_aprovadas = [eid for eid in ids_aprovadas if eid == target_id]
        else:
            ids_aprovadas = []

    existentes = (
        supabase.table("empresas_uso_ia")
        .select("empresa_id")
        .in_("empresa_id", ids_aprovadas)
        .execute()
        .data
    )
    ids_existentes = {int(r["empresa_id"]) for r in existentes}

    novas = [eid for eid in ids_aprovadas if eid not in ids_existentes]
    if not novas:
        print(f"[info] {len(ids_aprovadas)} empresa(s) aprovada(s) — todas já presentes em empresas_uso_ia")
        return 0

    # Busca dominio e gupy_subdominio para preencher desde o início
    empresas_rows = (
        supabase.table("empresas")
        .select("id, dominio, gupy_subdominio")
        .in_("id", novas)
        .execute()
        .data
    )
    mapa = {int(r["id"]): r for r in empresas_rows}

    registros = [
        {
            "empresa_id":      eid,
            "dominio":         mapa.get(eid, {}).get("dominio"),
            "gupy_subdominio": mapa.get(eid, {}).get("gupy_subdominio"),
        }
        for eid in novas
    ]

    supabase.table("empresas_uso_ia").insert(registros).execute()
    print(f"[banco] {len(registros)} nova(s) linha(s) criada(s) em empresas_uso_ia")
    return len(registros)


def atualizar(atualizar_banco: bool = True) -> None:
    """
    Pipeline completo de atualização de empresas_uso_ia:
      1. Seed — cria linhas para aprovadas ainda ausentes
      2. Enriquecimento — preenche cnpj e campos BrasilAPI
      3. Descoberta de produto — scraping + Playwright + Claude
      4. Descoberta de uso de IA — scraping + Playwright + Gemini
      5. Maturidade — calcula score e nível AI-native
    """
    print("=" * 55)
    print("  PASSO 1 — seed de aprovadas")
    print("=" * 55)
    _seed_aprovadas()

    print()
    print("=" * 55)
    print("  PASSO 2 — enriquecimento de identidade")
    print("=" * 55)
    enriquece_identidade.enriquecer(atualizar_banco=atualizar_banco)

    print()
    print("=" * 55)
    print("  PASSO 3 — descoberta de produto")
    print("=" * 55)
    descobre_produto.descobrir(atualizar_banco=atualizar_banco)

    print()
    print("=" * 55)
    print("  PASSO 4 — descoberta de uso de IA")
    print("=" * 55)
    descobre_uso_ia.descobrir(atualizar_banco=atualizar_banco)

    print()
    print("=" * 55)
    print("  PASSO 5 — classificação ia_e_core_product")
    print("=" * 55)
    descobre_ia_core_product.descobrir(atualizar_banco=atualizar_banco)

    print()
    print("=" * 55)
    print("  PASSO 6 — classificação modelo_negocio")
    print("=" * 55)
    descobre_modelo_negocio.descobrir(atualizar_banco=atualizar_banco)

    print()
    print("=" * 55)
    print("  PASSO 7 — verificação de produto_ia_lancado")
    print("=" * 55)
    descobre_produto_ia_lancado.descobrir(atualizar_banco=atualizar_banco)

    print()
    print("=" * 55)
    print("  PASSO 8 — classificação de setor")
    print("=" * 55)
    define_setor.descobrir(atualizar_banco=atualizar_banco)

    print()
    print("=" * 55)
    print("  PASSO 9 — classificação de maturidade")
    print("=" * 55)
    define_maturidade.classificar(atualizar_banco=atualizar_banco)

    print()
    print("[concluído] empresas_uso_ia atualizada")


if __name__ == "__main__":
    atualizar()
