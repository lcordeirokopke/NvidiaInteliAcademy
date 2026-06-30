"""
Descobre a stack técnica atual de cada startup a partir das vagas Gupy já coletadas.

Estratégia:
  1. Lê data/jsons/gupy_vagas/gupy_vagas_ia.json e agrupa títulos por empresa_id
  2. Envia os títulos ao Gemini para extração de frameworks, cloud, orquestradores, etc.
  3. Grava em data/jsons/empresas_uso_ia/stack_atual.json e atualiza empresas_uso_ia.stack_atual
  4. Lista no terminal as empresas sem vagas Gupy — preencher via atualiza_stack.py

Uso:
    python -m src.dados_startups_selecionadas.outros.stack_atual
    python -m src.dados_startups_selecionadas.outros.stack_atual "Nome da Startup"
    python -m src.dados_startups_selecionadas.outros.stack_atual --dry-run
"""
from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

from src.agents.extrator_stack_gemini import extrair_stack

_RAIZ = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_RAIZ / ".env")

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

_VAGAS_JSON = _RAIZ / "data" / "jsons" / "gupy_vagas" / "gupy_vagas_ia.json"
_SAIDA = _RAIZ / "data" / "jsons" / "empresas_uso_ia" / "stack_atual.json"


def _carregar_titulos_por_empresa() -> dict[int, list[str]]:
    if not _VAGAS_JSON.exists():
        return {}
    vagas = json.loads(_VAGAS_JSON.read_text(encoding="utf-8"))
    agrupado: dict[int, list[str]] = defaultdict(list)
    for v in vagas:
        if v.get("titulo_vaga"):
            agrupado[int(v["empresa_id"])].append(v["titulo_vaga"])
    return dict(agrupado)


def _gravar_json(registros: list[dict]) -> None:
    _SAIDA.parent.mkdir(parents=True, exist_ok=True)

    existentes: dict[int, dict] = {}
    if _SAIDA.exists():
        for reg in json.loads(_SAIDA.read_text(encoding="utf-8")):
            existentes[int(reg["empresa_id"])] = reg

    for reg in registros:
        existentes[int(reg["empresa_id"])] = {
            **reg,
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
        }

    _SAIDA.write_text(
        json.dumps(
            sorted(existentes.values(), key=lambda r: r["empresa_id"]),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[json] {len(registros)} registro(s) salvo(s) em {_SAIDA}")


def descobrir(atualizar_banco: bool = True, nome: str | None = None) -> list[dict]:
    """Para cada empresa sem stack_atual, tenta extrair a stack via vagas Gupy + Gemini."""
    pendentes = (
        supabase.table("empresas_uso_ia")
        .select("empresa_id")
        .is_("stack_atual", "null")
        .not_.is_("cnpj", "null")
        .execute()
        .data
    )

    if not pendentes:
        print("[info] nenhuma empresa pendente de stack_atual")
        return []

    ids = [r["empresa_id"] for r in pendentes]
    nomes_rows = (
        supabase.table("empresas")
        .select("id, nome")
        .in_("id", ids)
        .execute()
        .data
    )
    if nome:
        nomes_rows = [r for r in nomes_rows if r["nome"] == nome]

    titulos_por_empresa = _carregar_titulos_por_empresa()

    print(f"[info] {len(nomes_rows)} empresa(s) sem stack_atual\n")

    atualizacoes: list[dict] = []
    sem_vagas: list[str] = []
    sem_sinal: list[str] = []

    for row in nomes_rows:
        empresa_id = int(row["id"])
        nome_emp = row["nome"]
        titulos = titulos_por_empresa.get(empresa_id, [])

        print(f"  [→] {nome_emp}  ({len(titulos)} vaga(s) Gupy)")

        if not titulos:
            sem_vagas.append(nome_emp)
            continue

        stack = extrair_stack(nome_emp, titulos)

        if stack is None:
            print("       [—] títulos sem sinal de stack suficiente")
            sem_sinal.append(nome_emp)
        else:
            print(f"       [✓] stack extraída: {stack}")
            atualizacoes.append({
                "empresa_id": empresa_id,
                "stack_atual": json.dumps(stack, ensure_ascii=False),
            })

        time.sleep(0.3)

    total_manual = len(sem_vagas) + len(sem_sinal)
    print(f"\n[resumo] {len(atualizacoes)} extraída(s) | {total_manual} para preenchimento manual")

    if sem_vagas:
        print("\n[sem vagas Gupy]:")
        for n in sem_vagas:
            print(f"  - {n}")

    if sem_sinal:
        print("\n[vagas sem sinal de stack]:")
        for n in sem_sinal:
            print(f"  - {n}")

    if total_manual:
        print("\n  → execute para preencher manualmente:")
        print("    python -m src.dados_startups_selecionadas.manual.atualiza_stack")

    if atualizacoes:
        _gravar_json(atualizacoes)

        if atualizar_banco:
            supabase.table("empresas_uso_ia").upsert(
                atualizacoes, on_conflict="empresa_id"
            ).execute()
            print(f"[banco] {len(atualizacoes)} stack_atual atualizado(s) em empresas_uso_ia")

    return atualizacoes


if __name__ == "__main__":
    import sys

    _nome = None
    _apenas_json = "--dry-run" in sys.argv
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            _nome = arg

    descobrir(atualizar_banco=not _apenas_json, nome=_nome)
