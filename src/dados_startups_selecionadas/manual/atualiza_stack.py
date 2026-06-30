"""
Preenchimento manual de stack_atual para empresas sem vagas Gupy ou sem sinal extraível.

Uso:
    python -m src.dados_startups_selecionadas.manual.atualiza_stack

Exibe a lista de empresas com stack_atual nulo.
O operador digita a stack (ex: PyTorch, AWS, Kubernetes) e o script grava no Supabase.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

_RAIZ = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_RAIZ / ".env")

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def _carregar_pendentes() -> list[dict]:
    pendentes = (
        supabase.table("empresas_uso_ia")
        .select("empresa_id")
        .is_("stack_atual", "null")
        .execute()
        .data
    )
    if not pendentes:
        return []

    ids = [r["empresa_id"] for r in pendentes]
    nomes_rows = (
        supabase.table("empresas")
        .select("id, nome")
        .in_("id", ids)
        .execute()
        .data
    )
    return sorted(nomes_rows, key=lambda r: r["nome"])


def _exibir_lista(empresas: list[dict]) -> None:
    print(f"\nEmpresas sem stack_atual ({len(empresas)}):")
    print("-" * 55)
    for i, emp in enumerate(empresas, 1):
        print(f"  {i:>3}. {emp['nome']}")
    print("-" * 55)


def _ler_escolha(empresas: list[dict]) -> dict | None:
    while True:
        raw = input("\nNúmero da empresa (ou 'q' para sair): ").strip()
        if raw.lower() in ("q", "sair", ""):
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(empresas):
            return empresas[int(raw) - 1]
        print(f"  [erro] escolha um número entre 1 e {len(empresas)}")


def _ler_stack() -> dict | None:
    """Lê a stack digitada pelo operador e devolve dict estruturado."""
    print()
    print("  Informe os itens da stack separados por vírgula.")
    print("  Ex: PyTorch, AWS, Kubernetes, Python, MLflow")
    raw = input("  Stack: ").strip()

    if not raw:
        return None

    itens = [s.strip() for s in raw.replace(";", ",").split(",") if s.strip()]
    if not itens:
        return None

    # Categorização simples por palavras-chave conhecidas
    _CLOUD = {"aws", "gcp", "azure", "google cloud", "oracle cloud"}
    _ORQUESTRADOR = {"kubernetes", "docker", "k8s", "helm", "airflow"}
    _MLOPS = {"mlflow", "kubeflow", "sagemaker", "vertex ai", "databricks", "wandb", "dvc"}
    _FRAMEWORKS = {"pytorch", "tensorflow", "keras", "jax", "sklearn", "scikit-learn",
                   "hugging face", "transformers", "langchain", "llamaindex"}
    _LINGUAGENS = {"python", "go", "java", "scala", "rust", "typescript", "javascript", "r"}

    categorizado: dict[str, list[str]] = {
        "frameworks_ml": [], "linguagens": [], "cloud": [],
        "orquestradores": [], "mlops": [], "outros": [],
    }

    for item in itens:
        lower = item.lower()
        if lower in _FRAMEWORKS:
            categorizado["frameworks_ml"].append(item)
        elif lower in _LINGUAGENS:
            categorizado["linguagens"].append(item)
        elif lower in _CLOUD:
            categorizado["cloud"].append(item)
        elif lower in _ORQUESTRADOR:
            categorizado["orquestradores"].append(item)
        elif lower in _MLOPS:
            categorizado["mlops"].append(item)
        else:
            categorizado["outros"].append(item)

    return {k: v for k, v in categorizado.items() if v}


def atualizar() -> None:
    print("=" * 55)
    print("  Preenchimento manual de stack_atual")
    print("=" * 55)

    while True:
        empresas = _carregar_pendentes()

        if not empresas:
            print("\n[info] nenhuma empresa com stack_atual nulo. Encerrando.")
            break

        _exibir_lista(empresas)

        emp = _ler_escolha(empresas)
        if emp is None:
            print("[info] saindo.")
            break

        print(f"\n  Empresa: {emp['nome']}  (id={emp['id']})")

        stack = _ler_stack()
        if stack is None:
            print("  [cancelado] voltando à lista.\n")
            continue

        stack_json = json.dumps(stack, ensure_ascii=False)
        confirma = input(f"\n  Gravar {stack_json} para '{emp['nome']}'? (s/n): ").strip().lower()
        if confirma != "s":
            print("  [cancelado] voltando à lista.\n")
            continue

        supabase.table("empresas_uso_ia").update(
            {"stack_atual": stack_json}
        ).eq("empresa_id", emp["id"]).execute()
        print(f"  [banco] stack_atual gravado para '{emp['nome']}'\n")


if __name__ == "__main__":
    atualizar()
