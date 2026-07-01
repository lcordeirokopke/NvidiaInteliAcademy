MATURIDADE

## Campos futuros que elevariam a qualidade do framework

Se coletados, estes campos agregariam dimensões atualmente não mensuráveis:

| Campo proposto | Tipo | O que mediria |
|---|---|---|
| `ia_proprio_modelo` | boolean | A empresa treina/faz fine-tuning de modelo próprio vs usa apenas API. Maior diferenciador de profundidade técnica real. |
| `receita_recorrente_ia` | boolean | Já tem receita recorrente de produto de IA (não apenas pilotos). Mede execução comercial, não apenas técnica. |
| `equipe_ia_propria` | boolean | Tem cientistas ou engenheiros de ML internos. Diferencia "empresa que faz IA" de "empresa que usa IA via API". |

Esses três campos tocariam na distinção central entre usar IA como insumo e construir IA como competência — o coração do conceito ai-native.

---
PROFUNDIDADE TECNICA NO empresas_uso_ia

Se no futuro você quiser reintroduzir profundidade técnica, basta adicionar um campo como nivel_tecnico (wrapper, fine-tuning, modelo-proprio) e um peso correspondente.

---
A´POS COLETA TOTAL -RERANKING ETC 

Agente 5 — Perguntas de Qualificação
As perguntas de qualificação por tecnologia são altamente previsíveis. Para NIM: "qual o tamanho do modelo?", "qual latência máxima?", "tem GPU em produção?". Essas perguntas não mudam significativamente de startup para startup dentro do mesmo ia_tipo. Um LLM para gerar perguntas que são essencialmente estáticas é desperdício de chamada.

Alternativa mais simples: um dicionário tecnologia → perguntas mantido manualmente ou gerado uma vez e armazenado. Mais confiável, zero custo por requisição, zero alucinação.

Veredicto: não adicionar como agente. Sistema de templates.

---

## LLM 3 — Agente de Casos de Sucesso (Inception Portfolio)

Removido do plano principal por enquanto. Depende de infraestrutura que ainda não existe.

**Pergunta que responde:** quem já fez isso? Quais startups similares adotaram essas tecnologias e o que obtiveram?

**Entrada:** perfil + tecnologias recomendadas (output do LLM 1)
**Saída:** 1-3 casos de startups similares do portfolio Inception com resultado mensurável

**Posição original no grafo:** fan-out paralelo com o LLM 1 — mesma entrada, base de dados diferente. O fan-in aguardava explicação + casos antes de chamar a síntese executiva.

**Por que é um agente e não uma extensão:** executa RAG em uma collection separada do Qdrant (`inception_cases`). A query é construída a partir das tecnologias recomendadas, não do perfil bruto.

**Pré-requisito bloqueante:** collection `inception_cases` no Qdrant com cases do portfolio NVIDIA Inception indexados com metadata de `setor`, `ia_tipo`, `tecnologia_usada`, `resultado`. Precisa ser construída do zero via scraping de cases no site NVIDIA, press releases e blog posts do Inception.

**Como reintroduzir quando estiver pronto:**
1. Criar e popular a collection `inception_cases` no Qdrant
2. Adicionar o nó `casos_de_sucesso` no grafo como fan-out paralelo ao LLM 1
3. Restaurar o fan-in para aguardar os dois outputs antes da síntese executiva
4. Adicionar `casos_sucesso: List[dict]` de volta ao `EstadoRecomendacao`
5. Adicionar `casos_sucesso` ao output final JSON

**Prompt:**

```
Com base nos casos de sucesso abaixo do portfolio NVIDIA Inception, identifique os mais
relevantes para a startup em questão. Priorize similaridade de setor, tecnologia e estágio.

Perfil da startup: {perfil}
Tecnologias recomendadas: {tecnologias}
Casos disponíveis: {chunks_inception}

Responda em JSON:
{
  "casos": [{
    "startup": "nome ou descrição",
    "setor": "...",
    "tecnologia_usada": "...",
    "resultado": "resultado mensurável obtido",
    "relevancia": "por que este caso é relevante para esta startup"
  }]
}
```