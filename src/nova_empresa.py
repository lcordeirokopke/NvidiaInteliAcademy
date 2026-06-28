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

    _titulo("1/4 · upload_empresas.py — upload para Supabase")
    from interacoes_banco.upload_empresas import upload as upload_empresas
    upload_empresas()

    _titulo("2/4 · descobre_dominio.py — descoberta de domínios")
    from dados_startups.descobre_dominio import descobrir as descobrir_dominio
    descobrir_dominio()

    _titulo("3/4 · descobre_gupy.py — descoberta de subdominios Gupy")
    from dados_startups.descobre_gupy import descobrir as descobrir_gupy
    descobrir_gupy()

    _titulo("4/4 · descobre_gupy_vagas.py — vagas de IA no Gupy")
    from dados_ia_startups.descobre_gupy_vagas import pesquisar
    pesquisar()

    elapsed = time.time() - inicio
    print(f"\n{'=' * 60}")
    print(f"  Fluxo completo em {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
