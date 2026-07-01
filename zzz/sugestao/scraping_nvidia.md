# Scraping NVIDIA — Construção e Fluxo

## Objetivo

Coletar conteúdo de sites NVIDIA e parceiros para alimentar a base de conhecimento vetorial (`nvidia_knowledge` no Qdrant). O RAG resultante permite que o sistema recomende tecnologias NVIDIA adequadas ao perfil de cada startup.

---

## Localização dos scripts

```
src/scraping_nvidia/
├── __init__.py
├── base.py              # ScraperBase: lógica comum a todos os scrapers
├── sites/
│   ├── __init__.py
│   └── <site>.py        # um módulo por site ou grupo de sites
└── run_scraping.py      # orquestrador: executa todos os scrapers em sequência
```

---

## Fluxo de coleta

```
URL(s) de entrada
      │
      ▼
[1] Fetch HTML (httpx / requests)
      │  - respeita robots.txt e rate limit
      │  - trata Cloudflare / JS-rendered com playwright se necessário
      ▼
[2] Extração de texto (BeautifulSoup / trafilatura)
      │  - remove nav, footer, scripts, ads
      │  - mantém título, headings, parágrafos, listas
      ▼
[3] Chunking
      │  - divide por tokens (~400 tok, overlap ~50)
      │  - preserva contexto semântico (não corta no meio de parágrafo)
      ▼
[4] Montagem do documento
      │  { texto, fonte, url, titulo, categoria, tecnologia,
      │    data_coleta, chunk_index }
      ▼
[5] Indexação (src/rag/indexador.py)
      │  - gera embedding via Gemini text-embedding-004
      │  - fallback: paraphrase-multilingual-mpnet-base-v2
      │  - upsert no Qdrant (collection: nvidia_knowledge)
      ▼
Qdrant pronto para consulta pelo buscador
```

---

## Classe base (`base.py`)

`ScraperBase` define a interface e o fluxo padrão. Cada scraper de site herda dela e sobrescreve apenas o que for diferente.

```python
class ScraperBase:
    fonte: str           # domínio, ex: "developer.nvidia.com"
    categoria: str       # produto | conceito | caso_de_uso | inception | stack
    tecnologia: str      # CUDA, NIM, NeMo, RAPIDS, Triton, etc. (ou vazio)

    def urls(self) -> list[str]: ...         # lista de URLs a coletar
    def fetch(self, url) -> str: ...         # retorna HTML bruto
    def extrair_texto(self, html) -> dict:   # retorna {titulo, texto}
    def chunkar(self, texto) -> list[str]:   # divide em chunks
    def run(self): ...                       # orquestra fetch→chunk→indexar
```

---

## Metadata indexada no Qdrant

### Estrutura completa

```json
{
  "url": "https://developer.nvidia.com/tensorrt",
  "fonte": "developer.nvidia.com",
  "titulo": "TensorRT — Otimização de Inferência",
  "categoria": "produto",
  "familia": "inferencia",
  "tecnologia": "TensorRT",
  "setores": ["saude", "industria", "geral"],
  "ia_tipos": ["visão computacional", "classificacao"],
  "data_coleta": "2026-06-29",
  "doc_id": "uuid",
  "chunk_index": 0,
  "chunk_total": 3
}
```

### Campos

#### Identificação e rastreabilidade

| Campo | Tipo | Descrição |
|---|---|---|
| `url` | str | URL exata da página coletada |
| `fonte` | str | Domínio de origem |
| `titulo` | str | Título da página ou seção |
| `data_coleta` | str | Data ISO da coleta — controla reindexação |

#### Classificação do conteúdo

| Campo | Tipo | Valores possíveis |
|---|---|---|
| `categoria` | str | `produto`, `conceito`, `caso_de_uso`, `inception`, `stack` |
| `familia` | str | `inferencia`, `treinamento`, `dados`, `deployment`, `plataforma` |
| `tecnologia` | str | `NIM`, `NeMo`, `TensorRT`, `RAPIDS`, `CUDA`, `Triton`, `cuDF`, `cuML`, `TensorRT-LLM`, `GPU Operator`, `DGX`, `NGC`, `AI Enterprise` |

#### Alinhamento com o perfil da startup

| Campo | Tipo | Descrição |
|---|---|---|
| `setores` | list[str] | Setores para os quais o chunk é relevante |
| `ia_tipos` | list[str] | Tipos de IA abordados no chunk |

#### Navegação no documento

| Campo | Tipo | Descrição |
|---|---|---|
| `doc_id` | str | UUID compartilhado por todos os chunks da mesma página |
| `chunk_index` | int | Posição do chunk dentro do documento |
| `chunk_total` | int | Total de chunks do documento |

### Valores controlados

**`familia`**

| Valor | Tecnologias associadas |
|---|---|
| `inferencia` | TensorRT, TensorRT-LLM, Triton, NIM |
| `treinamento` | NeMo, CUDA, cuDNN |
| `dados` | RAPIDS, cuDF, cuML |
| `deployment` | NIM, GPU Operator |
| `plataforma` | DGX, NGC, AI Enterprise |

**`setores`**: `saude`, `financas`, `agro`, `varejo`, `industria`, `educacao`, `energia`, `logistica`, `geral`

> `geral` é usado quando o conteúdo é relevante para qualquer setor.

**`ia_tipos`**: `visão computacional`, `NLP`, `LLM`, `recomendacao`, `series temporais`, `deteccao de anomalias`, `classificacao`, `geracao de conteudo`, `busca semantica`

### Cruzamento com o perfil da startup

| Campo do perfil | Campo da metadata | Tipo de uso |
|---|---|---|
| `setor` | `setores` | filtro `$in` |
| `ia_tipo` | `ia_tipos` | filtro `$in` |
| `produto` | — | ancora a busca semântica |
| `maturidade` | — | usado pelo Gemini na argumentação |
| `ia_core_product` | `categoria` | se true, prioriza `produto` e `stack`; se false, prioriza `caso_de_uso` |

---

## Orquestrador (`run_scraping.py`)

Importa todos os scrapers registrados e executa em sequência (ou paralelo com `asyncio`). Ao final, loga quantos documentos foram indexados por site e categoria.

---

## Integração com o RAG existente

O scraper chama diretamente `src.rag.indexador.indexar_documento(texto, metadata)` — sem acoplamento adicional. O Qdrant e o embedding já estão configurados em `src/rag/`.

Para consultar o conhecimento coletado, usar `src.rag.buscador` normalmente.

---

## Categorias de conteúdo

| Categoria      | Exemplos de conteúdo                                     |
|----------------|----------------------------------------------------------|
| `produto`      | fichas técnicas, documentação de produtos NVIDIA          |
| `conceito`     | o que é GPU computing, inferência, fine-tuning, etc.     |
| `caso_de_uso`  | cases de startups, histórias de clientes, benchmarks     |
| `inception`    | programa NVIDIA Inception, benefícios, como participar   |
| `stack`        | NIM, NeMo, RAPIDS, Triton, CUDA, cuDF, TensorRT, etc.   |
