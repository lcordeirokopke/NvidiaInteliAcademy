import sys
sys.path.insert(0, ".")
from src.dados_ia_startups.descobre_institucional import _buscar_pagina_playwright, _extrair_texto
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    html = _buscar_pagina_playwright("https://idwall.com", page, debug=True)
    browser.close()

if html:
    texto = _extrair_texto(html)
    print(f"\n[chars extraídos: {len(texto)}]")
    print(texto[:2000])
else:
    print("[falhou]")
