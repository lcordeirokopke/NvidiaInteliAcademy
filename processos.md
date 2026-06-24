# Processos do Projeto

## O que o projeto faz

Coleta nomes de startups brasileiras a partir do site Neofeed, extrai os nomes via IA (Gemini) com fallback em NLP (spaCy) e regex, salva os dados em JSON localmente e envia para um banco de dados Supabase.

---

## Estrutura de pastas

```
NvidiaInteliAcademy/
├── app.py                                      # ponto de entrada principal (em construção)
├── .env                                        # credenciais (Gemini, Supabase) — não sobe pro git
├── requirements.md                             # dependências e instruções de instalação
├── processos.md                                # este arquivo
│
├── src/
│   ├── coleta_startups/
│   │   ├── coleta.py                           # scraping do Neofeed via Playwright
│   │   └── filtro.py                           # extração de nomes via Gemini + spaCy + regex
│   ├── interacoes_banco/
│   │   └── upload_nomes_empresas.py            # envia nomes_empresas.json para o Supabase
│   └── agents/
│       └── extrator_gemini.py                  # integração com a API Gemini
│
├── data/
│   ├── artigos_nomes_empresas/
│   │   └── artigos_brutos.json                 # artigos crus raspados do Neofeed
│   └── nomes_empresas/
│       └── nomes_empresas.json                 # nomes de startups extraídos (saída final)
│
└── sql/
    └── criar_tabela.sql                        # SQL para criar a tabela no Supabase (roda uma vez)
```

---

## Pipeline de dados

```
1. coleta.py
   → abre o Neofeed via Playwright
   → clica em "Carregar mais" até trazer todos os artigos
   → salva título, url e tags em:
      data/artigos_nomes_empresas/artigos_brutos.json

2. filtro.py
   → lê artigos_brutos.json
   → para cada artigo, tenta extrair o nome da startup via:
        1º  Gemini API (extrator_gemini.py)
        2º  spaCy NER (fallback)
        3º  regex por posição verbal (fallback final)
   → aplica denylist (Google, Meta, bancos etc.) e heurísticas de validação
   → descarta duplicatas
   → salva em:
      data/nomes_empresas/nomes_empresas.json

3. upload_nomes_empresas.py
   → lê nomes_empresas.json
   → envia para a tabela "nomes_empresas" no Supabase via upsert (sem duplicatas)
```

---

## Como rodar

```bash
# 1. Instalar dependências (primeira vez)
pip install playwright spacy google-genai supabase python-dotenv
python -m spacy download pt_core_news_sm
playwright install chromium

# 2. Coletar artigos brutos
python src/coleta_startups/coleta.py

# 3. Extrair nomes de startups
python src/coleta_startups/filtro.py

# 4. Enviar para o Supabase
python src/interacoes_banco/upload_nomes_empresas.py
```

---

## Banco de dados (Supabase)

Tabela: `nomes_empresas`

| coluna     | tipo        | descrição                        |
|------------|-------------|----------------------------------|
| id         | bigint      | chave primária (auto)            |
| startup    | text        | nome da startup                  |
| titulo     | text        | título da notícia de origem      |
| url        | text unique | URL da notícia (evita duplicatas)|
| tags       | text[]      | categorias (vazio por enquanto)  |
| created_at | timestamptz | data de inserção (auto)          |

O arquivo `sql/criar_tabela.sql` contém o SQL para criar a tabela — colar no SQL Editor do Supabase e executar uma única vez.

---

## Observações

- O `.env` nunca sobe para o git (está no `.gitignore`)
- Os arquivos `data/` também não sobem — são gerados pelo pipeline
- `verify=False` no cliente httpx do Gemini é necessário pela SSL inspection da rede Nvidia
- O upsert usa `url` como chave de conflito — rodar o pipeline duas vezes não duplica registros
