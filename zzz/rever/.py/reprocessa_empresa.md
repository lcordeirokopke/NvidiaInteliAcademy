# reprocessa_empresa.py

**Localização:** `src/dados_startups_selecionadas/manual/reprocessa_empresa.py`

**Como rodar:**
```bash
python -m src.dados_startups_selecionadas.manual.reprocessa_empresa
```

---

## O que é

Script interativo de uso manual para reprocessar campos NULL em empresas que já passaram pelo pipeline principal mas ficaram com dados incompletos. Ao escolher um passo, continua automaticamente pelos passos seguintes — igual ao `inicia_aprofundamento`, mas filtrado para uma empresa específica e com preenchimento manual como fallback quando a coleta automática falha.

---

## Quando usar

Após o pipeline principal (`app.py` ou `inicia_aprofundamento.py`) rodar e algumas empresas ficarem com `situacao_coleta = 'informação pendente'` porque campos obrigatórios não foram preenchidos automaticamente. Casos típicos:

- Site fora do ar durante a coleta → `produto` ou `uso_ia_descricao` ficou NULL
- CNPJ encontrado mas BrasilAPI não retornou `ano_fundacao`
- Gemini retornou `INCERTO` ou valor inválido → `ia_tipo` ou `ia_e_core_product` ficou NULL
- Empresa adicionada com dados parciais e precisa ter passos específicos reexecutados

---

## Quem chama

Chamado **manualmente pelo operador** — nunca pelo pipeline automático. Não é invocado por `app.py`, `nova_empresa.py` nem `inicia_aprofundamento.py`.

---

## Fluxo interativo

```
1. Carrega todas as empresas com pelo menos 1 campo NULL em empresas_uso_ia
2. Exibe lista numerada com:
     - nome da empresa
     - quantidade de campos NULL
     - situacao_coleta atual

3. Operador escolhe a empresa pelo número

4. Exibe:
     - quais campos estão NULL
     - os passos do pipeline com campos NULL (únicos que aparecem como opção)

5. Operador escolhe:
     - um passo específico → roda esse passo e todos os seguintes em sequência
     - "Apenas os passos com NULL" → roda só os passos listados, sem continuar além
     - 'v' para voltar à lista

6. Confirma com 's/n'

7. Para cada passo executado:
     a. Verifica se os campos do passo ainda estão NULL antes de rodar
        (pula automaticamente se já estiverem preenchidos)
     b. Roda o passo (scraping + Gemini)
     c. Verifica novamente quais campos ainda estão NULL após o passo
     d. Se ainda NULL → oferece preenchimento manual (ver seção abaixo)
     e. Continua para o próximo passo

8. Ao final, define_maturidade.classificar(nome=) sempre roda:
     - recalcula score e nível de maturidade
     - chama atualiza_situacao_coleta.atualizar()
       → sobe para 'completo' se todos os campos obrigatórios estiverem preenchidos
     (pulado apenas se o próprio passo escolhido já era o de maturidade)

9. Loop volta para a lista atualizada
```

---

## Preenchimento manual após falha do pipeline

Quando um passo automático não consegue preencher um campo (Gemini incerto, site inacessível, API com erro), o script detecta que o campo continua NULL e pergunta:

```
  [manual] O pipeline não preencheu: produto_ia_lancado
  Deseja preencher manualmente? (s/n):
```

Se o operador confirmar, o script solicita o valor campo a campo com validação por tipo:

| Tipo de campo | Comportamento |
|---|---|
| Boolean (`ia_e_core_product`, `produto_ia_lancado`) | `s = true / n = false` |
| Inteiro (`ano_fundacao`, `capital_social`) | digita número inteiro |
| Enum curto (≤ 6 opções: `ia_tipo`, `modelo_negocio`, `mercado_alvo`, `situacao_rf`) | opções exibidas inline, valida contra conjunto fechado |
| Enum longo (`setor`, 28 opções) | lista numerada — aceita número ou valor exato |
| Texto livre (`produto`, `uso_ia_descricao`, `razao_social` etc.) | digita livremente |
| Calculados (`score_maturidade_ia`, `nivel_maturidade_ia`) | nunca pedidos — gerados pelo `define_maturidade` |

Após confirmar os valores, o script grava no banco e segue para o próximo passo.

---

## Comportamento ao escolher um passo

**Escolher passo específico (ex: "Produto de IA já lançado?"):**
Expande automaticamente para todos os passos seguintes na ordem do pipeline. Passos com campos já preenchidos são pulados.

```
produto_ia_lancado → setor → mercado_alvo → define_maturidade
  ↑ escolhido       ↑ pula se ok   ↑ pula se ok   ↑ sempre roda
```

**Escolher "Apenas os passos com NULL":**
Roda somente os passos listados que têm campos NULL, sem continuar para os seguintes. Útil quando se quer reprocessar um conjunto específico sem disparar toda a cadeia.

---

## Mapeamento campo NULL → passo executado

| Campo(s) NULL | Passo executado |
|---|---|
| `cnpj`, `razao_social`, `situacao_rf`, `municipio`, `uf`, `cnae_principal`, `porte`, `capital_social`, `natureza_juridica`, `ano_fundacao` | `enriquece_identidade.enriquecer(nome=)` |
| `produto` | `produto.descobrir(nome=)` |
| `uso_ia_descricao` | `uso_ia.descobrir(nome=)` |
| `ia_e_core_product` | `ia_core_product.descobrir(nome=)` |
| `ia_tipo` | `ia_tipo.descobrir(nome=)` |
| `modelo_negocio` | `modelo_negocio.descobrir(nome=)` |
| `produto_ia_lancado` | `produto_ia_lancado.descobrir(nome=)` |
| `setor` | `define_setor.descobrir(nome=)` |
| `mercado_alvo` | `mercado_alvo.descobrir(nome=)` |
| `score_maturidade_ia`, `nivel_maturidade_ia` | `define_maturidade.classificar(nome=)` |

---

## Diferença em relação aos outros arquivos manuais

| | `reprocessa_empresa.py` | `atualiza_status.py` | `atualiza_cnpj.py` |
|---|---|---|---|
| **O que faz** | Roda o pipeline de coleta + fallback manual | Revisa `situacao_coleta` (preenche à mão ou define destino) | Preenche CNPJ manualmente e consulta BrasilAPI |
| **Quem preenche o dado** | Pipeline (scraping + Gemini) com fallback manual | Operador digita o valor | Operador digita o CNPJ |
| **Quando usar** | Falha de coleta — quer tentar novamente (com manual como fallback) | Pipeline rodou, campos ainda NULL, quer só preencher à mão ou definir destino | CNPJ não encontrado automaticamente |
| **Roda passos seguintes automaticamente** | Sim | Não | Não |
| **Roda define_maturidade ao final** | Sim, sempre | Não | Não |

### Ordem recomendada de uso após o pipeline

```
inicia_aprofundamento.py
    ↓
atualiza_cnpj.py          (se cnpj_pendente = TRUE)
    ↓
reprocessa_empresa.py     (tenta nova coleta + fallback manual por campo)
    ↓
atualiza_status.py        (se ainda pendente — define destino ou ignora)
```

---

## Observações

- Passos são pulados silenciosamente se todos os seus campos já estão preenchidos no banco no momento da execução.
- Cada módulo de coleta tem sua própria query interna (`produto IS NULL`, etc.) — se o campo foi preenchido pelo fallback manual, o módulo não reprocessa na próxima rodada.
- O script exibe empresas com `'empresa deve ser ignorada'` na lista — o operador decide se quer reprocessar mesmo assim.
