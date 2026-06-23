from __future__ import annotations
import re
from playwright.sync_api import sync_playwright

# Verbos que costumam aparecer logo após o nome da startup no título
VERBOS = [
    'anuncia', 'lança', 'levanta', 'fecha', 'capta', 'recebe',
    'expande', 'estreia', 'vai', 'quer', 'busca', 'aposta',
    'cresce', 'contrata', 'demite', 'projeta', 'prevê',
]

# Tags/setores relevantes do universo de startups
TAGS_RELEVANTES = [
    'startup', 'startups', 'empreendedorismo', 'inovação', 'tecnologia',
    'fintech', 'edtech', 'healthtech', 'agtech', 'proptech', 'insurtech',
    'venture capital', 'vc', 'seed', 'série a', 'série b', 'série c',
    'ipo', 'unicórnio', 'scale-up', 'aceleradora', 'incubadora',
    'esg', 'inteligência artificial', 'ia', 'saas', 'b2b', 'b2c',
]

VERBOS_REGEX = re.compile(r'\b(' + '|'.join(VERBOS) + r')\b', re.IGNORECASE)
NOME_REGEX = re.compile(r'^([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^.,;:!?]+?)(?:\s*,|\s*$)')


VERBOS = [
    'anuncia', 'anunciam', 'lança', 'lançam', 'levanta', 'levantam',
    'fecha', 'fecham', 'capta', 'captam', 'recebe', 'recebem',
    'expande', 'expandem', 'estreia', 'estreiam', 'vai', 'vão',
    'quer', 'querem', 'busca', 'buscam', 'aposta', 'apostam',
    'cresce', 'crescem', 'contrata', 'contratam', 'demite', 'demitem',
    'projeta', 'projetam', 'prevê', 'preveem', 'atrai', 'atraem',
    'avança', 'avançam', 'acelera', 'aceleram', 'prepara', 'preparam',
    'investe', 'investem', 'adquire', 'adquirem', 'compra', 'compram',
    'vende', 'vendem', 'conquista', 'conquistam', 'dispara', 'disparam',
    'registra', 'registram', 'fatura', 'faturam', 'atinge', 'atingem',
    'supera', 'superam', 'fortalece', 'fortalecem', 'reforça', 'reforçam',
    'amplia', 'ampliam', 'abre', 'abrem', 'firma', 'firmam', 'assina',
    'assinam', 'garante', 'garantem', 'mira', 'miram', 'planeja', 'planejam',
    'negocia', 'negociam', 'integra', 'integram', 'consolida', 'consolidam',
    'monta', 'montam', 'estrutura', 'estruturam', 'sai', 'saem', 'chega',
    'chegam', 'entra', 'entram', 'ganha', 'ganham', 'perde', 'perdem',
    'soma', 'somam', 'dobra', 'dobram', 'eleva', 'elevam', 'reduz',
    'reduzem', 'corta', 'cortam',
]

# Palavras que indicam que o título NÃO começa com o nome de uma startup
BLOCKLIST_INICIO = {
    'Na', 'No', 'Em', 'Após', 'Apos', 'O', 'A', 'Os', 'As', 'Um', 'Uma',
    'Por', 'Para', 'Como', 'Quando', 'Se', 'Com', 'Sem', 'Sob', 'Entre',
    'Brasil', 'Sobre', 'Mais', 'Esta', 'Este', 'Estes', 'Estas',
}

VERBOS_REGEX = re.compile(r'\b(' + '|'.join(VERBOS) + r')\b', re.IGNORECASE)
NOME_REGEX = re.compile(r'^([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^.,;:!?]+?)(?:\s*,|\s*$)')


def extrair_nome(titulo: str) -> str | None:
    """Extrai o nome da startup a partir do título do artigo."""
    t = (titulo or '').strip()
    if not t:
        return None

    match_verbo = VERBOS_REGEX.search(t)
    if not match_verbo:
        return None  # sem verbo reconhecido -> não dá pra confiar na extração

    parte = t[:match_verbo.start()].strip()
    if not parte:
        return None

    match = NOME_REGEX.match(parte)
    if not match:
        return None

    nome = match.group(1).strip()
    primeira_palavra = nome.split(' ')[0]
    if primeira_palavra in BLOCKLIST_INICIO:
        return None  # ex: "Na disputa por...", "Brasil sai do..."

    return nome

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://neofeed.com.br/startups/', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_selector('article', timeout=30000)

        # Coleta dados brutos (título + tags) de cada artigo
        artigos = page.eval_on_selector_all(
            'article',
            """(arts) => arts.map((art) => {
                const titulo = art.querySelector('h2, h3')?.innerText?.trim() || '';
                const tags = [...art.querySelectorAll('a[rel="tag"], .tag-links a, .cat-links a')]
                    .map((a) => a.innerText.trim().toLowerCase());
                return { titulo, tags };
            })"""
        )

        browser.close()

    # Processa nome + filtra tags no contexto Python
    resultado = []
    for a in artigos:
        nome = extrair_nome(a['titulo'])
        if not nome:
            continue
        tags = [t for t in a['tags'] if any(r in t for r in TAGS_RELEVANTES)]
        resultado.append({'startup': nome, 'tags': tags})

    # Deduplica por nome
    vistos = set()
    unicos = []
    for r in resultado:
        if r['startup'] in vistos:
            continue
        vistos.add(r['startup'])
        unicos.append(r)

    print(f"\nStartups brasileiras encontradas ({len(unicos)}):\n")
    for i, r in enumerate(unicos, start=1):
        tag_str = f"  [{', '.join(r['tags'])}]" if r['tags'] else ''
        print(f"{i}. {r['startup']}{tag_str}")

    return unicos


if __name__ == '__main__':
    main()