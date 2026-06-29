from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_RAIZ))          # permite: from src.agents...
sys.path.insert(0, str(_RAIZ / "src"))  # permite: from dados_startups...

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

    _titulo("1/16 · descobre_dominio.py — descoberta de domínios")
    from dados_startups.descobre_dominio import descobrir as descobrir_dominio
    descobrir_dominio(nome=nome)

    _titulo("2/16 · descobre_gupy.py — descoberta de subdominios Gupy")
    from dados_startups.descobre_gupy import descobrir as descobrir_gupy
    descobrir_gupy(nome=nome)

    _titulo("3/16 · descobre_gupy_vagas.py — vagas de IA no Gupy")
    from dados_ia_startups.descobre_gupy_vagas import pesquisar
    pesquisar(nome=nome)

    _titulo("4/16 · descobre_institucional.py — análise site institucional")
    from dados_ia_startups.descobre_institucional import pesquisar as pesquisar_institucional
    pesquisar_institucional(nome=nome)

    _titulo("5/16 · descobre_imprensa.py — notícias de IA (News API)")
    from dados_ia_startups.descobre_imprensa import pesquisar as pesquisar_imprensa
    pesquisar_imprensa(nome=nome)

    _titulo("6/16 · analisa_neofeed.py — tag ecossistema")
    from dados_ia_startups.analisa_neofeed import classificar as classificar_neofeed
    classificar_neofeed(nome=nome)

    _titulo("7/16 · filtro_ia.py — veredito de uso de IA")
    from dados_ia_startups.filtro_ia import filtrar as filtrar_ia
    filtrar_ia(filtrar_nome=nome)

    _titulo("8/16 · inicia_aprofundamento.py — seed de aprovadas")
    from dados_startups_selecionadas.inicia_aprofundamento import _seed_aprovadas
    _seed_aprovadas(nome=nome)

    _titulo("9/16 · enriquece_identidade.py — CNPJ + BrasilAPI")
    from dados_startups_selecionadas.identidade.enriquece_identidade import enriquecer
    enriquecer(nome=nome)

    _titulo("10/16 · produto.py — produto principal")
    from dados_startups_selecionadas.outros.produto import descobrir as descobrir_produto
    descobrir_produto(nome=nome)

    _titulo("11/16 · uso_ia.py — como usa IA")
    from dados_startups_selecionadas.outros.uso_ia import descobrir as descobrir_uso_ia
    descobrir_uso_ia(nome=nome)

    _titulo("12/16 · ia_core_product.py — IA é o core product?")
    from dados_startups_selecionadas.outros.ia_core_product import descobrir as descobrir_ia_core
    descobrir_ia_core(nome=nome)

    _titulo("13/16 · modelo_negocio.py — B2B / B2C / B2B2C")
    from dados_startups_selecionadas.outros.modelo_negocio import descobrir as descobrir_modelo
    descobrir_modelo(nome=nome)

    _titulo("14/16 · produto_ia_lancado.py — produto já lançado?")
    from dados_startups_selecionadas.outros.produto_ia_lancado import descobrir as descobrir_produto_lancado
    descobrir_produto_lancado(nome=nome)

    _titulo("15/16 · define_setor.py — setor de atuação")
    from dados_startups_selecionadas.outros.define_setor import descobrir as descobrir_setor
    descobrir_setor(nome=nome)

    _titulo("16/18 · mercado_alvo.py — mercado-alvo geográfico")
    from dados_startups_selecionadas.outros.mercado_alvo import descobrir as descobrir_mercado_alvo
    descobrir_mercado_alvo(nome=nome)

    _titulo("17/18 · acelerada_ia.py — programas de aceleração")
    from dados_startups_selecionadas.outros.acelerada_ia import descobrir as descobrir_aceleradoras
    descobrir_aceleradoras(nome=nome)

    _titulo("18/18 · define_maturidade.py — score e nível de maturidade")
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
