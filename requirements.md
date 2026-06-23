# Dependências do projeto

## Coleta (`src/coleta_startups/coleta.py`)
- **playwright** `1.60.0` — automação de browser para scraping do neofeed.com.br

## Filtragem (`src/coleta_startups/filtro.py`)
- **spacy** `3.8.14` — NER em português (fallback quando a API Gemini falha)
  - modelo: `pt_core_news_sm` (instalar com `python -m spacy download pt_core_news_sm`)

## Extração via LLM (`src/agents/extrator_gemini.py`)
- **google-genai** `2.9.0` — SDK oficial da Gemini API
  - modelo: `gemini-flash-lite-latest`
  - requer `GOOGLE_API_KEY` no `.env`
- **httpx** `0.28.1` — cliente HTTP usado pelo google-genai
- **certifi** `2026.5.20` — bundle de certificados SSL (transitivo do google-genai)

## Instalação

```bash
pip install playwright spacy google-genai
python -m spacy download pt_core_news_sm
playwright install chromium
```

## Notas
- `verify=False` está configurado no cliente httpx do `extrator_gemini.py` para contornar SSL inspection da rede corporativa (Nvidia). Não alterar sem resolver o certificado do proxy.
