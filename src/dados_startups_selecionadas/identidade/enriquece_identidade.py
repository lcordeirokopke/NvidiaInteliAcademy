from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

from . import brasil_api, cnae_setor
from . import cnpj as cnpj_mod

_RAIZ = Path(__file__).resolve().parent.parent.parent
load_dotenv(_RAIZ / ".env")

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def enriquecer(atualizar_banco: bool = True) -> list[dict]:
    registros = (
        supabase.table("empresas_uso_ia")
        .select("empresa_id, cnpj")
        .is_("cnpj", "null")
        .execute()
        .data
    )

    if not registros:
        print("[info] nenhuma empresa pendente de enriquecimento de identidade")
        return []

    ids = [r["empresa_id"] for r in registros]

    dominios_rows = (
        supabase.table("empresas")
        .select("id, nome, dominio")
        .in_("id", ids)
        .execute()
        .data
    )
    mapa = {int(r["id"]): r for r in dominios_rows}

    print(f"[info] {len(ids)} empresa(s) para enriquecer\n")

    atualizacoes: list[dict] = []
    sem_dominio: list[str] = []
    sem_cnpj: list[str] = []

    for empresa_id in ids:
        info = mapa.get(empresa_id)
        if not info:
            continue

        nome    = info.get("nome", f"id={empresa_id}")
        dominio = info.get("dominio")

        if not dominio:
            print(f"  [skip] {nome} — sem domínio cadastrado")
            sem_dominio.append(nome)
            continue

        print(f"  [→] {nome}  ({dominio})")

        cnpj = cnpj_mod.obter(dominio, nome=nome)
        if not cnpj:
            print(f"       [✗] CNPJ não encontrado (site + minhareceita)")
            sem_cnpj.append(nome)
            time.sleep(0.5)
            continue

        print(f"       [cnpj] {cnpj_mod.formatar(cnpj)}")

        time.sleep(0.3)
        dados = brasil_api.consultar_cnpj(cnpj)
        if not dados:
            atualizacoes.append({"empresa_id": empresa_id, "cnpj": cnpj})
            continue

        situacao = brasil_api.situacao(dados)
        if situacao not in ("", "ATIVA"):
            print(f"       [aviso] situação cadastral: {situacao}")

        atividades = brasil_api.atividades_principais(dados)
        setor   = cnae_setor.inferir(atividades)
        produto = brasil_api.nome_empresa(dados)

        print(f"       [setor] {setor}  |  [produto] {produto[:50]}")
        atualizacoes.append({
            "empresa_id": empresa_id,
            "cnpj":    cnpj,
            "produto": produto,
            "setor":   setor,
        })

        time.sleep(0.5)

    print(
        f"\n[resumo] {len(atualizacoes)} enriquecida(s) | "
        f"{len(sem_cnpj)} sem CNPJ | {len(sem_dominio)} sem domínio"
    )

    if atualizar_banco and atualizacoes:
        supabase.table("empresas_uso_ia").upsert(
            atualizacoes, on_conflict="empresa_id"
        ).execute()
        print(f"[banco] {len(atualizacoes)} registro(s) atualizado(s) em empresas_uso_ia")

    return atualizacoes


if __name__ == "__main__":
    enriquecer()
