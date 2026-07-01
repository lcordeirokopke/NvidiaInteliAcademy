# Estrutura de Metadados — Base de Conhecimento NVIDIA

## Decisão

A estrutura adotada é a **Hierárquica com família tecnológica**.

---

## Estrutura completa

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

---

## Campos e responsabilidades

### Identificação e rastreabilidade

| Campo | Tipo | Descrição |
|---|---|---|
| `url` | str | URL exata da página coletada |
| `fonte` | str | Domínio de origem (ex: `developer.nvidia.com`) |
| `titulo` | str | Título da página ou seção |
| `data_coleta` | str | Data ISO da coleta — controla reindexação |

### Classificação do conteúdo

| Campo | Tipo | Valores possíveis |
|---|---|---|
| `categoria` | str | `produto`, `conceito`, `caso_de_uso`, `inception`, `stack` |
| `familia` | str | `inferencia`, `treinamento`, `dados`, `deployment`, `plataforma` |
| `tecnologia` | str | `NIM`, `NeMo`, `TensorRT`, `RAPIDS`, `CUDA`, `Triton`, `cuDF`, `cuML`, `TensorRT-LLM`, `GPU Operator`, `DGX`, `NGC`, `AI Enterprise` |

### Alinhamento com o perfil da startup

| Campo | Tipo | Descrição |
|---|---|---|
| `setores` | list[str] | Setores para os quais o chunk é relevante |
| `ia_tipos` | list[str] | Tipos de IA abordados no chunk |

### Navegação no documento

| Campo | Tipo | Descrição |
|---|---|---|
| `doc_id` | str | UUID compartilhado por todos os chunks da mesma página |
| `chunk_index` | int | Posição do chunk dentro do documento |
| `chunk_total` | int | Total de chunks do documento |

---

## Valores controlados

### `categoria`

| Valor | Quando usar |
|---|---|
| `produto` | Ficha técnica, documentação, especificações de uma tecnologia NVIDIA |
| `conceito` | Explicação de um conceito (o que é inferência, o que é fine-tuning) |
| `caso_de_uso` | Cases de clientes, histórias de startups, benchmarks aplicados |
| `inception` | Conteúdo sobre o programa NVIDIA Inception |
| `stack` | Conteúdo sobre combinação de tecnologias, arquiteturas de referência |

### `familia`

| Valor | Tecnologias associadas |
|---|---|
| `inferencia` | TensorRT, TensorRT-LLM, Triton, NIM |
| `treinamento` | NeMo, CUDA, cuDNN |
| `dados` | RAPIDS, cuDF, cuML |
| `deployment` | NIM, GPU Operator |
| `plataforma` | DGX, NGC, AI Enterprise |

### `setores`

`saude`, `financas`, `agro`, `varejo`, `industria`, `educacao`, `energia`, `logistica`, `geral`

> `geral` é usado quando o conteúdo é relevante para qualquer setor.

### `ia_tipos`

`visão computacional`, `NLP`, `LLM`, `recomendacao`, `series temporais`, `deteccao de anomalias`, `classificacao`, `geracao de conteudo`, `busca semantica`

---

## Como os filtros funcionam no Qdrant

O pipeline monta os filtros a partir do perfil da startup e executa busca vetorial com filtros de metadata (não é busca híbrida — BM25 foi descartado, ver `zzz/sugestao/fluxo de recomendacao de tecnologias.md`):

```python
buscador.buscar(
    query="startup de saúde com visão computacional precisa de inferência em produção",
    filtros={
        "setor": {"$in": ["saude", "geral"]},  # mapeado por resolver_setor_qdrant()
        # categoria não precisa ser passado: buscador aplica o default automaticamente
        # ["produto", "caso_de_uso", "stack", "inception"]
    },
    top_k=5,
    reranking=True,
    fator_candidatos=3,
)
```

O filtro por `ia_tipos` não é aplicado — a query semântica e o reranking já direcionam o resultado para o tipo de IA correto sem precisar de filtro categórico adicional.

O agente pode filtrar em dois níveis de tecnologia:

- Por **família** quando a startup não tem tech preference definida
- Por **tecnologia** quando quer aprofundar em uma tech específica

---

## Por que não foram adotados outros campos

| Campo descartado | Motivo |
|---|---|
| `nivel` (tecnico/negocio) | O sistema faz recomendação automatizada, não adapta linguagem a um interlocutor |
| `maturidade_alvo` | Maturidade influencia *como* a recomendação é justificada pelo Gemini, não *quais* chunks são recuperados |
| `setor` (string única) | Limita cobertura — um chunk pode ser relevante para múltiplos setores |

---

## Cruzamento com o perfil da startup

| Campo do perfil | Campo da metadata | Tipo de uso |
|---|---|---|
| `setor` | `setores` | filtro `$in` |
| `ia_tipo` | `ia_tipos` | filtro `$in` |
| `produto` | — | ancora a busca semântica |
| `nivel_maturidade_ia` | — | usado pelo Gemini na argumentação |
| `ia_e_core_product` | — | não afeta os filtros do Qdrant; determina qual prompt do LLM 1 é usado (`explicar_tecnico` ou `explicar_negocio`) |
