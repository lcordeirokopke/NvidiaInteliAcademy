# Dashboard — Guia de Uso e Visualização

O dashboard é uma aplicação Streamlit (`dashboard.py`) que consome os dados gerados pelo pipeline e os apresenta em páginas navegáveis. Para iniciá-lo:

```bash
python nvidia.py
# ou diretamente:
.venv\Scripts\streamlit.exe run dashboard.py
```

---

## Estrutura geral

A interface é dividida em duas áreas:

**Sidebar (esquerda)**
- Campo de busca global por nome de empresa — filtra a página ativa em tempo real
- Menu de navegação com rádio entre as páginas
- Botão **▶ Executar Pipeline** no rodapé — abre a tela de execução do pipeline

**Área principal (direita)**
- Conteúdo da página selecionada

---

## Páginas

### Empresas

Página principal do dashboard. Exibe as startups que já receberam recomendações de tecnologia NVIDIA geradas pelo LangGraph.

**Métricas de topo**
- Total de empresas com recomendação
- Tecnologia NVIDIA mais recomendada entre todas as empresas
- Número de setores distintos representados

**Seletor de empresa**
Dropdown com os nomes de todas as empresas. Ao selecionar uma, carrega o perfil completo e os outputs dos 4 agentes LLM.

**Seções do perfil**

| Seção | Conteúdo |
|---|---|
| Identidade | CNPJ, razão social, situação na Receita Federal, município/UF, CNAE, porte, capital social, natureza jurídica, domínio, ano de fundação |
| Produto e Mercado | Descrição do produto, modelo de negócio (B2B/B2C/B2B2C), mercado alvo, setor, subdomínio Gupy, programas de aceleração |
| Uso de Inteligência Artificial | Descrição do uso de IA, tipo de IA, se IA é o core product, se o produto está em produção, score e nível de maturidade |
| Síntese Executiva | Resumo executivo (LLM 2), impacto principal, diferencial competitivo, investimento estimado, próximo passo |
| Tecnologias Recomendadas | Lista de tecnologias NVIDIA com justificativa contextualizada (LLM 1) e links de fontes |
| Roadmap de Adoção | Tecnologia prioritária, plano de ações em 30/60/90 dias, dependências e métrica de sucesso (LLM 3) |
| Kit de Início | Por tecnologia: container NGC, tutorial de entrada, créditos Inception e tempo estimado para primeiro resultado (LLM 4) |
| Detalhes Técnicos | Query semântica enviada ao Qdrant, versão da base de conhecimento e tabela dos chunks reranqueados (diagnóstico de retrieval) |

---

### Uso de IA

Lista todas as startups aprovadas pelo filtro de IA (`empresas_uso_ia`), independentemente de já terem recomendação gerada.

**Métricas de topo**
- Total de empresas aprovadas
- Quantidade classificadas como `ai-native`
- Score médio de maturidade de IA (0–10)
- Quantidade com produto de IA já em produção

**Filtros**
- Setor (multiselect — valores dinâmicos do banco)
- Tipo de IA (multiselect — valores dinâmicos do banco)
- Nível de maturidade (multiselect — ai-native, ai-first, ai-enabled, ai-adjacent)
- Situação de coleta (selectbox)

**Tabela**
Exibe empresa, setor, tipo de IA, nível de maturidade, score (barra de progresso 0–10) e situação de coleta. O contador abaixo dos filtros mostra quantas empresas estão sendo exibidas.

**Painel de detalhes**
Dropdown abaixo da tabela. Ao selecionar uma empresa, abre um expander com três sub-seções: Identidade, Produto e Mercado, e Uso de Inteligência Artificial.

---

### Pendentes

Lista as empresas aprovadas pelo filtro de IA que estão com `situacao_coleta = 'informação pendente'` — ou seja, algum campo obrigatório (CNPJ, produto, setor, tipo de IA, etc.) ainda não foi preenchido, impedindo que o pipeline de recomendação as processe.

A página exibe uma tabela completa com todos os campos disponíveis, incluindo checkboxes para `ia_e_core_product` e `produto_ia_lancado`, e barra de progresso para o score de maturidade.

> Campos como Programa de Aceleração e Gupy costumam aparecer em branco — isso é esperado e não é o que determina a pendência.

#### Reprocessar empresa pendente

Ferramenta integrada na parte inferior da página que permite resolver pendências sem precisar abrir um terminal.

**Como usar:**
1. Selecione a empresa no dropdown — os campos ainda sem valor são exibidos abaixo
2. Escolha a partir de qual passo reprocessar (todos os passos seguintes também rodam automaticamente)
3. Clique em **Avançar**, confirme e clique em **Executar**
4. O sistema roda os mesmos módulos do pipeline original e tenta preencher os campos ausentes automaticamente
5. Se após a execução algum campo ainda ficar vazio, um formulário aparece para preenchimento manual
6. Ao salvar, os dados vão diretamente para o banco e o score de maturidade é recalculado

**Passos disponíveis**

| Passo | Campos preenchidos |
|---|---|
| Identidade (CNPJ + BrasilAPI) | cnpj, razão social, situação RF, município, UF, CNAE, porte, capital social, natureza jurídica, ano de fundação |
| Produto principal | produto |
| Uso de IA | uso_ia_descricao |
| IA é o core product? | ia_e_core_product |
| Tipo de IA | ia_tipo |
| Modelo de negócio | modelo_negocio |
| Produto de IA já lançado? | produto_ia_lancado |
| Setor de atuação | setor |
| Mercado-alvo geográfico | mercado_alvo |
| Score e nível de maturidade | score_maturidade_ia, nivel_maturidade_ia |

**Formulário de preenchimento manual**

Quando o pipeline não consegue preencher um campo automaticamente (site sem informação, API indisponível, etc.), o formulário exibe cada campo com o widget adequado ao seu tipo:
- Campos booleanos (`ia_e_core_product`, `produto_ia_lancado`): radio Sim / Não / Deixar em branco
- Campos numéricos (`ano_fundacao`, `capital_social`): número inteiro
- Campos com lista fechada de valores (`ia_tipo`, `setor`, `modelo_negocio`, etc.): selectbox com as opções válidas
- Campos de texto livre: campo de texto

Um preview dos campos e valores a salvar é exibido antes do botão "Salvar e Concluir". Ao salvar, o banco é atualizado e `define_maturidade` roda automaticamente para recalcular `score_maturidade_ia`, `nivel_maturidade_ia` e `situacao_coleta`. Se todos os campos obrigatórios forem preenchidos, a empresa sai da lista de pendentes e fica elegível para geração de recomendações NVIDIA na próxima execução do pipeline.

**Estados da tela**

| Estado | O que aparece |
|---|---|
| Início | Dropdown de empresa + campos pendentes + dropdown de passo inicial + botão Avançar |
| Confirmar | Resumo da operação + botões Executar / Voltar |
| Rodando | Spinner enquanto os passos executam |
| Manual | Log colapsado + formulário de preenchimento por tipo de campo |
| Concluído | Mensagem de sucesso + log completo + botão para reprocessar outra empresa |

---

### Excluídas

Lista as empresas que foram coletadas pelo pipeline mas **não atingiram pontuação suficiente** nos sinais de uso de IA e foram descartadas antes do enriquecimento.

**Métricas de topo**
- Total de empresas excluídas
- Pontuação média
- Média de sinais de IA encontrados

**Tabela**
Empresa, site (clicável), pontuação (barra de progresso), sinais encontrados vs. total verificado e data de avaliação. Ordenada da menor para a maior pontuação.

**Painel de detalhes**
Dropdown que abre um expander com site, pontuação, data de avaliação e o detalhamento das camadas de sinais avaliadas (✅ encontrado / ❌ não encontrado).

#### Atualizar domínio

Ferramenta exibida abaixo do expander de detalhes ao selecionar uma empresa. Permite corrigir o domínio cadastrado caso esteja errado ou ausente, e opcionalmente re-executar o pipeline de sinais_ia para reclassificar a empresa com o novo domínio.

**Como usar:**
1. Selecione uma empresa no dropdown "Ver detalhes de:"
2. A seção "Atualizar domínio" aparece abaixo do expander de detalhes
3. Informe o novo domínio no campo de texto (pode colar a URL completa — o `https://` é removido automaticamente)
4. Marque ou desmarque a opção de re-executar o pipeline de sinais_ia
5. Clique em **Salvar**

**O que acontece ao salvar:**
- O domínio é validado (formato `empresa.com.br`) — se inválido, um erro é exibido e nada é gravado
- O novo domínio é gravado em `empresas.dominio` e espelhado em `empresas_uso_ia.dominio`
- Se a opção de re-execução estiver marcada, o pipeline de sinais_ia roda em sequência: gupy_vagas → institucional → imprensa → neofeed → filtro_ia, podendo reclassificar a empresa (inclusive aprovando-a se os novos sinais forem suficientes)
- O log completo do pipeline é exibido colapsado ao final

**Estados da tela**

| Estado | O que aparece |
|---|---|
| Formulário | Domínio atual + campo de texto + checkbox de re-execução + botão Salvar |
| Rodando | Spinner enquanto o pipeline de sinais_ia executa |
| Concluído | Mensagem de sucesso + log colapsado + botão para atualizar outro domínio |

---

### Resumo Geral

Painel de visão agregada — primeira página exibida ao abrir o dashboard. Todas as métricas são gerais; nenhuma informação é específica por empresa.

**Funil de análise** — 5 métricas em linha que contam cada etapa do pipeline:
- Empresas coletadas
- IA detectada
- Excluídas (não atingiram pontuação mínima de sinais de IA)
- Perfil completo (situação de coleta = `completo`)
- Recomendação NVIDIA gerada

**Maturidade de IA** — 6 métricas agregadas das empresas aprovadas:
- Contagem por nível: ai-native, ai-first, ai-enabled, ai-adjacent
- Score médio geral (0–10)
- Quantidade com IA como core product

**Perfil tecnológico e comercial** — grade 2×2 com tabelas de distribuição:

| Posição | Conteúdo |
|---|---|
| Linha 1, coluna 1 | Tipo de IA (NLP/LLM, Visão Computacional, IA Generativa, etc.) |
| Linha 1, coluna 2 | Modelo de negócio (B2B, B2C, B2B2C) |
| Linha 2, coluna 1 | Mercado-alvo (Brasil, LATAM, Global) |
| Linha 2, coluna 2 | Produto de IA em produção vs em desenvolvimento |

**Setores com mais startups de IA** — tabela com barra de progresso proporcional, ordenada do setor com mais para o com menos empresas.

**Tecnologias NVIDIA mais recomendadas** — ranking das tecnologias que mais aparecem nas recomendações geradas pelos agentes LangGraph, com barra de progresso. Só aparece quando há recomendações no banco.

---

## Executar Pipeline

Acessível pelo botão **▶ Executar Pipeline** no rodapé da sidebar. Toma conta da área principal enquanto está ativo.

**Estados da tela**

| Estado | O que aparece |
|---|---|
| Idle | Descrição do pipeline + botão "Executar Pipeline" |
| Running | Aviso de execução em andamento + log ao vivo (últimas 40 linhas do stdout do `app.py`) |
| Done | Mensagem de sucesso + log completo colapsado + botões "Ver Resultados" e "Executar Novamente" |
| Error | Mensagem de erro + log completo expandido + botão "Tentar Novamente" |

O pipeline executa os 16 passos do `app.py` em sequência (coleta Neofeed → filtro → uploads → domínio → Gupy → vagas → institucional → imprensa → Neofeed tag → filtro IA → seed → identidade → maturidade → situação → recomendações NVIDIA). O log é atualizado linha a linha em tempo real.

Ao clicar em "Ver Resultados", a tela volta automaticamente para a página **Empresas** com os dados atualizados.

> A execução não pode ser interrompida pela interface — para parar, encerre o processo no terminal.

---

## Cache de dados

Todas as consultas ao Supabase têm cache de 2 minutos (`ttl=120`). Isso significa que após o pipeline terminar, os novos dados podem levar até 2 minutos para aparecer no dashboard. Recarregar a página manualmente força a renovação do cache.

---

## Busca global

O campo "Filtrar por nome..." no topo da sidebar aplica um filtro de texto (case-insensitive) na página ativa. Funciona nas páginas Empresas, Pendentes, Excluídas e Uso de IA. Não tem efeito na tela do Pipeline.
