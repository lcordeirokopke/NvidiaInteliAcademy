# Busca de Notícias — Como Funciona

## Visão Geral

A camada de imprensa é uma das cinco camadas do pipeline de detecção de adoção de IA (`sinais_ia`). Seu objetivo é encontrar artigos jornalísticos que evidenciem que uma empresa usa, implementou ou recebeu investimento relacionado a inteligência artificial.

O processo usa três APIs em cascata: se a primária falhar ou não retornar resultados, o sistema tenta automaticamente a segunda e depois a terceira.

```
News API (newsapi.org)
    └── falhou? → NewsData.io
                      └── falhou? → GNews
```

---

## Queries de Busca

Cada empresa passa por três queries distintas, aplicadas a todas as APIs. As queries foram desenhadas para capturar sinais em ordem decrescente de especificidade:

### Query A — Ação Concreta
```
"{nome}" AND (implementou OR lançou OR integrou OR desenvolveu OR automatizou OR adquiriu)
           AND ("inteligência artificial" OR "machine learning" OR "IA generativa"
                OR "modelo de linguagem" OR "GPT" OR "LLM")
```
Captura artigos onde a empresa fez algo concreto com IA. É o sinal mais forte porque exige um verbo de ação — não apenas menção ao tema.

### Query B — Produto ou Serviço com IA
```
"{nome}" AND ("com IA" OR "baseada em IA" OR "baseado em IA" OR "powered by AI"
              OR "assistente virtual" OR "recomendação" OR "predição"
              OR "automação inteligente" OR "chatbot" OR "copilot")
```
Captura linguagem de produto e go-to-market. Empresas que comunicam publicamente que seus produtos usam IA aparecem aqui.

### Query C — Aporte ou Investimento com IA
```
"{nome}" AND ("aporte" OR "rodada" OR "captou" OR "investimento" OR "Series A" OR "seed")
           AND ("inteligência artificial" OR "IA" OR "machine learning")
```
Rodadas de investimento com foco em IA são amplamente cobertas pela imprensa de negócios brasileira e são um sinal forte de adoção real — quem capta para IA, usa IA.

---

## As Três APIs

### 1. News API — `newsapi.org` (primária)

**Arquivo:** `src/dados_ia_startups/descobre_imprensa.py`

A API principal. Oferece o maior controle sobre a busca por permitir filtro por domínio diretamente no request, ou seja, a filtragem acontece no servidor antes mesmo dos resultados chegarem.

**Parâmetros relevantes:**
| Parâmetro | Valor | Por quê |
|-----------|-------|---------|
| `q` | `"{nome}" AND ({termos})` | Query booleana completa |
| `domains` | lista de domínios brasileiros | Restringe à imprensa nacional de qualidade |
| `language` | `pt` | Português |
| `sortBy` | `relevancy` | Prioriza artigos mais relevantes para a query |
| `pageSize` | `10` | Máximo por requisição |

**Domínios permitidos:** valor.globo.com, exame.com, startups.com.br, neofeed.com, folha.uol.com.br, estadao.com.br, infomoney.com.br, tecmundo.com.br, olhardigital.com.br, canarinho.vc, forbes.com.br, pegn.globo.com, revistapegn.globo.com, epocanegocios.globo.com, braziljournal.com, siliconvalleybrasil.com.br, canaltech.com.br, computerworld.com.br, startupi.com.br

**Limitação principal:** plano gratuito só acessa artigos dos últimos 30 dias.

---

### 2. NewsData.io — `newsdata.io` (primeiro fallback)

**Arquivo:** `src/dados_ia_startups/fallback/newsdata_io.py`

Ativado quando o News API falha ou retorna erro. A principal diferença em relação à API primária é o uso do parâmetro `intitle`, que restringe a busca dos termos de IA ao **título do artigo** — não ao corpo. Isso elimina o problema mais comum de falso positivo: artigos longos que mencionam a empresa em um parágrafo e IA em outro parágrafo completamente diferente.

**Parâmetros relevantes:**
| Parâmetro | Valor | Por quê |
|-----------|-------|---------|
| `q` | `"{nome}"` | Só o nome da empresa no corpo |
| `intitle` | termos de IA | IA obrigatória no título do artigo |
| `language` | `pt` | Português |
| `country` | `br` | Brasil |

**Por que `intitle` muda o jogo:** um artigo com o nome da empresa no título e um termo de IA também no título quase sempre é sobre a empresa usando IA. Um artigo onde IA aparece só no corpo pode ser um roundup do setor onde a empresa é mencionada de passagem.

**Normalização de campos:** o NewsData.io usa nomes de campo diferentes do News API. O módulo normaliza automaticamente:
- `link` → `url`
- `pubDate` → `publishedAt`

---

### 3. GNews — `gnews.io` (segundo fallback)

**Arquivo:** `src/dados_ia_startups/fallback/gnews.py`

Último recurso quando as duas APIs anteriores falham. Tem menor precisão que as outras por não suportar filtro de domínio no servidor — a filtragem é feita localmente após os resultados chegarem, o que significa que os 10 resultados retornados podem ter menos artigos úteis após o filtro.

**Parâmetros relevantes:**
| Parâmetro | Valor | Por quê |
|-----------|-------|---------|
| `q` | query com parênteses e exclusões | Ver abaixo |
| `lang` | `pt` | Português |
| `country` | `br` | Brasil |
| `max` | `10` | Máximo por requisição |
| `sortby` | `relevance` | Prioriza relevância |

**Estrutura da query:**
```
"{nome}" ("inteligência artificial" OR "machine learning" OR "IA generativa"
          OR "chatbot" OR "automação inteligente" OR "LLM" OR "GPT")
         -"previsão do tempo" -"inteligência artificial geral"
```

Os parênteses garantem que o nome da empresa seja obrigatório em **todas** as alternativas — sem eles, o parser interpretaria a query de forma errada e retornaria artigos sem o nome da empresa. As exclusões (`-"previsão do tempo"`, `-"inteligência artificial geral"`) removem as fontes de ruído mais frequentes no corpus brasileiro.

**Filtragem local:** após receber os resultados, o módulo mantém apenas artigos de domínios da lista brasileira permitida.

---

## Filtro Final

Independente de qual API retornou os resultados, todos passam pelo mesmo filtro em `descobre_imprensa.py`:

1. **Domínio bloqueado?** — descarta domínios acadêmicos (arxiv, pubmed, springer etc.)
2. **Domínio brasileiro?** — descarta qualquer artigo fora da lista permitida
3. **Nome no título?** — descarta artigos onde o nome exato da empresa não aparece no título

O terceiro filtro é o mais importante: garante que o artigo é *sobre* a empresa, não apenas a menciona de passagem. O máximo de artigos salvos por empresa é **5**.

---

## O que é Salvo

Cada artigo aprovado gera um registro na tabela `sinais_ia` com:
- `camada`: `"imprensa"`
- `encontrado`: `true`
- `evidencia`: título + descrição do artigo
- `fonte_url`: URL do artigo
- `publicado_em`: data de publicação

Se nenhuma query retornar artigos válidos, um registro com `encontrado: false` é inserido para indicar que a empresa foi verificada e não há cobertura de imprensa sobre IA.
