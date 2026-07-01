# Briefing do Projeto — Para Leitura por IA

Este documento descreve o estado atual de um sistema que recomenda tecnologias NVIDIA para startups brasileiras. Use-o como contexto completo antes de receber qualquer tarefa relacionada ao projeto.

---

## O que o sistema faz

Recebe o perfil de uma startup brasileira já coletado em banco de dados e gera uma recomendação fundamentada de quais tecnologias NVIDIA são mais adequadas ao contexto dela. A recomendação não é feita por um agente que "decide" — é feita por um pipeline RAG com reranking que seleciona os chunks mais relevantes, e um agente de explicação (Gemini) que articula em linguagem natural por que cada tecnologia foi selecionada.

---

## Perfil de startup disponível

Cada startup no banco possui os seguintes campos relevantes para recomendação:

| Campo | Exemplos |
|---|---|
| `setor` | saude, financas, agro, varejo, industria, educacao, energia, logistica |
| `produto` | descrição textual do produto principal |
| `ia_tipo` | visão computacional, NLP, LLM, classificacao, recomendacao, etc. |
| `maturidade` | MVP, escala |
| `ia_core_product` | true / false |

---

## Fluxo de recomendação (ponta a ponta)

```
PERFIL DA STARTUP
      │
      ▼
MONTAGEM DA QUERY SEMÂNTICA
Combina setor + produto + ia_tipo + maturidade em uma frase de busca natural.
Ex: "startup de saúde com visão computacional em MVP, precisa de inferência de modelos de imagem"
      │
      ▼
BUSCA VETORIAL NO QDRANT  (src/rag/buscador.py)
Recupera top_k * 3 candidatos (ex: 15 chunks) por similaridade de cosseno.
Filtros aplicados automaticamente:
  - setor: {"$in": [setor_da_startup, "geral"]}
  - categoria: {"$in": ["produto", "caso_de_uso", "stack", "inception"]}
      │
      ▼
RERANKING  (src/rag/reranker.py — a criar)
Cross-encoder ms-marco-MiniLM-L-6-v2 lê query + chunk com atenção cruzada.
Reordena os 15 candidatos e trunca para top_k (ex: 5).
A seleção final das tecnologias acontece aqui.
      │
      ▼
AGENTE DE EXPLICAÇÃO  (src/agents/ — a criar)
Recebe perfil da startup + top chunks reranqueados.
Não decide tecnologias — apenas justifica as que chegaram.
Consolida múltiplos chunks da mesma tecnologia em uma única justificativa.
      │
      ▼
SAÍDA JSON
{
  "tecnologias": [
    {"tecnologia": "NIM", "justificativa": "..."},
    {"tecnologia": "TensorRT", "justificativa": "..."}
  ],
  "fontes": ["https://..."]
}
```

---

## Infraestrutura RAG existente

**Qdrant** em `http://localhost:6333`, collection `nvidia_knowledge`, embeddings de 768 dimensões.

**Embedding** → `src/rag/embedding.py` → `gerar_embedding(texto: str) -> list[float]`
Usa Gemini `text-embedding-004` com fallback `paraphrase-multilingual-mpnet-base-v2`.
Requer `GEMINI_API_KEY2` no `.env`.

**Indexação** → `src/rag/indexador.py` → `indexar_documento(texto: str, metadata: dict) -> str`
Gera embedding e faz upsert no Qdrant. Retorna o ID gerado.

**Busca** → `src/rag/buscador.py` → `buscar(query: str, filtros: dict | None, top_k: int) -> list[dict]`
Aplica automaticamente o filtro de categoria padrão se não for passado explicitamente.
Suporta `$in` para campos lista.

---

## Base de conhecimento NVIDIA

A base de conhecimento é populada **exclusivamente via arquivos JSON locais** — não há scraping de sites ativo.

### Por que JSON em vez de scraping

O site nvidia.com bloqueia scrapers com frequência, renderiza conteúdo via JavaScript e o conteúdo muda sem aviso. JSONs escritos manualmente ou gerados por LLM oferecem controle total sobre qualidade, classificação e cobertura, e são indexados mais rapidamente. O scraping foi descartado como abordagem primária.

### Onde ficam os arquivos

```
tecnologias_nvidia/
├── __init__.py
└── popular_via_json.py     ← script de indexação

data/nvidia_knowledge/
├── _schema.json            ← referência de campos e valores válidos (não indexado)
└── *.json                  ← um arquivo por tecnologia/tema
```

### Como indexar

```bash
# Indexa todos os JSONs da pasta padrão
python -m tecnologias_nvidia.popular_via_json

# Indexa um arquivo específico
python -m tecnologias_nvidia.popular_via_json --arquivo data/nvidia_knowledge/nim.json
```

O script valida os campos obrigatórios e valores controlados antes de indexar. Arquivos que começam com `_` são ignorados.

---

## Schema obrigatório de cada JSON

```json
{
  "url": "https://www.nvidia.com/...",
  "fonte": "nvidia.com",
  "titulo": "NVIDIA NIM — Microservices de Inferência",
  "categoria": "produto",
  "familia": "inferencia",
  "tecnologia": "NIM",
  "setores": ["saude", "geral"],
  "ia_tipos": ["LLM", "visão computacional"],
  "texto": "Texto descritivo rico em prosa corrida. Mínimo 50 chars."
}
```

### Valores controlados

**categoria** — `produto` | `conceito` | `caso_de_uso` | `inception` | `stack`
- `produto`: tecnologia ou ferramenta NVIDIA (SDK, framework, plataforma)
- `conceito`: explicação de conceito técnico (inferência, quantização, etc.)
- `caso_de_uso`: aplicação real em setor ou empresa
- `inception`: conteúdo sobre o programa NVIDIA Inception para startups
- `stack`: combinação de tecnologias NVIDIA para resolver um problema

**familia** — `inferencia` | `treinamento` | `dados` | `deployment` | `plataforma`
- `inferencia` → TensorRT, TensorRT-LLM, Triton, NIM, Dynamo
- `treinamento` → NeMo, CUDA, cuDNN
- `dados` → RAPIDS, cuDF, cuML, cuOpt
- `deployment` → NIM, GPU Operator, Run:ai
- `plataforma` → DGX, NGC, AI Enterprise, Nemotron, Metropolis, Isaac, Jetson

**setores** — `saude` | `financas` | `agro` | `varejo` | `industria` | `educacao` | `energia` | `logistica` | `geral`

**ia_tipos** — `visão computacional` | `NLP` | `LLM` | `recomendacao` | `series temporais` | `deteccao de anomalias` | `classificacao` | `geracao de conteudo` | `busca semantica`

---

## Decisões de design relevantes

**`categoria: "inception"` é sempre incluído no filtro de busca.**
O programa NVIDIA Inception é um habilitador universal — relevante para qualquer startup independentemente de setor ou tipo de IA. O buscador inclui `"inception"` no filtro de categoria por padrão. O reranker decide se o documento fica ou cai nos top_k com base na relevância semântica real.

**`conceito` é excluído do filtro padrão.**
Documentos de categoria `conceito` (ex: explicações de quantização, paralelismo de modelos) raramente são o que uma startup precisa na recomendação — são referências técnicas, não recomendações de adoção. Podem ser incluídos passando `categoria` explicitamente na chamada do buscador.

**`ia_tipos` não é campo de filtro na busca atual.**
O campo existe para discriminação semântica futura e como metadata de rastreabilidade, mas o retrieval atual filtra apenas por `setor` e `categoria`. Não popule `ia_tipos` com todos os valores disponíveis para documentos genéricos — isso destroiria o poder discriminativo do campo. Para documentos universais (ex: Inception), use os tipos que o texto realmente aborda.

**Chunking:** tiktoken `cl100k_base`, 400 tokens por chunk, overlap de 50 tokens, nunca corta no meio de uma frase. Todos os chunks de um mesmo documento compartilham o mesmo `doc_id`. A metadata de um chunk é herdada integralmente do documento JSON de origem — não há classificação por chunk no pipeline atual.

**Idioma:** português do Brasil ou inglês, ambos funcionam. O Gemini `text-embedding-004` é multilíngue e gera embeddings de qualidade comparável nos dois idiomas. Nomes de tecnologias NVIDIA devem sempre aparecer no original em inglês (NIM, NeMo, TensorRT, etc.).

---

## Status de implementação

| Componente | Arquivo | Status |
|---|---|---|
| Embedding | `src/rag/embedding.py` | Pronto |
| Indexação | `src/rag/indexador.py` | Pronto |
| Busca vetorial | `src/rag/buscador.py` | Pronto |
| Populador via JSON | `tecnologias_nvidia/popular_via_json.py` | Pronto |
| Reranker | `src/rag/reranker.py` | A criar |
| Agente de explicação | `src/agents/` | A criar |
| Base de conhecimento | `data/nvidia_knowledge/*.json` | Em construção |
