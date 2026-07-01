# NVIDIA Startup AI Radar

Sistema multi-agente capaz de mapear startups brasileiras com potencial AI-native, coletar informações públicas sobre elas, diagnosticar sua maturidade técnica em IA e recomendar tecnologias NVIDIA adequadas ao perfil de cada empresa.

---

## 1. Contextualização do problema

O mercado de inteligência artificial está passando por uma mudança estrutural. Grandes laboratórios como OpenAI, Anthropic, Google DeepMind e Meta deixaram de atuar apenas como fornecedores de modelos fundacionais e passaram a subir na cadeia de valor — oferecendo APIs multimodais, agentes, ferramentas de produtividade, busca, voz, código, automação de workflows e produtos finais para empresas.

Esse movimento cria uma ameaça direta para startups de IA que se posicionam apenas como wrappers de LLMs. Uma startup que apenas conecta uma API de terceiro a uma interface gráfica, sem dados proprietários, sem workflow profundo e sem otimização técnica, pode ser rapidamente substituída por funcionalidades nativas dos grandes labs.

Ao mesmo tempo, surge uma oportunidade: startups podem se diferenciar ao se tornarem **AI-native services**, combinando software, agentes de IA, dados proprietários, automação e serviço especializado para entregar resultados de negócio de ponta a ponta.

Nesse contexto, a NVIDIA tem posição estratégica. Muitas startups usam IA, mas poucas otimizam toda a stack técnica. A stack NVIDIA pode ajudar essas empresas a evoluir de protótipos baseados em APIs para sistemas de IA escaláveis, eficientes e preparados para produção.

---

## 2. Objetivo do projeto

Construir um sistema capaz de:

- Encontrar startups brasileiras com sinais de uso intensivo de IA.
- Coletar dados públicos sobre empresa, produto, setor, clientes e tecnologias utilizadas.
- Avaliar possíveis gaps na stack de IA da empresa.
- Consultar uma base de conhecimento sobre tecnologias NVIDIA.
- Recomendar as tecnologias NVIDIA mais adequadas para cada startup.
- Gerar um briefing executivo para apoiar a abordagem comercial e técnica pelo NVIDIA Inception.

---

## 3. Escopo da solução

A solução é composta por três camadas:

**Pipeline de coleta e qualificação** (`app.py` — 16 etapas sequenciais)
Raspa artigos do Neofeed, extrai nomes de startups via LLM, envia para o Supabase, descobre domínios e perfis Gupy, pesquisa sinais de uso de IA (site institucional, vagas, notícias, artigos), emite veredito de qualificação, enriquece o perfil das aprovadas com dados do CNPJ via BrasilAPI, calcula score de maturidade AI-native e gera recomendações NVIDIA via LangGraph.

**Pipeline de recomendação** (`src/recomendacao/` + `src/agents/extras/`)
Grafo LangGraph com 9 nós sequenciais e condicionais que carrega o perfil da startup, monta uma query semântica, busca e reranqueia chunks da base de conhecimento NVIDIA no Qdrant e aciona 4 LLMs em sequência para gerar: tecnologias recomendadas, síntese executiva, roadmap de adoção 30/60/90 dias e kit de início com containers NGC e créditos Inception.

**Dashboard web** (`dashboard.py` — Streamlit)
Interface com 6 abas: Resumo Geral, Análise Completa, Pendentes, Excluídas, Uso de IA e Todas as Empresas. Permite visualizar o funil completo, disparar o pipeline, reprocessar empresas pendentes, corrigir domínios e promover empresas excluídas manualmente.

---

## 4. Tecnologias principais

### Coleta e scraping
| Tecnologia | Uso |
|---|---|
| **Playwright** | Scraping de sites dinâmicos (Neofeed, sites institucionais das startups) |
| **BeautifulSoup4** | Parsing de HTML estático |
| **requests / httpx** | Requisições HTTP gerais |

### Banco de dados
| Tecnologia | Uso |
|---|---|
| **Supabase (PostgreSQL)** | Armazenamento estruturado de empresas, sinais de IA, avaliações e recomendações |
| **Qdrant** | Banco vetorial para a base de conhecimento NVIDIA |

### LLM e orquestração
| Tecnologia | Uso |
|---|---|
| **Google Gemini 2.5 Flash** | LLM principal de todos os agentes (extração, classificação, recomendação) |
| **gemini-embedding-001** | Geração de embeddings para o RAG |
| **LangGraph** | Orquestração do grafo de agentes de recomendação |
| **LangChain Core** | Abstrações base |
| **Langchain Groq** | Interface alternativa de LLM |

### RAG e reranking
| Tecnologia | Uso |
|---|---|
| **Qdrant Client** | Busca vetorial por similaridade de cosseno (3072 dimensões) |
| **sentence-transformers** | Cross-encoder `mmarco-mMiniLMv2-L12-H384-v1` para reranking semântico |

### NLP
| Tecnologia | Uso |
|---|---|
| **spaCy + pt_core_news_sm** | NER para extração de nomes de startups (fallback ao Gemini) |
| **tiktoken** | Contagem de tokens |

### APIs externas
| Tecnologia | Uso |
|---|---|
| **BrasilAPI** | Enriquecimento de CNPJ (razão social, CNAE, porte, município, UF) |
| **Gupy** | Descoberta de subdomínios e vagas de IA |
| **News API / GNews / NewsData.io** | Pesquisa de notícias sobre uso de IA |

### Frontend e utilitários
| Tecnologia | Uso |
|---|---|
| **Streamlit** | Dashboard web interativo |
| **pandas** | Manipulação de dados tabulares |
| **python-dotenv** | Gestão de variáveis de ambiente |

---

## 5. Agentes

### Agentes de extração e classificação (pipeline de coleta)

| Agente | Arquivo | Função |
|---|---|---|
| **Extrator de Nomes** | `extrato_nomes_startups_gemini.py` | Extrai o nome de startups a partir de títulos de artigos |
| **Extrator de Produto** | `extrator_gemini_produto.py` | Descreve o produto ou serviço principal da startup |
| **Extrator de Uso de IA** | `extrator_uso_ia_gemini.py` | Descreve como a startup utiliza IA |
| **Extrator de Stack** | `extrator_stack_gemini.py` | Identifica a stack tecnológica da empresa |
| **Classificador de Tipo de IA** | `classificador_ia_tipo_gemini.py` | Classifica o tipo de IA (Visão Computacional, NLP/LLM, IA Generativa, etc.) |
| **Classificador de Setor** | `classificador_setor_gemini.py` | Classifica o setor de atuação (saúde, finanças, agro, varejo, etc.) |
| **Extrator de Modelo de Negócio** | `extractor_gemini_modelo_negocios.py` | Classifica o modelo de negócio (SaaS, marketplace, etc.) |
| **Inferidor de Mercado-Alvo** | `inferidor_mercado_alvo_gemini.py` | Infere o segmento de clientes da startup |
| **Inferidor de Produto Lançado** | `inferidor_produto_lancado_gemini.py` | Infere se a startup já tem produto de IA em produção |
| **Gerador de Query** | `query.py` | Gera a query semântica para o RAG a partir do perfil da empresa |

### Agentes do grafo LangGraph (pipeline de recomendação)

```
carregar_perfil → montar_query → buscar_e_reranquear
    ↓ (condicional: ia_e_core_product?)
explicar_tecnico | explicar_negocio → validar_json (com retry)
    → sintese_executiva → roadmap_adocao → kit_inicio → salvar_resultado
```

| Nó | Função |
|---|---|
| **carregar_perfil** | Carrega o perfil completo da startup do Supabase |
| **montar_query** | Gera a query semântica via LLM com fallback determinístico |
| **buscar_e_reranquear** | Busca vetorial no Qdrant + reranking com CrossEncoder (até 3 tentativas com relaxamento progressivo de filtros) |
| **explicar_tecnico** | LLM 1 — foco em stack técnica (quando IA é o produto central) |
| **explicar_negocio** | LLM 1 — foco em casos de uso de negócio (quando IA é suporte) |
| **validar_json** | Valida e parseia o JSON do LLM 1, com até 2 retries injetando o erro no prompt |
| **sintese_executiva** | LLM 2 — síntese executiva para CEO e account manager |
| **roadmap_adocao** | LLM 3 — plano de adoção 30/60/90 dias calibrado pela maturidade da startup |
| **kit_inicio** | LLM 4 — containers NGC, tutoriais e créditos Inception por tecnologia recomendada |
| **salvar_resultado** | Persiste todos os outputs no Supabase (`recomendacoes_nvidia`) |

### Tecnologias NVIDIA na base de conhecimento

A base de conhecimento indexada no Qdrant contém **23 tecnologias NVIDIA**:

| Tecnologia | Tecnologia |
|---|---|
| NVIDIA Inception | NVIDIA NIM |
| NVIDIA API Catalog | NVIDIA NeMo |
| NVIDIA NeMo Guardrails | NVIDIA Triton Inference Server |
| NVIDIA TensorRT-LLM | NVIDIA RAPIDS |
| NVIDIA cuDF | NVIDIA cuML |
| NVIDIA cuGraph | NVIDIA cuOpt |
| NVIDIA cuVS | NVIDIA CUDA Toolkit |
| NVIDIA Riva | NVIDIA Omniverse |
| NVIDIA Isaac | NVIDIA Clara |
| NVIDIA Morpheus | NVIDIA AI Enterprise |
| NVIDIA Nemotron | NVIDIA Parakeet | 
| NVIDIA NV EmbedQA | |

---

## 6. Fontes de scraping

| Fonte | Tipo | Tecnologia |
|---|---|---|
| **Neofeed** (`neofeed.com.br/startups/`) | Portal de notícias de startups brasileiras | Playwright |
| **Sites institucionais das startups** | Páginas oficiais das empresas (produto, sobre, tecnologia, blog) | Playwright + requests + BeautifulSoup |
| **Gupy** | Subdomínios e vagas de emprego com sinal de uso de IA | requests |
| **News API** | Notícias de imprensa sobre uso de IA por empresa | requests |
| **GNews** | Fallback de notícias | requests |
| **NewsData.io** | Fallback secundário de notícias | requests |
| **BrasilAPI** | Dados cadastrais via CNPJ (razão social, CNAE, porte, município, UF) | requests |

---

## 7. Entregáveis concluídos

| # | Entregável | Status | Detalhes |
|---|---|---|---|
| 1 | **Pipeline de scraping** | ✅ Concluído | Coleta automática do Neofeed com Playwright, extração de nomes via Gemini + spaCy, descoberta de domínios e vagas Gupy, análise de site institucional e imprensa |
| 2 | **Sistema multiagente com LangGraph** | ✅ Concluído | Grafo com 9 nós, edges condicionais, ciclo de retry de qualidade nos chunks e retry de JSON inválido, checkpointer MemorySaver |
| 3 | **RAG NVIDIA com reranking** | ✅ Concluído | Base de 23 tecnologias indexadas no Qdrant com embeddings `gemini-embedding-001` (3072 dim), reranking semântico com CrossEncoder multilingual |
| 4 | **Motor de recomendação** | ✅ Concluído | Pipeline de 4 LLMs em sequência: tecnologias recomendadas com justificativa técnica e de negócio, síntese executiva, roadmap 30/60/90 dias e kit de início com containers NGC e créditos Inception |
| 5 | **Interface web** | ✅ Concluído | Dashboard Streamlit com 6 abas, funil de qualificação, reprocessamento manual de pendentes, atualização de domínios e promoção de empresas excluídas |
| 6 | **Diferencial do projeto** | ✅ Concluído | Funil de qualificação AI-native com score de maturidade (0–10) e classificação em 4 níveis (ai-native, ai-first, ai-enabled, ai-adjacent); pipeline totalmente automatizado de ponta a ponta acionável pelo próprio dashboard |

---

## Pré-requisitos

- Python 3.12+
- Docker (para o Qdrant)
- Variáveis de ambiente configuradas no `.env`

> Todos os comandos devem ser executados a partir da **raiz do projeto** (`NvidiaInteliAcademy/`).

---

## Instalação

```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_sm
playwright install chromium
```

---

## Variáveis de ambiente (`.env`)

```env
SUPABASE_URL=...
SUPABASE_KEY=...
GEMINI_API_KEY=...        # LLM principal (Gemini 2.5 Flash)
GEMINI_API_KEY2=...       # embeddings (gemini-embedding-001) + fallback de cota
OPENROUTER_API_KEY=...    # geração da query semântica (fallback)
```

---

## Setup — primeira execução

### 1. Subir o Qdrant

```bash
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

Se o container já existe e está parado:

```bash
docker start qdrant
```

### 2. Criar a collection no Qdrant

```bash
python -m src.rag.setup_qdrant
```

### 3. Indexar a base de conhecimento NVIDIA

```bash
python -m src.rag.indexador
```

Para indexar um arquivo específico:

```bash
python -m src.rag.indexador --arquivo data/nvidia_knowledge/nvidia_nim.json
```

---

## Executar o pipeline completo

```bash
python app.py
```

## Adicionar uma empresa manualmente

```bash
python src/nova_empresa.py "Nome da Empresa"
```

## Executar apenas as recomendações

```bash
# Todas as empresas elegíveis
python src/recomendacao/inicia_recomendacao.py

# Uma empresa específica
python src/recomendacao/inicia_recomendacao.py --empresa-id 42

# Reprocessar mesmo que já tenha resultado
python src/recomendacao/inicia_recomendacao.py --empresa-id 42 --forcar
```

## Rodar o dashboard

```bash
streamlit run dashboard.py
```

---

## Documentação

| Documento | Conteúdo |
|---|---|
| `documentacao/fluxo_recomendacao_tecnologias.md` | Como funciona o pipeline RAG + agentes |
| `documentacao/langgraph.md` | Grafo LangGraph: nós, arestas, estado e retries |
| `documentacao/dashboard.md` | Guia de uso do dashboard Streamlit |
