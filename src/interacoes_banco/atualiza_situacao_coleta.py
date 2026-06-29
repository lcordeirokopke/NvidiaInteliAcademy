from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

_RAIZ = Path(__file__).resolve().parent.parent.parent
load_dotenv(_RAIZ / ".env")

# Campos obrigatórios para situacao_coleta = 'completo'.
# Excluídos: fonte_dados, programa_aceleracao, gupy_subdominio, nome_fantasia,
#            acelerada_ia (coluna removida), empresa_id, enriquecido_em, situacao_coleta.
CAMPOS_COMPLETO: frozenset[str] = frozenset({
    "cnpj", "cnpj_pendente", "dominio", "razao_social", "situacao_rf",
    "municipio", "uf", "cnae_principal", "porte", "capital_social",
    "natureza_juridica", "produto", "modelo_negocio", "mercado_alvo",
    "setor", "uso_ia_descricao", "ia_e_core_product", "ia_tipo",
    "ano_fundacao", "produto_ia_lancado",
    "score_maturidade_ia", "nivel_maturidade_ia",
})


def atualizar(atualizar_banco: bool = True) -> None:
    """
    Verifica empresas com situacao_coleta = 'informação pendente' e seta
    'completo' para aquelas cujos campos obrigatórios estão todos preenchidos.

    Nunca sobrescreve valores definidos manualmente pelo humano
    ('empresa deve ser ignorada' ou 'seguir para próxima fase apesar de incompleto').
    """
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

    campos_select = ", ".join(CAMPOS_COMPLETO | {"empresa_id", "situacao_coleta"})
    pendentes = (
        supabase.table("empresas_uso_ia")
        .select(campos_select)
        .eq("situacao_coleta", "informação pendente")
        .execute()
        .data
    )

    if not pendentes:
        print("[info] nenhuma empresa pendente para verificação de situacao_coleta")
        return

    completas: list[int] = []
    for emp in pendentes:
        faltando = [c for c in CAMPOS_COMPLETO if emp.get(c) is None]
        if not faltando:
            completas.append(int(emp["empresa_id"]))
        else:
            print(f"  [pendente] id={emp['empresa_id']} — faltando: {', '.join(sorted(faltando))}")

    print(f"\n[situacao_coleta] {len(completas)} completa(s) | {len(pendentes) - len(completas)} pendente(s)")

    if atualizar_banco and completas:
        for eid in completas:
            supabase.table("empresas_uso_ia").update(
                {"situacao_coleta": "completo"}
            ).eq("empresa_id", eid).execute()
        print(f"[banco] {len(completas)} empresa(s) marcada(s) como 'completo'")


if __name__ == "__main__":
    atualizar()
