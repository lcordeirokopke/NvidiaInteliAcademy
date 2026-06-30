from __future__ import annotations

"""
Orquestrador do pipeline de recomendação de tecnologias NVIDIA.

Ordem de execução:
  1. verifica_situacao_coleta  — garante que só empresas completas avancem
  2. gerar_queries             — gera query semântica via LLM e salva no banco
  3. buscar_chunks             — embedding + busca Qdrant + reranking
  4. recomendar                — LLM gera justificativas e salva recomendações

Execute com:
  python src/recomendacao/inicia_recomendacao.py
  python src/recomendacao/inicia_recomendacao.py --empresa-id 42
  python src/recomendacao/inicia_recomendacao.py --forcar --passo gerar_queries
"""

import argparse
import logging
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_RAIZ / "src"))

from dotenv import load_dotenv
load_dotenv(_RAIZ / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_PASSOS_DISPONIVEIS = [
    "verifica_situacao_coleta",
    "gerar_queries",
    "buscar_chunks",
    "recomendar",
]


def _separador(titulo: str) -> None:
    print()
    print("=" * 60)
    print(f"  {titulo}")
    print("=" * 60)


def _rodar_passo(nome: str, empresa_id: int | None, forcar: bool) -> bool:
    """Importa e executa um passo do pipeline. Retorna False se o módulo ainda não existe."""
    try:
        import importlib
        modulo = importlib.import_module(f"recomendacao.{nome}")
    except ModuleNotFoundError:
        logger.warning("Passo '%s' ainda não implementado — pulando.", nome)
        return False

    _separador(f"Passo: {nome}")
    modulo.rodar(empresa_id=empresa_id, forcar=forcar)
    return True


def rodar(
    empresa_id: int | None = None,
    forcar: bool = False,
    apenas_passo: str | None = None,
) -> None:
    """
    Executa o pipeline completo ou um passo específico.

    Args:
        empresa_id:   processa só essa empresa se informado.
        forcar:       repassa a flag --forcar para todos os passos.
        apenas_passo: nome de um passo para executar isoladamente.
    """
    if apenas_passo is not None:
        if apenas_passo not in _PASSOS_DISPONIVEIS:
            logger.error(
                "Passo '%s' inválido. Disponíveis: %s",
                apenas_passo, ", ".join(_PASSOS_DISPONIVEIS),
            )
            sys.exit(1)
        _rodar_passo(apenas_passo, empresa_id, forcar)
        return

    logger.info(
        "Iniciando pipeline completo | empresa_id=%s | forcar=%s",
        empresa_id, forcar,
    )

    from recomendacao.verifica_situacao_coleta import verificar

    _separador("Verificação de elegibilidade")
    ids_elegiveis = verificar(empresa_id=empresa_id)

    if not ids_elegiveis:
        logger.warning("Nenhuma empresa elegível — pipeline encerrado.")
        return

    passos = [p for p in _PASSOS_DISPONIVEIS if p != "verifica_situacao_coleta"]
    for nome in passos:
        _rodar_passo(nome, empresa_id, forcar)

    _separador("Pipeline concluído")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Orquestrador do pipeline de recomendação NVIDIA.",
    )
    parser.add_argument(
        "--empresa-id",
        type=int,
        default=None,
        help="Processa só essa empresa.",
    )
    parser.add_argument(
        "--forcar",
        action="store_true",
        help="Reprocessa mesmo que dados já existam no banco.",
    )
    parser.add_argument(
        "--passo",
        choices=_PASSOS_DISPONIVEIS,
        default=None,
        metavar="PASSO",
        help=f"Executa só um passo. Opções: {', '.join(_PASSOS_DISPONIVEIS)}",
    )
    args = parser.parse_args()

    rodar(
        empresa_id=args.empresa_id,
        forcar=args.forcar,
        apenas_passo=args.passo,
    )
