Plano de Ação — Frontend Streamlit
1. Configuração Inicial
Dependências a instalar

pip install streamlit supabase pandas


Variáveis de ambiente / secrets
O Streamlit usa .streamlit/secrets.toml para secrets locais. Crie o arquivo (não commitar):


# .streamlit/secrets.toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "eyJ..."
Imports e conexão no topo do arquivo

import streamlit as st
import pandas as pd
from supabase import create_client

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )

@st.cache_data(ttl=120)  # cache de 2 min; boto para desenvolvimento, aumentar em prod
def fetch_empresas() -> pd.DataFrame:
    rows = get_supabase().table("empresas").select("*").order("created_at", desc=True).execute().data
    return pd.DataFrame(rows)

@st.cache_data(ttl=120)
def fetch_empresas_uso_ia() -> pd.DataFrame:
    rows = get_supabase().table("empresas_uso_ia").select("*").execute().data
    return pd.DataFrame(rows)

@st.cache_data(ttl=120)
def fetch_recomendacoes() -> pd.DataFrame:
    rows = get_supabase().table("recomendacoes_nvidia").select("*").order("gerado_em", desc=True).execute().data
    return pd.DataFrame(rows)
Por que @st.cache_resource para o cliente e @st.cache_data para os dados?

O cliente Supabase é uma conexão (objeto com estado); cache_resource garante uma única instância. Os dados são serializáveis; cache_data pode reinvalidá-los automaticamente via ttl.

2. Estrutura de Código Sugerida
Arquivo sugerido: dashboard.py (ou streamlit_app.py).


dashboard.py
├── get_supabase()               — singleton de conexão
├── fetch_empresas()             — dados da aba 1
├── fetch_empresas_uso_ia()      — dados da aba 2
├── fetch_recomendacoes()        — dados da aba 3
│
├── render_tab_empresas(df)      — layout da aba 1
├── render_tab_uso_ia(df)        — layout da aba 2
├── render_tab_recomendacoes(df) — layout da aba 3
│
└── main()                       — st.tabs + orquestração
Esqueleto da main():


def main():
    st.set_page_config(page_title="NVIDIA Intel Academy", layout="wide")
    st.title("NVIDIA · Radar de Startups")

    tab1, tab2, tab3 = st.tabs([
        "Empresas Coletadas",
        "Uso de IA Detectado",
        "Recomendações NVIDIA",
    ])

    with tab1:
        render_tab_empresas(fetch_empresas())
    with tab2:
        render_tab_uso_ia(fetch_empresas_uso_ia())
    with tab3:
        render_tab_recomendacoes(fetch_recomendacoes())

if __name__ == "__main__":
    main()
3. Layout e Componentes por Aba
Aba 1 — Empresas Coletadas
Objetivo: visão rápida do universo coletado (tabela empresas).

Colunas da tabela: id, nome, dominio, gupy_subdominio, created_at

Layout sugerido:


[Métrica: Total de empresas]   [Métrica: Com domínio]   [Métrica: Com Gupy]
─────────────────────────────────────────────────────────────────────
[🔍 Filtro de texto: "Buscar empresa..."]
─────────────────────────────────────────────────────────────────────
[st.dataframe — tabela completa, colunas configuradas]

def render_tab_empresas(df: pd.DataFrame):
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Empresas", len(df))
    col2.metric("Com Domínio", df["dominio"].notna().sum())
    col3.metric("Com Gupy", df["gupy_subdominio"].notna().sum())

    busca = st.text_input("Buscar empresa", placeholder="Nome ou domínio...")
    if busca:
        mask = df["nome"].str.contains(busca, case=False, na=False) | \
               df["dominio"].str.contains(busca, case=False, na=False)
        df = df[mask]

    st.dataframe(
        df[["id", "nome", "dominio", "gupy_subdominio", "created_at"]],
        use_container_width=True,
        column_config={
            "dominio": st.column_config.LinkColumn("Site"),
            "created_at": st.column_config.DatetimeColumn("Coletada em", format="DD/MM/YYYY HH:mm"),
        },
        hide_index=True,
    )
Aba 2 — Uso de IA Detectado
Objetivo: explorar as startups aprovadas com todos os campos de maturidade (tabela empresas_uso_ia).

Layout sugerido:


[Métrica: Total aprovadas]  [Métrica: AI-Native]  [Métrica: Score médio]  [Métrica: Produto IA em produção]
──────────────────────────────────────────────────────────────────────────────────────────────────────────
[Filtros em linha]
  Setor: [multiselect]   Tipo de IA: [multiselect]   Maturidade: [multiselect]   Situação: [selectbox]
──────────────────────────────────────────────────────────────────────────────────────────────────────────
[st.dataframe — colunas principais + barra de score]

[Expandable "Ver detalhes" por empresa selecionada]

def render_tab_uso_ia(df: pd.DataFrame):
    # Métricas de topo
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aprovadas", len(df))
    c2.metric("AI-Native", (df["nivel_maturidade_ia"] == "ai-native").sum())
    c3.metric("Score Médio", f"{df['score_maturidade_ia'].mean():.1f}/10")
    c4.metric("Produto em Produção", df["produto_ia_lancado"].sum())

    # Filtros
    f1, f2, f3, f4 = st.columns(4)
    setores   = f1.multiselect("Setor", sorted(df["setor"].dropna().unique()))
    tipos_ia  = f2.multiselect("Tipo de IA", sorted(df["ia_tipo"].dropna().unique()))
    maturidade = f3.multiselect("Maturidade", ["ai-native","ai-first","ai-enabled","ai-adjacent"])
    situacao  = f4.selectbox("Situação", ["Todas"] + df["situacao_coleta"].dropna().unique().tolist())

    mask = pd.Series([True] * len(df), index=df.index)
    if setores:    mask &= df["setor"].isin(setores)
    if tipos_ia:   mask &= df["ia_tipo"].isin(tipos_ia)
    if maturidade: mask &= df["nivel_maturidade_ia"].isin(maturidade)
    if situacao != "Todas": mask &= df["situacao_coleta"] == situacao
    df = df[mask]

    # Tabela principal
    cols_exibir = ["empresa_id","nome_fantasia","setor","ia_tipo",
                   "nivel_maturidade_ia","score_maturidade_ia","situacao_coleta"]
    st.dataframe(
        df[cols_exibir],
        use_container_width=True,
        column_config={
            "score_maturidade_ia": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=10, format="%d"
            ),
            "nivel_maturidade_ia": st.column_config.TextColumn("Maturidade"),
        },
        hide_index=True,
    )

    # Detalhe de uma empresa selecionada
    empresas_lista = df["nome_fantasia"].dropna().tolist()
    empresa_sel = st.selectbox("Ver detalhes de:", ["—"] + empresas_lista)
    if empresa_sel != "—":
        row = df[df["nome_fantasia"] == empresa_sel].iloc[0]
        with st.expander(f"Perfil completo — {empresa_sel}", expanded=True):
            d1, d2 = st.columns(2)
            d1.write(f"**CNPJ:** {row.get('cnpj','—')}")
            d1.write(f"**Razão Social:** {row.get('razao_social','—')}")
            d1.write(f"**Município/UF:** {row.get('municipio','—')}/{row.get('uf','—')}")
            d1.write(f"**CNAE:** {row.get('cnae_principal','—')}")
            d2.write(f"**Produto:** {row.get('produto','—')}")
            d2.write(f"**Uso de IA:** {row.get('uso_ia_descricao','—')}")
            d2.write(f"**IA é core product?** {'Sim' if row.get('ia_e_core_product') else 'Não'}")
            d2.write(f"**Programas:** {row.get('programa_aceleracao','—')}")
Aba 3 — Recomendações NVIDIA
Objetivo: exibir o output consolidado dos 4 agentes LangGraph (tabela recomendacoes_nvidia).

Esta é a aba mais rica — os campos explicacao, sintese_executiva, roadmap e kit_inicio são JSONB com estrutura aninhada.

Layout sugerido:


[Métrica: Empresas com recomendação]  [Métrica: Tecnologia mais recomendada]  [Métrica: Score médio (via join)]
──────────────────────────────────────────────────────────────────────────────────────────────────────────
[Seletor: Empresa]
──────────────────────────────────────────────────────────────────────────────────────────────────────────
[Card: Síntese Executiva — para CEO/Account Manager NVIDIA]
[Expandable: Tecnologias Recomendadas (LLM 1)]
[Expandable: Roadmap 30/60/90 dias (LLM 3)]   [Expandable: Kit de Início (LLM 4)]
[Expandable: Detalhes Técnicos de Retrieval — chunks reranqueados, query semântica]

def render_tab_recomendacoes(df: pd.DataFrame):
    if df.empty:
        st.info("Nenhuma recomendação gerada ainda.")
        return

    st.metric("Empresas com Recomendação", len(df))

    # Seletor de empresa
    empresa_id = st.selectbox(
        "Selecionar empresa",
        df["empresa_id"].tolist(),
        format_func=lambda eid: f"Empresa #{eid}"  # idealmente fazer join com nome
    )
    row = df[df["empresa_id"] == empresa_id].iloc[0]

    sintese    = row.get("sintese_executiva") or {}
    explicacao = row.get("explicacao") or {}
    roadmap    = row.get("roadmap") or {}
    kit        = (row.get("kit_inicio") or {}).get("kit", [])

    # ── Card: Síntese Executiva ──────────────────────────────────────────
    st.subheader("Síntese Executiva")
    st.info(sintese.get("resumo", "—"))
    c1, c2 = st.columns(2)
    c1.write(f"**Impacto Principal:** {sintese.get('impacto_principal','—')}")
    c1.write(f"**Diferencial Competitivo:** {sintese.get('diferencial_competitivo','—')}")
    c2.write(f"**Investimento Estimado:** {sintese.get('investimento_estimado','—')}")
    c2.write(f"**Próximo Passo:** {sintese.get('proximo_passo','—')}")

    # ── Tecnologias Recomendadas (LLM 1) ────────────────────────────────
    with st.expander("Tecnologias Recomendadas", expanded=True):
        for tech in explicacao.get("tecnologias", []):
            st.markdown(f"**{tech['tecnologia']}** — {tech['justificativa']}")
        fontes = explicacao.get("fontes", [])
        if fontes:
            st.caption("Fontes: " + " · ".join(fontes))

    # ── Roadmap 30/60/90 dias (LLM 3) ───────────────────────────────────
    with st.expander("Roadmap de Adoção"):
        st.write(f"**Tecnologia Prioritária:** {roadmap.get('tecnologia_prioritaria','—')}")
        st.write(roadmap.get('justificativa_prioridade',''))
        plano = roadmap.get("plano", {})
        r1, r2, r3 = st.columns(3)
        r1.markdown("**30 dias**\n" + "\n".join(f"- {a}" for a in plano.get("30_dias",[])))
        r2.markdown("**60 dias**\n" + "\n".join(f"- {a}" for a in plano.get("60_dias",[])))
        r3.markdown("**90 dias**\n" + "\n".join(f"- {a}" for a in plano.get("90_dias",[])))
        if roadmap.get("metrica_de_sucesso"):
            st.success(f"Métrica de Sucesso: {roadmap['metrica_de_sucesso']}")

    # ── Kit de Início (LLM 4) ────────────────────────────────────────────
    with st.expander("Kit de Início"):
        for item in kit:
            st.markdown(f"### {item.get('tecnologia','')}")
            st.code(item.get("container_ngc",""), language="bash")
            st.write(f"Tutorial: {item.get('tutorial_entrada','—')}")
            st.write(f"Créditos Inception: {item.get('creditos_inception','—')}")
            st.caption(f"Tempo estimado para primeiro resultado: {item.get('tempo_primeiro_resultado','—')}")
            st.divider()

    # ── Debug de retrieval ────────────────────────────────────────────────
    with st.expander("Detalhes Técnicos (Retrieval)"):
        st.caption(f"Query semântica: `{row.get('query','—')}`")
        chunks = row.get("chunks_reranqueados") or []
        if chunks:
            st.dataframe(pd.DataFrame(chunks), use_container_width=True, hide_index=True)
4. Próximos Passos Imediatos
Ordem de execução sugerida:

#	Tarefa	Prioridade
1	Criar dashboard.py com a estrutura de st.tabs e as funções de fetch	Alta
2	Adicionar .streamlit/secrets.toml com credenciais Supabase e incluí-lo no .gitignore	Alta
3	Implementar a Aba 1 (render_tab_empresas) — mais simples, serve de aquecimento	Alta
4	Implementar a Aba 2 (render_tab_uso_ia) com filtros e expander de detalhes	Alta
5	Fazer join no fetch de recomendações para trazer nome_fantasia de empresas_uso_ia	Média
6	Implementar a Aba 3 (render_tab_recomendacoes) com os 4 blocos de agentes	Alta
7	Adicionar botão "Atualizar dados" com st.cache_data.clear() em cada aba	Média
8	Testar com dados reais no Supabase e ajustar tipos de coluna (JSONB pode vir como dict ou str)	Alta
Atenção ao ponto 8: os campos JSONB (explicacao, sintese_executiva, roadmap, kit_inicio) podem chegar como dict Python já parseado pelo supabase-py, ou como string JSON dependendo da versão. Use um helper de segurança:


import json

def safe_json(val):
    if isinstance(val, dict): return val
    if isinstance(val, str):
        try: return json.loads(val)
        except: return {}
    return {}


Resumo: o trabalho começa criando dashboard.py com o esqueleto de tabs e as funções de fetch cacheadas. Aba 1 entra em produção rapidamente; Aba 3 é a mais complexa mas o código de renderização dos 4 agentes já está mapeado acima sobre a estrutura exata do JSONB de cada LLM.