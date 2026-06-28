from __future__ import annotations

import re

# (padrão de código CNAE, setor startup)
_MAPA: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^86"),             "healthtech"),
    (re.compile(r"^(64|65|66)"),     "fintech"),
    (re.compile(r"^85"),             "edtech"),
    (re.compile(r"^(49|52|53)"),     "logtech"),
    (re.compile(r"^(47|45|46)"),     "retailtech"),
    (re.compile(r"^(55|56|79)"),     "traveltech"),
    (re.compile(r"^(41|42|43|68)"),  "proptech"),
    (re.compile(r"^(01|02|03|10|11)"), "agritech"),
    (re.compile(r"^(35|36|37|38|39)"), "cleantech"),
    (re.compile(r"^(62|63|72|95)"),  "deeptech"),
]
_DEFAULT = "tech"


def inferir(atividades: list[dict]) -> str:
    """Recebe a lista de atividades da BrasilAPI e retorna o setor startup."""
    for atividade in atividades:
        codigo = re.sub(r"\D", "", str(atividade.get("codigo", "")))
        for padrao, setor in _MAPA:
            if padrao.match(codigo):
                return setor
    return _DEFAULT
