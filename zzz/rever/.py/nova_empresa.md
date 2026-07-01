# nova_empresa.py — Adição Manual de Empresa ao Pipeline

## O que é

`src/nova_empresa.py` é o ponto de entrada para adicionar uma empresa manualmente ao banco de dados e executar todo o pipeline de análise sobre ela, sem precisar rodar o fluxo completo do `app.py` (que depende de scraping do Neofeed).

---

## Como usar

```bash
python src/nova_empresa.py "Nome da Empresa"
```

Exemplo:

```bash
python src/nova_empresa.py "Agibank"
```

Se o nome tiver mais de uma palavra, basta passar entre aspas. O script aceita múltiplos argumentos e os une com espaço.

---

## O que acontece passo a passo

| Passo | Módulo | O que faz |
|-------|--------|-----------|
| 0 | `nova_empresa.py` | Insere o nome na tabela `empresas` do Supabase (upsert — não duplica se já existir) |
| 1 | `descobre_dominio.py` | Testa candidatos de domínio e grava em `empresas.dominio` + `data/dominio_empresas/dominios_encontrados.json` |
| 2 | `descobre_gupy.py` | Descobre subdomínio Gupy e grava em `empresas.gupy_subdominio` + JSON |
| 3 | `descobre_gupy_vagas.py` | Busca vagas de IA no Gupy e grava sinais em `sinais_ia` + `data/gupy_vagas/gupy_vagas_ia.json` |
| 4 | `descobre_institucional.py` | Analisa site institucional e grava sinal em `sinais_ia` + `data/institucional/institucional.json` |
| 5 | `descobre_imprensa.py` | Busca notícias de IA via News API e grava sinal em `sinais_ia` + `data/imprensa/noticias_encontradas.json` |
| 6 | `analisa_neofeed.py` | Verifica se a empresa aparece nos artigos do Neofeed e grava sinal de ecossistema em `sinais_ia` |
| 7 | `filtro_ia.py` | Agrega todos os sinais, calcula pontuação e grava veredito em `avaliacoes_ia` + `data/vereditos_ia/<data>.json` |
| 8 | `enriquece_identidade.py` | Busca CNPJ, produto e setor via BrasilAPI e grava em `empresas_uso_ia` |
| 9 | `define_maturidade.py` | Calcula score e nível de maturidade de IA e atualiza `empresas_uso_ia` |

---

## Diferença em relação ao app.py

O `app.py` roda 13 passos, começando pelo scraping do Neofeed para descobrir novas empresas. O `nova_empresa.py` pula os passos 1–4 (scraping, filtro, upload de nomes) e insere a empresa diretamente, executando apenas os passos de análise (5–13 do app.py).

```
app.py:          [Neofeed] → [filtro] → [upload nomes] → [upload empresas] → [domínio] → ... → [maturidade]
nova_empresa.py:                                          [inserção direta] → [domínio] → ... → [maturidade]
```

---

## Onde os dados ficam

**Supabase (banco de dados):**
- `empresas` — registro principal da empresa (nome, domínio, gupy_subdominio)
- `sinais_ia` — sinais coletados por camada (institucional, gupy_vagas, imprensa, neofeed, ecossistema)
- `avaliacoes_ia` — pontuação e veredito final de uso de IA
- `empresas_uso_ia` — classificação de maturidade (ai-native, ai-first, ai-enabled, ai-adjacent)

**JSONs locais (`data/`):**
- `data/dominio_empresas/dominios_encontrados.json`
- `data/gupy_vagas/gupy_vagas_ia.json`
- `data/institucional/institucional.json`
- `data/imprensa/noticias_encontradas.json`
- `data/vereditos_ia/<YYYY-MM-DD>.json`

---

## Reprocessar uma empresa (reset)

Se precisar re-rodar o pipeline para uma empresa já existente (ex: corrigir análise, forçar nova verificação), use o script de reset antes de rodar `nova_empresa.py`:

```bash
python src/reset_empresa.py "Nome da Empresa"
python src/nova_empresa.py "Nome da Empresa"
```

O reset remove os registros da empresa em `sinais_ia`, `avaliacoes_ia` e `empresas_uso_ia`, mas **mantém** a entrada em `empresas` com domínio e gupy_subdominio já descobertos. Isso significa que os passos 1 e 2 serão pulados automaticamente e o pipeline recomeça a partir da análise institucional.

---

## Comportamento de cada etapa ao rodar novamente (sem reset)

Cada etapa tem sua própria proteção contra duplicata:

| Etapa | Comportamento |
|-------|--------------|
| Domínio / Gupy | Pula se já há valor preenchido no campo (`dominio`, `gupy_subdominio`) |
| Gupy vagas | Processa normalmente (insere novo registro) |
| Institucional | Pula se já existe linha em `sinais_ia` com `camada = 'institucional'` |
| Imprensa | Pula se já existe linha em `sinais_ia` com `camada = 'imprensa'` |
| Neofeed | Pula se já existe linha em `sinais_ia` com `camada = 'neofeed'` |
| Filtro IA | Re-avalia e faz upsert em `avaliacoes_ia` |
| Identidade / Maturidade | Re-processa apenas empresas com campos ausentes |

---

## Requisitos

- Arquivo `.env` na raiz do projeto com `SUPABASE_URL` e `SUPABASE_KEY`
- Dependências instaladas (`pip install -r requirements.txt`)
- Conexão com internet (buscas de domínio, Gupy, News API, BrasilAPI)
