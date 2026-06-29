from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_RAIZ / "src"))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(_RAIZ / ".env")


def _titulo(texto: str) -> None:
    separador = "=" * 60
    print(f"\n{separador}")
    print(f"  {texto}")
    print(separador)


def _inserir_empresa(nome: str) -> None:
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    response = (
        supabase.table("empresas")
        .upsert({"nome": nome}, on_conflict="nome")
        .execute()
    )
    print(f"[banco] empresa '{nome}' inserida/confirmada em 'empresas'")
    return response


def main(nome: str) -> None:
    inicio = time.time()

    _titulo(f"nova_empresa · adicionando: {nome}")
    _inserir_empresa(nome)

    _titulo("1/14 · descobre_dominio.py — descoberta de domínios")
    from dados_startups.descobre_dominio import descobrir as descobrir_dominio
    descobrir_dominio(nome=nome)

    _titulo("2/14 · descobre_gupy.py — descoberta de subdominios Gupy")
    from dados_startups.descobre_gupy import descobrir as descobrir_gupy
    descobrir_gupy(nome=nome)

    _titulo("3/14 · descobre_gupy_vagas.py — vagas de IA no Gupy")
    from dados_ia_startups.descobre_gupy_vagas import pesquisar
    pesquisar(nome=nome)

    _titulo("4/14 · descobre_institucional.py — análise site institucional")
    from dados_ia_startups.descobre_institucional import pesquisar as pesquisar_institucional
    pesquisar_institucional(nome=nome)

    _titulo("5/14 · descobre_imprensa.py — notícias de IA (News API)")
    from dados_ia_startups.descobre_imprensa import pesquisar as pesquisar_imprensa
    pesquisar_imprensa(nome=nome)

    _titulo("6/14 · analisa_neofeed.py — tag ecossistema")
    from dados_ia_startups.analisa_neofeed import classificar as classificar_neofeed
    classificar_neofeed(nome=nome)

    _titulo("7/14 · filtro_ia.py — veredito de uso de IA")
    from dados_ia_startups.filtro_ia import filtrar as filtrar_ia
    filtrar_ia(filtrar_nome=nome)

    _titulo("8/14 · inicia_aprofundamento.py — seed de aprovadas")
    from dados_startups_selecionadas.inicia_aprofundamento import _seed_aprovadas
    _seed_aprovadas(nome=nome)

    _titulo("9/14 · enriquece_identidade.py — CNPJ + BrasilAPI")
    from dados_startups_selecionadas.identidade.enriquece_identidade import enriquecer
    enriquecer(nome=nome)

    _titulo("10/14 · descobre_produto.py — produto principal")
    from dados_startups_selecionadas.outros.descobre_produto import descobrir as descobrir_produto
    descobrir_produto(nome=nome)

    _titulo("11/14 · descobre_uso_ia.py — como usa IA")
    from dados_startups_selecionadas.outros.descobre_uso_ia import descobrir as descobrir_uso_ia
    descobrir_uso_ia(nome=nome)

    _titulo("12/14 · descobre_ia_core_product.py — IA é o core product?")
    from dados_startups_selecionadas.outros.descobre_ia_core_product import descobrir as descobrir_ia_core
    descobrir_ia_core(nome=nome)

    _titulo("13/14 · descobre_modelo_negocio.py — B2B / B2C / B2B2C")
    from dados_startups_selecionadas.outros.descobre_modelo_negocio import descobrir as descobrir_modelo
    descobrir_modelo(nome=nome)

    _titulo("14/14 · define_maturidade.py — score de maturidade")
    from dados_startups_selecionadas.define_maturidade import classificar
    classificar(nome=nome)

    elapsed = time.time() - inicio
    print(f"\n{'=' * 60}")
    print(f"  '{nome}' processada em {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python src/nova_empresa.py \"Nome da Empresa\"")
        sys.exit(1)

    nome_empresa = " ".join(sys.argv[1:])
    main(nome_empresa)
