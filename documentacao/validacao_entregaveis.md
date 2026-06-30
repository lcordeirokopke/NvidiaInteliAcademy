# Validação dos Entregáveis

## Entregável 2 — Sistema multiagente com LangGraph

**Status: Completo**

Sistema com agentes especializados para busca, extração, classificação, validação, RAG e recomendação, implementado como grafo de estados com LangGraph.

---

### Agentes implementados

| Agente | Arquivo | Responsabilidade |
|---|---|---|
| Busca | `src/agents/extras/nodes.py` → `buscar_e_reranquear` | Busca vetorial no Qdrant com relaxamento progressivo em até 3 iterações |
| Extração de query | `src/agents/query.py` + `montar_query` | Transforma o perfil da startup em frase de busca semântica via OpenRouter; fallback local em caso de falha |
| Classificação e roteamento | `src/agents/extras/nodes.py` → `rotear_apos_busca` | Roteia para explicação técnica (`ia_e_core_product=True`) ou de negócio (demais casos) com base no perfil |
| Validação | `src/agents/extras/nodes.py` → `validar_json` + `checar_json_valido` | Extrai e valida o JSON da resposta do LLM 1; injeta o erro no prompt e retenta até 3 vezes |
| RAG | `src/rag/` (buscador + reranker + embedding) | Pipeline completo: embedding via Gemini → busca top-k no Qdrant → reordenação com cross-encoder multilingual |
| Recomendação LLM 1 | `explicar_tecnico` / `explicar_negocio` | Articula as tecnologias NVIDIA mais relevantes com justificativa para CTO ou founder |
| Recomendação LLM 2 | `sintese_executiva` | Traduz a recomendação técnica para linguagem de negócio (CEO + account manager NVIDIA) |
| Recomendação LLM 3 | `roadmap_adocao` | Gera plano de adoção em 30/60/90 dias calibrado pelo nível de maturidade de IA da startup |
| Recomendação LLM 4 | `kit_inicio` | Retorna container NGC, tutorial de entrada e créditos Inception específicos para cada tecnologia recomendada |

---

### Arquivos entregues

```
src/recomendacao/
├── inicia_recomendacao.py        — entry point; itera sobre empresas elegíveis, suporta --empresa-id e --forcar
└── verifica_situacao_coleta.py   — filtra empresas com perfil completo e situação adequada

src/agents/extras/
├── graph.py      — monta, conecta e compila o grafo LangGraph
├── nodes.py      — todos os nós e funções de roteamento
├── state.py      — TypedDict EstadoRecomendacao (contrato do estado compartilhado)
├── prompts.py    — prompts dos 4 agentes LLM
└── gemini.py     — wrapper Gemini com retry exponencial (3×, 5s/10s/20s) e singleton thread-safe

src/rag/
├── buscador.py   — busca vetorial no Qdrant com filtros de metadata
├── reranker.py   — cross-encoder multilingual que reordena os candidatos
├── embedding.py  — geração de embeddings via Gemini gemini-embedding-001
└── indexador.py  — chunking e indexação de documentos JSON no Qdrant
```

---

### Grafo de estados

O grafo (`graph.py`) conecta os nós em sequência com roteamento condicional:

```
carregar_perfil → montar_query → buscar_e_reranquear
  → (rotear_apos_busca) → explicar_tecnico / explicar_negocio
  → validar_json → (checar_json_valido) → sintese_executiva
  → roadmap_adocao → kit_inicio → salvar_resultado
```

Caminhos de falha encerram via `sem_resultado` com motivo registrado em `output_final["erro"]`.

---

### Ciclos de retry implementados

**Qualidade dos chunks** — `buscar_e_reranquear` executa até 3 vezes com parâmetros progressivamente relaxados:

| Iteração | Candidatos | Filtro de setor |
|---|---|---|
| 0 | top_k × 3 = 15 | setor + "geral" |
| 1 | top_k × 5 = 25 | nenhum |
| 2 | top_k × 7 = 35 | nenhum |

Dispara quando `chunks` está vazio ou `rerank_score[0] < 0.3`.

**JSON inválido** — LLM 1 pode ser chamado até 3 vezes. A cada falha o erro de parse é injetado no prompt e os chunks originais permanecem disponíveis no estado.

---

### Saída final

Ao final de um run bem-sucedido, `output_final` consolida os quatro outputs dos LLMs:

```json
{
  "explicacao":        { "tecnologias": [...], "fontes": [...] },
  "sintese_executiva": { "resumo": "...", "impacto_principal": "...", ... },
  "roadmap":           { "tecnologia_prioritaria": "...", "plano": { "30_dias": [...], ... }, ... },
  "kit_inicio":        [{ "tecnologia": "...", "container_ngc": "...", "tutorial_entrada": "...", ... }]
}
```

---

### Persistência e tolerância a falhas

- Grafo compilado com `MemorySaver`; suporta `SqliteSaver`/`PostgresSaver` em produção.
- Resultado salvo no Supabase via upsert com `on_conflict="empresa_id"`.
- Falha na escrita no banco não interrompe o run — resultado preservado no checkpointer para reconciliação posterior.
- Todas as dependências externas (Supabase, Qdrant, Gemini, OpenRouter) têm tratamento de falha individual sem crash do pipeline.
