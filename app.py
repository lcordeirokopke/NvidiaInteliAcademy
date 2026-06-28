from __future__ import annotations

import sys
import time
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(_RAIZ / "src"))


def _titulo(texto: str) -> None:
    separador = "=" * 60
    print(f"\n{separador}")
    print(f"  {texto}")
    print(separador)


def main() -> None:
    inicio = time.time()

    # 1. Coleta artigos brutos do Neofeed
    _titulo("1/12 · coleta_neofeed.py — raspagem Neofeed")
    from coleta_startups.coleta_neofeed import coletar
    coletar()

    # 2. Filtra e extrai nomes de startups
    _titulo("2/12 · filtro.py — extração de nomes")
    from coleta_startups.filtro import filtrar
    filtrar()

    # 3. Envia nomes brutos para Supabase (tabela nomes_empresas)
    _titulo("3/12 · upload_nomes_empresas.py — upload para Supabase")
    from interacoes_banco.upload_nomes_empresas import upload as upload_nomes
    upload_nomes()

    # 4. Envia empresas para Supabase (tabela empresas) — deve vir antes das descobertas
    _titulo("4/12 · upload_empresas.py — upload para Supabase")
    from interacoes_banco.upload_empresas import upload as upload_empresas
    upload_empresas()

    # 5. Descobre domínio de cada empresa
    _titulo("5/12 · descobre_dominio.py — descoberta de domínios")
    from dados_startups.descobre_dominio import descobrir as descobrir_dominio
    descobrir_dominio()

    # 6. Descobre subdomínio Gupy de cada empresa
    _titulo("6/12 · descobre_gupy.py — descoberta de subdominios Gupy")
    from dados_startups.descobre_gupy import descobrir as descobrir_gupy
    descobrir_gupy()

    # 7. Pesquisa vagas de IA no Gupy
    _titulo("7/12 · descobre_gupy_vagas.py — vagas de IA no Gupy")
    from dados_ia_startups.descobre_gupy_vagas import pesquisar
    pesquisar()

    # 8. Analisa site institucional de cada empresa
    _titulo("9/12 · descobre_institucional.py — análise site institucional")
    from dados_ia_startups.descobre_institucional import pesquisar as pesquisar_institucional
    pesquisar_institucional()

    # 10. Pesquisa notícias de IA na News API
    _titulo("10/12 · descobre_imprensa.py — notícias de IA (News API)")
    from dados_ia_startups.descobre_imprensa import pesquisar as pesquisar_imprensa
    pesquisar_imprensa()

    # 11. Classifica artigos Neofeed como ecossistema de IA
    _titulo("11/12 · analisa_neofeed.py — tag ecossistema")
    from dados_ia_startups.analisa_neofeed import classificar
    classificar()

    elapsed = time.time() - inicio
    print(f"\n{'=' * 60}")
    print(f"  Fluxo completo em {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
