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

    _titulo("1/9 · descobre_dominio.py — descoberta de domínios")
    from dados_startups.descobre_dominio import descobrir as descobrir_dominio
    descobrir_dominio()

    _titulo("2/9 · descobre_gupy.py — descoberta de subdominios Gupy")
    from dados_startups.descobre_gupy import descobrir as descobrir_gupy
    descobrir_gupy()

    _titulo("3/9 · descobre_gupy_vagas.py — vagas de IA no Gupy")
    from dados_ia_startups.descobre_gupy_vagas import pesquisar
    pesquisar()

    _titulo("4/9 · descobre_institucional.py — análise site institucional")
    from dados_ia_startups.descobre_institucional import pesquisar as pesquisar_institucional
    pesquisar_institucional()

    _titulo("5/9 · descobre_imprensa.py — notícias de IA (News API)")
    from dados_ia_startups.descobre_imprensa import pesquisar as pesquisar_imprensa
    pesquisar_imprensa()

    _titulo("6/9 · analisa_neofeed.py — tag ecossistema")
    from dados_ia_startups.analisa_neofeed import classificar as classificar_neofeed
    classificar_neofeed()

    _titulo("7/9 · filtro_ia.py — veredito de uso de IA")
    from dados_ia_startups.filtro_ia import filtrar as filtrar_ia
    filtrar_ia()

    _titulo("8/9 · enriquece_identidade.py — CNPJ + BrasilAPI")
    from dados_startups_selecionadas.identidade.enriquece_identidade import enriquecer
    enriquecer()

    _titulo("9/9 · define_maturidade.py — score de maturidade")
    from dados_startups_selecionadas.define_maturidade import classificar
    classificar()

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
