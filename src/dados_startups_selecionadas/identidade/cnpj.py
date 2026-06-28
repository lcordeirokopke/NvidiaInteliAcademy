from __future__ import annotations

import re
import urllib.parse

import requests

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = "Mozilla/5.0 (compatible; pesquisa-academica/1.0)"

_RE_CNPJ = re.compile(
    r"\b(\d{2})[.\s]?(\d{3})[.\s]?(\d{3})[/\\]?(\d{4})[-.]?(\d{2})\b"
)

_MINHARECEITA_SEARCH = "https://minhareceita.org/?q={}"


def _validar(cnpj: str) -> bool:
    return len(cnpj) == 14 and len(set(cnpj)) > 1


def extrair_do_site(dominio: str, timeout: int = 8) -> str | None:
    """Raspa o HTML do domínio e retorna o primeiro CNPJ encontrado (somente dígitos)."""
    for schema in ("https://", "http://"):
        try:
            r = _SESSION.get(f"{schema}{dominio}", timeout=timeout, allow_redirects=True)
            if r.status_code != 200:
                continue
            match = _RE_CNPJ.search(r.text)
            if match:
                cnpj = "".join(match.groups())
                if _validar(cnpj):
                    return cnpj
        except requests.RequestException:
            continue
    return None


def buscar_minhareceita(nome_ou_dominio: str, timeout: int = 10) -> str | None:
    """Busca CNPJ no minhareceita.org por nome ou domínio (scraping limitado)."""
    query = urllib.parse.quote_plus(nome_ou_dominio)
    try:
        r = _SESSION.get(_MINHARECEITA_SEARCH.format(query), timeout=timeout)
        if r.status_code != 200:
            return None
        match = _RE_CNPJ.search(r.text)
        if match:
            cnpj = "".join(match.groups())
            if _validar(cnpj):
                return cnpj
    except requests.RequestException:
        pass
    return None


def obter(dominio: str, nome: str | None = None, timeout: int = 8) -> str | None:
    """
    1. Regex no HTML do próprio domínio.
    2. Fallback: minhareceita.org buscando por nome (ou domínio se nome ausente).
    """
    cnpj = extrair_do_site(dominio, timeout=timeout)
    if cnpj:
        return cnpj
    return buscar_minhareceita(nome or dominio, timeout=timeout + 2)


def formatar(cnpj: str) -> str:
    """XX.XXX.XXX/XXXX-XX"""
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
