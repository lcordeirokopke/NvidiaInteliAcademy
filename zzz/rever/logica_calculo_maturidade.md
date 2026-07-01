# Lógica de Cálculo de Maturidade AI — Framework Proposto

Documenta o framework redesenhado de classificação de maturidade de IA das empresas analisadas, substituindo o modelo de soma linear por uma arquitetura de ancoragem com modificadores.

---

## Filosofia central

O modelo anterior tratava maturidade como **soma linear de booleanos**. A mudança fundamental é reconhecer que maturidade de IA tem **hierarquia**, não aditividade: uma empresa pode acumular sinais positivos em vários campos, mas se IA não é o core do negócio, ela estruturalmente não pode ser `ai-native` — independente do score acumulado.

O novo framework usa **ancoragem com teto por nível**: `ia_e_core_product` define o teto máximo atingível, e os outros três pilares refinam a posição dentro desse teto.

---

## Visão geral do cálculo

```
score_maturidade_ia =
    pilar_centralidade (ia_e_core_product)     → 0.0 ou 4.0
  + pilar_sofisticacao (ia_tipo)               → 0.0 a 2.0
  + pilar_execucao     (produto_ia_lancado)    → 0.0 ou 2.0
  + pilar_genesis      (ano_fundacao)          → 0.0 a 2.0

score máximo possível = 10.0
```

```
nivel_maturidade_ia =
    se ia_e_core_product = NULL  →  NULL (não classificada)
    se ia_e_core_product = false →  max "ai-enabled" (hard cap)
    se ia_e_core_product = true  →  mapeado pelo score (ver tabela abaixo)
```

---

## Pilar 1 — Centralidade de IA (`ia_e_core_product`)

**O ancorador. Define o teto máximo do nível.**

| Valor | Pontos | Efeito no nível |
|---|---|---|
| `true` | 4.0 | Abre acesso a `ai-first` e `ai-native` |
| `false` | 0.0 | Hard cap em `ai-enabled` |
| `NULL` | — | Empresa não classificada; `nivel_maturidade_ia` permanece `NULL` |

Este é o único campo que pode bloquear a classificação inteiramente (`NULL`) ou limitar o teto máximo atingível (`false`). A regra de NULL preserva o comportamento atual: dados insuficientes não produzem classificação enganosa.

### Por que o peso é 4.0 (40% do score máximo)

`ia_e_core_product` é o maior diferenciador entre uma empresa que *usa* IA e uma empresa que *é* IA. O peso 4.0 garante que nenhuma combinação dos outros três pilares (max 6.0) consiga sozinha cruzar o threshold de `ai-first` (5.0) sem que IA seja o core — impedindo inflação de score.

---

## Pilar 2 — Sofisticação Técnica (`ia_tipo`)

**Mede a profundidade técnica do comprometimento com IA.**

Não é hierarquia de valor entre tipos de IA (Visão Computacional não é inferior a LLM), mas hierarquia de **profundidade de comprometimento técnico**: quão especializado e custoso é o stack de IA que a empresa precisa dominar para entregar seu produto.

| `ia_tipo` | Pontos | Raciocínio |
|---|---|---|
| `IA Generativa` | +2.0 | Frontier AI; exige domínio de LLMs, prompting, RAG, fine-tuning ou treinamento próprio |
| `NLP / LLM` | +2.0 | Frontier AI; deepstack de linguagem, embeddings, modelos de linguagem |
| `Visão Computacional` | +2.0 | Deep learning denso; exige dados rotulados, GPU, pipelines de inferência |
| `Automação Inteligente` | +1.0 | IA aplicada e processual; integra modelos mas raramente os constrói |
| `Análise Preditiva` | +1.0 | ML clássico; mais acessível, baseado em features estruturadas |
| `Dados e Analytics` | +0.5 | Data-driven; pode não envolver aprendizado de máquina real |
| `NULL` | +0.0 | Dado ausente não pontua; não penaliza |

### Observação sobre NULL

Se `ia_tipo` for `NULL` mas `ia_e_core_product = true`, a empresa ainda é classificada — simplesmente sem o bônus de sofisticação. Isso preserva a filosofia de "NULL não penaliza".

---

## Pilar 3 — Execução de Mercado (`produto_ia_lancado`)

**Mede se a intenção virou entrega real para clientes.**

| Valor | Pontos | Raciocínio |
|---|---|---|
| `true` | +2.0 | Execução confirmada; produto de IA em produção com clientes reais |
| `false` | +0.0 | Produto em construção; sem entrega ainda |
| `NULL` | +0.0 | Dado não coletado; não pontua, não penaliza |

### Comportamento com NULL e ai-native

Com `produto_ia_lancado = NULL`, uma empresa ainda pode atingir `ai-native` se os outros três pilares forem máximos:

```
ia_e_core = true        → 4.0
ia_tipo frontier        → 2.0
produto_lancado = NULL  → 0.0
ano >= 2022             → 2.0
                 Total: 8.0  →  ai-native
```

Isso é intencional: impede que a ausência de um dado manual bloqueie a classificação de uma startup early-stage genuinamente AI-native.

---

## Pilar 4 — Gênese / DNA Temporal (`ano_fundacao`)

**Mede se a empresa foi arquitetada para IA ou adaptada a ela.**

Em vez do binário atual (>= 2020 ou não), o ano é mapeado às **ondas tecnológicas de IA**, cada uma representando um nível diferente de profundidade de DNA:

| `ano_fundacao` | Pontos | Onda de referência |
|---|---|---|
| >= 2022 | +2.0 | Era ChatGPT / LLM generativo — nasceu para IA de linguagem |
| >= 2020 | +1.5 | Era GPT-3 / IA moderna acessível |
| >= 2017 | +1.0 | Era Transformers / deep learning mainstream |
| >= 2012 | +0.5 | Era Big Data / early deep learning |
| < 2012 | +0.0 | Era pré-IA — provavelmente pivotou para IA depois |

### Por que ondas e não um único corte

Uma empresa fundada em 2001 que hoje tem IA como core (ex: Blip) é estruturalmente diferente de uma fundada em 2023 para o mesmo propósito. A primeira foi construída em outra arquitetura e adotou IA progressivamente; a segunda nasceu com IA no centro de cada decisão de produto, dados e stack técnico. As ondas capturam essa diferença de forma graduada, sem descartar empresas mais antigas que genuinamente pivotaram.

---

## Regra de teto por nível

```
se ia_e_core_product = NULL:
    nivel_maturidade_ia = NULL
    score_maturidade_ia = NULL

se ia_e_core_product = false:
    nivel_maturidade_ia = max "ai-enabled"
    score_maturidade_ia = calculado normalmente (visível para comparação interna)

se ia_e_core_product = true:
    nivel_maturidade_ia = mapeado pelo score (tabela abaixo)
    score_maturidade_ia = calculado normalmente
```

A regra de teto não anula o score — o score continua sendo calculado e armazenado. Isso permite comparar empresas dentro do mesmo nível e identificar quais estão mais próximas de subir de tier.

---

## Mapeamento score → nível

| Score | `nivel_maturidade_ia` | Perfil |
|---|---|---|
| >= 8.0 (requer `ia_e_core = true`) | `ai-native` | IA é o DNA fundacional e atual — construída para IA, produto entregue, tecnologia de ponta |
| >= 5.0 (requer `ia_e_core = true`) | `ai-first` | IA é o produto central mas com gaps: empresa legada que pivotou, ou produto ainda não lançado, ou tipo menos sofisticado |
| >= 2.0 | `ai-enabled` | IA integrada com relevância real, mas não é o core do produto |
| < 2.0 | `ai-adjacent` | Menciona IA mas sem produto ou uso demonstrável baseado nela |

### Score máximo por combinação

```
Score 10.0 (ai-native máximo):
  ia_e_core = true       → 4.0
  ia_tipo frontier       → 2.0
  produto_lancado = true → 2.0
  ano >= 2022            → 2.0

Score 8.0 (ai-native sem produto lançado ou sem dado de ano):
  ia_e_core = true + frontier + ano >= 2022 + produto NULL  → 8.0
  ia_e_core = true + frontier + produto true + ano < 2012   → 8.0

Score 7.0 (ai-first sólido — empresa legada que pivotou):
  ia_e_core = true + tipo médio + produto true + ano < 2012 → 7.0

Score 5.5 (ai-first com gaps de execução):
  ia_e_core = true + tipo médio + produto NULL + ano 2017+  → 5.5

Score 5.0 (ai-enabled forte — hard cap por ia_e_core = false):
  ia_e_core = false + frontier + produto true + ano >= 2022 → 5.0 (cap: ai-enabled)

Score 2.0 (ai-enabled fraco):
  ia_e_core = false + produto true + ano < 2012            → 2.0
```

---

## Validação com dados reais

| Empresa | Core | Tipo IA | Lançado | Ano | Score | Nível |
|---|---|---|---|---|---|---|
| Sinatra AI | true (+4.0) | IA Gen (+2.0) | true (+2.0) | 2023 (+2.0) | **10.0** | ai-native |
| Blip | true (+4.0) | Auto Int (+1.0) | true (+2.0) | 2001 (+0.0) | **7.0** | ai-first |
| Fintalk | true (+4.0) | Auto Int (+1.0) | NULL (+0.0) | 2019 (+1.0) | **5.5** | ai-first |
| Segura.ai | false → cap | Auto Int (+1.0) | true (+2.0) | 2024 (+2.0) | **5.0** → cap | ai-enabled |
| Vivo | false → cap | NULL (+0.0) | true (+2.0) | 1998 (+0.0) | **2.0** → cap | ai-enabled |

### Leitura dos resultados

- **Sinatra AI (10.0 / ai-native):** Startup de IA generativa, fundada em 2023, produto entregue, IA como razão de ser. Classificação perfeita.
- **Blip (7.0 / ai-first):** Plataforma conversacional com IA como core hoje, produto entregue, mas fundada em 2001. É genuinamente AI-first, mas não AI-native — o DNA histórico é de empresa de software, não de IA.
- **Fintalk (5.5 / ai-first):** IA como core, fundada em 2019 (era deep learning), mas `produto_ia_lancado` ainda não confirmado. Ai-first com execução pendente de validação.
- **Segura.ai (5.0 / ai-enabled):** Insurtech com IA integrada de forma sofisticada e produto lançado, mas IA não é o core — o core é a corretagem. Hard cap funciona corretamente.
- **Vivo (2.0 / ai-enabled):** Telco usando Gemini integrado ao portfólio. AI-enabled por margem mínima — correto para uma operadora de telecom.

---

## Campos que entram no cálculo

| Campo | Pilar | Fonte |
|---|---|---|
| `ia_e_core_product` | Centralidade (ancorador) | Gemini via scraping |
| `ia_tipo` | Sofisticação | Gemini com validação por conjunto fechado |
| `produto_ia_lancado` | Execução | Preenchimento manual |
| `ano_fundacao` | Gênese | BrasilAPI / Receita Federal |

---

## Campos que NÃO entram no cálculo e por quê

| Campo | Motivo de exclusão |
|---|---|
| `programa_aceleracao` | NULL ≠ não participa. Scraping falha silenciosamente (badges como imagem sem alt text). Penalizaria injustamente participantes cujo site não expõe o badge em texto. Disponível para consulta manual. |
| `mercado_alvo` | Dimensão de estratégia de negócio, não de maturidade de IA. Uma empresa pode ser AI-native focada só no Brasil. |
| `modelo_negocio` | Idem — B2B vs B2C não determina profundidade de IA. |
| `uso_ia_descricao` | Campo textual não estruturado; introduziria subjetividade no score. Valor está no `ia_e_core_product` derivado dele. |

---

## Campos futuros que elevariam a qualidade do framework

Se coletados, estes campos agregariam dimensões atualmente não mensuráveis:

| Campo proposto | Tipo | O que mediria |
|---|---|---|
| `ia_proprio_modelo` | boolean | A empresa treina/faz fine-tuning de modelo próprio vs usa apenas API. Maior diferenciador de profundidade técnica real. |
| `receita_recorrente_ia` | boolean | Já tem receita recorrente de produto de IA (não apenas pilotos). Mede execução comercial, não apenas técnica. |
| `equipe_ia_propria` | boolean | Tem cientistas ou engenheiros de ML internos. Diferencia "empresa que faz IA" de "empresa que usa IA via API". |

Esses três campos tocariam na distinção central entre usar IA como insumo e construir IA como competência — o coração do conceito ai-native.

---


