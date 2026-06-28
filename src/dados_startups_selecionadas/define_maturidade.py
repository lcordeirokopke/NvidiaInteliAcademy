from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

_RAIZ = Path(__file__).resolve().parent.parent.parent
load_dotenv(_RAIZ / ".env")

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

# Campos obrigatórios para classificar — se todos NULL, empresa fica pendente
_CAMPOS_CRITICOS = {"ia_e_core_product", "modelos_proprios", "dados_proprietarios"}

_PESOS: dict[str, float] = {
    "ia_e_core_product":   2.0,
    "modelos_proprios":    1.0,
    "dados_proprietarios": 1.0,
    "produto_ia_lancado":  1.0,
    "acelerada_ia":        0.5,
}


def _score_ano_fundacao(ano: int | None) -> float:
    return 0.5 if ano and ano >= 2020 else 0.0


def _nivel(score: float) -> str:
    if score >= 5:
        return "ai-native"
    if score >= 3:
        return "ai-first"
    if score >= 1:
        return "ai-enabled"
    return "ai-adjacent"


def _calcular(empresa: dict) -> tuple[float, str] | None:
    """Retorna (score, nivel) ou None se dados críticos estiverem todos ausentes."""
    criticos_presentes = any(
        empresa.get(campo) is not None for campo in _CAMPOS_CRITICOS
    )
    if not criticos_presentes:
        return None

    score: float = 0.0
    for campo, peso in _PESOS.items():
        if empresa.get(campo) is True:
            score += peso

    score += _score_ano_fundacao(empresa.get("ano_fundacao"))

    return round(score, 1), _nivel(score)


def classificar(atualizar_banco: bool = True) -> list[dict]:
    empresas = (
        supabase.table("empresas_uso_ia")
        .select(
            "empresa_id, ia_e_core_product, modelos_proprios, dados_proprietarios,"
            " produto_ia_lancado, acelerada_ia, ano_fundacao"
        )
        .execute()
        .data
    )

    nomes_rows = supabase.table("empresas").select("id, nome, dominio, gupy_subdominio").execute().data
    mapa_nomes    = {int(r["id"]): r["nome"]            for r in nomes_rows}
    mapa_dominios = {int(r["id"]): r["dominio"]         for r in nomes_rows}
    mapa_gupy     = {int(r["id"]): r["gupy_subdominio"] for r in nomes_rows}

    print(f"[info] {len(empresas)} empresa(s) carregada(s) para classificação\n")

    atualizacoes: list[dict] = []
    pendentes: list[str] = []

    for emp in empresas:
        empresa_id = int(emp["empresa_id"])
        nome = mapa_nomes.get(empresa_id, f"id={empresa_id}")
        resultado = _calcular(emp)

        if resultado is None:
            print(f"  [{'?':>4}] {nome:<35} ⚠  dados incompletos — classificação pendente")
            pendentes.append(nome)
            continue

        score, nivel = resultado
        print(f"  [{score:>4}] {nome:<35} → {nivel}")
        atualizacoes.append({
            "empresa_id":          empresa_id,
            "dominio":             mapa_dominios.get(empresa_id),
            "gupy_subdominio":     mapa_gupy.get(empresa_id),
            "score_maturidade_ia": score,
            "nivel_maturidade_ia": nivel,
        })

    print(f"\n[resumo] {len(atualizacoes)} classificada(s) | {len(pendentes)} pendente(s)")

    if pendentes:
        print(f"[pendentes] {', '.join(pendentes)}")

    if atualizar_banco and atualizacoes:
        supabase.table("empresas_uso_ia").upsert(
            atualizacoes, on_conflict="empresa_id"
        ).execute()
        print(f"[banco] {len(atualizacoes)} registro(s) atualizado(s) em empresas_uso_ia")

    return atualizacoes


if __name__ == "__main__":
    classificar()
