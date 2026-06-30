# Dependências do projeto

## Coleta (`src/coleta_startups/coleta_neofeed.py`)
- **playwright** `1.60.0` — automação de browser para scraping do neofeed.com.br

## Filtragem (`src/coleta_startups/filtro.py`)
- **spacy** `3.8.14` — NER em português (fallback quando a API Gemini falha)
  - modelo: `pt_core_news_sm` (instalar com `python -m spacy download pt_core_news_sm`)
- **click** `8.4.2` — dependência do spacy para CLI (instalar separadamente se faltar)

## Extração via LLM (`src/agents/extrator_gemini.py`)
- **google-genai** `2.9.0` — SDK oficial da Gemini API
  - modelo: `gemini-flash-lite-latest`
  - requer `GOOGLE_API_KEY` no `.env`
- **httpx** `0.28.1` — cliente HTTP usado pelo google-genai
- **certifi** `2026.5.20` — bundle de certificados SSL (transitivo do google-genai)

## Banco de dados / uploads (`src/interacoes_banco/`, `src/dados_startups/`, `src/dados_ia_startups/`)
- **supabase** `2.31.0` — cliente Python do Supabase
  - requer `SUPABASE_URL` e `SUPABASE_KEY` no `.env`
- **python-dotenv** `1.2.2` — leitura do arquivo `.env`
- **requests** `2.34.2` — requisições HTTP para descoberta de domínios e Gupy

## Imprensa — fallback (`src/dados_ia_startups/fallback/newsdata_io.py`)
- **requests** — já listado acima; reutilizado aqui para chamar `newsdata.io`
  - requer `NEWS_DATA_KEY` no `.env` (chave do [newsdata.io](https://newsdata.io))
  - acionado automaticamente quando `newsapi.org` retorna erro ou limite esgotado

## RAG (`src/rag/`)
- **qdrant-client** — cliente do Qdrant para armazenamento e busca vetorial
  - requer Qdrant rodando em `http://localhost:6333`
- **google-genai** — já listado acima; reutilizado para embedding via `text-embedding-004`
  - requer `GEMINI_API_KEY2` no `.env`
- **sentence-transformers** — fallback local de embedding (`paraphrase-multilingual-mpnet-base-v2`)

## Scraping NVIDIA (`src/scraping_nvidia/`)
- **trafilatura** — extração de conteúdo principal de páginas web (remove nav, footer, ads automaticamente)
- **tiktoken** — contagem e divisão por tokens reais (`cl100k_base`); chunks de 400 tokens com overlap de 50
- **httpx** — já listado acima; reutilizado para fetch de páginas
- **playwright** — já listado acima; usado apenas para sites que renderizam conteúdo via JavaScript

## Instalação

```bash
pip install playwright spacy click google-genai supabase python-dotenv requests qdrant-client sentence-transformers trafilatura tiktoken
python -m spacy download pt_core_news_sm
playwright install chromium
```

## Notas
- `verify=False` está configurado no cliente httpx do `extrator_gemini.py` para contornar SSL inspection da rede corporativa (Nvidia). Não alterar sem resolver o certificado do proxy.
