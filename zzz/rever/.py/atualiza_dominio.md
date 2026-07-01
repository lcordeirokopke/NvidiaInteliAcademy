# atualiza_dominio.py

**Localização:** `src/interacoes_banco/atualiza_dominio.py`

**Como rodar:**
```bash
python -m src.interacoes_banco.atualiza_dominio
```

---

## O que é

Script interativo de uso manual para corrigir ou preencher o domínio oficial de uma empresa já cadastrada no banco. Após gravar o novo domínio, oferece a opção de re-executar o pipeline de coleta de `sinais_ia` para que os sinais reflitam o domínio correto.

---

## Quando usar

- O domínio foi preenchido errado durante a descoberta automática
- A empresa mudou de domínio
- O domínio ficou NULL e o pipeline não conseguiu descobrir automaticamente
- Quer forçar nova coleta de sinais (institucional, vagas, imprensa) após corrigir o domínio

---

## Quem chama

Chamado **manualmente pelo operador** — nunca pelo pipeline automático. Não é invocado por `app.py`, `nova_empresa.py` nem `inicia_aprofundamento.py`.

---

## Fluxo interativo

```
1. Carrega todas as empresas da tabela 'empresas', ordenadas por nome
2. Exibe lista numerada com:
     - nome da empresa
     - domínio atual (ou "—" se NULL)

3. Operador escolhe a empresa pelo número (ou 'q' para sair)

4. Exibe os dados atuais da empresa (nome, domínio)

5. Operador digita o novo domínio
     - aceita formato simples:  empresa.com.br
     - aceita URL completa:     https://empresa.com.br  (protocolo removido automaticamente)
     - 'v' para voltar à lista sem alterar nada

6. Confirma com 's/n'

7. Grava o domínio em dois lugares:
     a. empresas.dominio         (registro principal)
     b. empresas_uso_ia.dominio  (espelhado, se a linha existir)

8. Pergunta se quer re-executar o pipeline de sinais_ia ('s/n')
     - 's' → roda os 5 passos abaixo para a empresa
     - 'n' → encerra sem reprocessar

9. Loop volta para a lista
```

---

## Pipeline de sinais_ia re-executado (quando confirmado)

| Passo | Módulo | Camada em sinais_ia |
|-------|--------|---------------------|
| 1 | `descobre_gupy_vagas.pesquisar(nome=)` | `gupy_vagas` |
| 2 | `descobre_institucional.pesquisar(nome=)` | `institucional` |
| 3 | `descobre_imprensa.pesquisar(nome=)` | `imprensa` |
| 4 | `analisa_neofeed.classificar(nome=)` | `neofeed` |
| 5 | `filtro_ia.filtrar(filtrar_nome=)` | — (consolida e grava em `avaliacoes_ia`) |

A ordem é a mesma do `nova_empresa.py`. O `filtro_ia` sempre roda por último para recalcular o veredito de uso de IA com base nos sinais atualizados.

---

## Onde os dados ficam

**Supabase:**
- `empresas.dominio` — atualizado direto
- `empresas_uso_ia.dominio` — espelhado (UPDATE silencioso se a linha não existir)
- `sinais_ia` — re-populado pelos passos de re-coleta
- `avaliacoes_ia` — veredito recalculado pelo `filtro_ia`

---

## Diferença em relação aos outros arquivos manuais

| | `atualiza_dominio.py` | `atualiza_cnpj.py` | `reprocessa_empresa.py` |
|---|---|---|---|
| **O que corrige** | `empresas.dominio` | `empresas_uso_ia.cnpj` | Qualquer campo NULL de `empresas_uso_ia` |
| **Tabela principal alterada** | `empresas` (+ espelho em `empresas_uso_ia`) | `empresas_uso_ia` | `empresas_uso_ia` |
| **Re-executa pipeline** | `sinais_ia` (opcional) | Sim — `enriquece_identidade` | Sim — passos escolhidos pelo operador |
| **Roda `define_maturidade` ao final** | Não | Não | Sempre |

---

## Observações

- A validação do domínio aceita qualquer hostname com pelo menos um ponto e TLD de 2+ letras. Não valida se o domínio está acessível — só o formato.
- O espelho em `empresas_uso_ia.dominio` usa `UPDATE ... WHERE empresa_id = ?`. Se a empresa ainda não tiver linha em `empresas_uso_ia`, a instrução não faz nada (sem erro).
- Re-executar o pipeline de `sinais_ia` pode sobrescrever sinais anteriores se os módulos fizerem upsert — verifique o comportamento de cada módulo antes de reprocessar em produção.
