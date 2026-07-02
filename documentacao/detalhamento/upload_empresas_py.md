# Documentação Técnica — upload_empresas.py

**Localização:** [`src/interacoes_banco/upload_empresas.py`](../src/interacoes_banco/upload_empresas.py)

---

## Visão Geral

Script de carga inicial responsável por popular a tabela `empresas` no Supabase. Lê o arquivo `nomes_empresas.json` produzido pela etapa de coleta, extrai os nomes únicos de startups e os insere (ou confirma) no banco via operação de upsert. É executado uma vez por ciclo de coleta, antes das etapas de enriquecimento, e serve como ponto de entrada para todo o pipeline — todas as tabelas subsequentes referenciam os registros criados aqui.

---

## Tecnologias Utilizadas

### `json` — Biblioteca Padrão Python
Módulo nativo responsável pela leitura e desserialização de arquivos no formato JSON. Converte o conteúdo do arquivo em estruturas de dados nativas do Python (listas e dicionários), permitindo iteração e filtragem dos registros.

### `os` — Biblioteca Padrão Python
Módulo nativo utilizado para acesso às variáveis de ambiente do sistema operacional. As credenciais de conexão ao banco de dados (`SUPABASE_URL` e `SUPABASE_KEY`) são lidas exclusivamente via `os.environ`, mantendo-as fora do código-fonte.

### `pathlib.Path` — Biblioteca Padrão Python
Classe para manipulação de caminhos de arquivo de forma orientada a objetos. A construção `Path(__file__).resolve().parent.parent.parent` resolve dinamicamente o caminho absoluto da raiz do projeto a partir da localização do próprio script, tornando os caminhos independentes do diretório de execução.

### `python-dotenv` (v1.2.2)
Biblioteca externa que lê o arquivo `.env` localizado na raiz do projeto e carrega suas variáveis como variáveis de ambiente do processo. Essa abordagem separa configuração de código e evita que credenciais sejam expostas no repositório.

### `supabase-py` (v2.31.0)
Cliente Python oficial para o Supabase. Abstrai as chamadas à API REST (PostgREST) do projeto, permitindo operações de banco de dados como `upsert`, `select` e `update` por meio de uma interface fluente em Python. Internamente, traduz cada operação em uma requisição HTTP direcionada ao endpoint do projeto Supabase.

> **Supabase** é uma plataforma de banco de dados como serviço (DBaaS) construída sobre PostgreSQL. Expõe a base de dados via API REST gerada automaticamente pelo PostgREST, com autenticação e políticas de acesso configuráveis por tabela.

---

## Funcionamento do Código

### 1. Inicialização do módulo

```python
_RAIZ = Path(__file__).resolve().parent.parent.parent
load_dotenv(_RAIZ / ".env")
```

Ao ser importado, o módulo resolve o caminho absoluto da raiz do projeto e carrega as variáveis de ambiente do arquivo `.env`. Esse bloco é executado antes de qualquer chamada à função `upload()`.

### 2. Conexão com o banco

```python
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
```

Instancia o cliente Supabase com a URL do projeto e a chave de API. A chave utilizada pode ser a `anon key` (sujeita às políticas de Row-Level Security) ou a `service_role key` (acesso administrativo irrestrito), conforme configurado no `.env`.

### 3. Leitura do arquivo de entrada

```python
json_path = _RAIZ / "data" / "jsons" / "nomes_empresas" / "nomes_empresas.json"
with open(json_path, encoding="utf-8") as f:
    dados = json.load(f)
```

Abre e desserializa o JSON gerado pela etapa de coleta. O `encoding="utf-8"` garante a leitura correta de nomes com caracteres especiais. Cada elemento de `dados` segue a estrutura:

```json
{
  "startup": "Nome da Empresa",
  "titulo": "Título do artigo",
  "url": "https://...",
  "tags": []
}
```

### 4. Extração e deduplicação de nomes

```python
nomes_unicos = list({item["startup"] for item in dados if item.get("startup")})
registros = [{"nome": nome} for nome in sorted(nomes_unicos)]
```

Utiliza uma *set comprehension* para eliminar automaticamente nomes duplicados — situação comum quando uma mesma startup é mencionada em múltiplos artigos. O filtro `item.get("startup")` descarta entradas com o campo ausente ou nulo. Os registros são ordenados alfabeticamente antes do envio.

### 5. Upsert na tabela `empresas`

```python
response = (
    supabase.table("empresas")
    .upsert(registros, on_conflict="nome")
    .execute()
)
```

Envia todos os registros em uma única operação de upsert. O parâmetro `on_conflict="nome"` instrui o PostgreSQL a detectar conflitos pela coluna `nome` (que possui constraint `UNIQUE`) e, em caso de duplicata, manter o registro existente sem modificações. Isso equivale à seguinte instrução SQL:

```sql
INSERT INTO empresas (nome)
VALUES ('Empresa A'), ('Empresa B'), ...
ON CONFLICT (nome) DO UPDATE SET nome = EXCLUDED.nome;
```

O atributo `response.data` contém os registros afetados (inseridos e atualizados) retornados pelo Supabase após a execução.

---

## Dados Processados

| Aspecto | Detalhe |
|---|---|
| **Arquivo de entrada** | `data/jsons/nomes_empresas/nomes_empresas.json` |
| **Campo consumido** | `startup` (nome da empresa) |
| **Campos ignorados** | `titulo`, `url`, `tags` |
| **Tabela de destino** | `empresas` |
| **Campo gravado** | `nome` (text UNIQUE NOT NULL) |

---

## Relação com Outros Arquivos

Este script é um dos dois responsáveis pela carga inicial a partir do mesmo JSON de coleta:

| Script | Tabela destino | Conteúdo enviado |
|---|---|---|
| [`upload_empresas.py`](../src/interacoes_banco/upload_empresas.py) | `empresas` | Nome único de cada startup |
| [`upload_nomes_empresas.py`](../src/interacoes_banco/upload_nomes_empresas.py) | `nomes_empresas` | Todos os artigos completos (startup + titulo + url + tags) |

A tabela `empresas` resultante serve como catálogo mestre do pipeline: todos os módulos de coleta, enriquecimento e recomendação referenciam seus registros via chave estrangeira (`empresa_id`). O script [`nova_empresa.py`](../src/nova_empresa.py) utiliza o mesmo mecanismo de upsert para inserir manualmente uma empresa e disparar as 10 etapas de processamento subsequentes.

---

## Pontos de Atenção

**Volume de registros por requisição**
Todos os registros são enviados ao Supabase em uma única requisição HTTP, sem paginação ou divisão em lotes. Para volumes muito elevados de startups, essa abordagem pode atingir limites de tamanho de payload da API REST.

**Carregamento de credenciais em nível de módulo**
A chamada `load_dotenv()` é executada no momento em que o módulo é importado. Caso o arquivo `.env` esteja ausente ou com variáveis incompletas, a ausência das credenciais será percebida somente quando a função `create_client()` for chamada, o que pode dificultar o diagnóstico do problema.

**Caminho do arquivo de entrada fixo no código**
O caminho para `nomes_empresas.json` é definido diretamente no código. Caso o arquivo não exista no local esperado, o script falhará com `FileNotFoundError`, sem possibilidade de configuração alternativa por parâmetro ou variável de ambiente.
