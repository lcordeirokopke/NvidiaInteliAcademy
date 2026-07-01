# Prompt — Criação de Scraper para Site NVIDIA

> Copie o bloco abaixo e substitua `{URL}` pela URL desejada antes de enviar ao Claude Code.

---

```
## Contexto do projeto

Estou desenvolvendo um sistema que analisa o perfil de startups brasileiras e recomenda tecnologias NVIDIA adequadas ao seu contexto. O sistema já coleta automaticamente os seguintes campos de cada startup:

- setor (ex: saude, financas, agro, varejo, industria)
- produto (descrição do produto principal)
- ia_tipo (ex: visão computacional, NLP, LLM, classificacao)
- maturidade (ex: MVP, escala)
- ia_core_product (bool)

## Fluxo de recomendação

1. O agente recebe o perfil da startup
2. Monta uma query semântica combinando os campos do perfil
3. Busca no Qdrant os chunks mais relevantes usando busca vetorial + filtros por metadata
4. Passa os chunks recuperados como contexto para o Gemini
5. O Gemini gera a recomendação de tecnologias NVIDIA fundamentada nos chunks

O scraper alimenta o passo 3 — é a fonte de conhecimento sobre tecnologias NVIDIA.

## Infraestrutura de RAG existente

**Qdrant** rodando em `http://localhost:6333`, collection `nvidia_knowledge`, embeddings de 768 dimensões.

**Embedding** via `src/rag/embedding.py` → `gerar_embedding(texto: str) -> list[float]`
Usa Gemini `text-embedding-004` com fallback `paraphrase-multilingual-mpnet-base-v2`.

**Indexação** via `src/rag/indexador.py` → `indexar_documento(texto: str, metadata: dict) -> str`
Gera o embedding e faz upsert no Qdrant. Retorna o ID gerado.

**Busca** via `src/rag/buscador.py` → `buscar(query: str, filtros: dict | None, top_k: int) -> list[dict]`
Suporta filtros Qdrant com `$in` para campos lista.

## Estrutura de metadata obrigatória

Cada documento indexado deve ter exatamente estes campos:

```json
{
  "url": "https://...",           // URL exata da página
  "fonte": "developer.nvidia.com", // domínio de origem
  "titulo": "...",                // título da página ou seção
  "categoria": "produto",         // produto | conceito | caso_de_uso | inception | stack
  "familia": "inferencia",        // inferencia | treinamento | dados | deployment | plataforma
  "tecnologia": "TensorRT",       // nome exato da tecnologia NVIDIA
  "setores": ["saude", "geral"],  // lista — setores para os quais o chunk é relevante
  "ia_tipos": ["visão computacional"], // lista — tipos de IA abordados
  "data_coleta": "YYYY-MM-DD",    // data ISO da coleta
  "doc_id": "uuid",               // mesmo UUID para todos os chunks da página
  "chunk_index": 0,               // posição do chunk
  "chunk_total": 3                // total de chunks da página
}
```

**Valores controlados:**

- `categoria`: `produto`, `conceito`, `caso_de_uso`, `inception`, `stack`
- `familia`: `inferencia`, `treinamento`, `dados`, `deployment`, `plataforma`
- `setores`: `saude`, `financas`, `agro`, `varejo`, `industria`, `educacao`, `energia`, `logistica`, `geral`
- `ia_tipos`: `visão computacional`, `NLP`, `LLM`, `recomendacao`, `series temporais`, `deteccao de anomalias`, `classificacao`, `geracao de conteudo`, `busca semantica`

Mapeamento de famílias:
- `inferencia` → TensorRT, TensorRT-LLM, Triton, NIM
- `treinamento` → NeMo, CUDA, cuDNN
- `dados` → RAPIDS, cuDF, cuML
- `deployment` → NIM, GPU Operator
- `plataforma` → DGX, NGC, AI Enterprise

## Estrutura de arquivos do scraping

```
src/scraping_nvidia/
├── __init__.py
├── base.py              # ScraperBase — classe base (pode ainda não existir, crie se necessário)
├── sites/
│   ├── __init__.py
│   └── <nome_site>.py   # um arquivo por site
└── run_scraping.py      # orquestrador (pode ainda não existir)
```

## Stack tecnológica obrigatória

Use exatamente estas bibliotecas em cada etapa:

| Etapa | Biblioteca | Função |
|---|---|---|
| Fetch | `httpx` | requisições HTTP; já está no projeto |
| Fetch JS | `playwright` | apenas se o site renderizar conteúdo via JavaScript |
| Extração | `trafilatura` | extrai o conteúdo principal da página, remove nav/footer/ads automaticamente |
| Chunking | `tiktoken` | divide o texto em chunks de tokens reais, garante respeito ao limite do embedding |

Parâmetros de chunking:
- Encoding: `cl100k_base`
- Tamanho do chunk: 400 tokens
- Overlap entre chunks: 50 tokens
- Nunca cortar no meio de uma frase

## Tarefa

Acesse o site abaixo, analise o conteúdo disponível e crie um scraper em `src/scraping_nvidia/sites/` que:

1. Colete todas as páginas relevantes sobre tecnologias NVIDIA disponíveis neste site
2. Extraia o texto limpo com `trafilatura` (sem nav, footer, scripts, banners)
3. Divida o conteúdo em chunks com `tiktoken` (400 tokens, overlap 50)
4. Classifique corretamente cada chunk nos campos de metadata (`categoria`, `familia`, `tecnologia`, `setores`, `ia_tipos`) com base no conteúdo real da página
5. Indexe cada chunk via `src.rag.indexador.indexar_documento(texto, metadata)`
6. Se a classe `ScraperBase` em `src/scraping_nvidia/base.py` ainda não existir, crie-a antes de criar o scraper do site

O scraper deve ser robusto: tratar erros de rede, respeitar rate limit com delay de 1s entre requests, evitar reindexar URLs já processadas na mesma execução.

**Site:** {URL}
```
