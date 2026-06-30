from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from supabase import create_client


# ── Conexão ────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


# ── Fetches com cache ──────────────────────────────────────────────────────────

@st.cache_data(ttl=120)
def fetch_empresas() -> pd.DataFrame:
    rows = get_supabase().table("empresas").select("*").order("created_at", desc=True).execute().data
    return pd.DataFrame(rows)


@st.cache_data(ttl=120)
def fetch_empresas_uso_ia() -> pd.DataFrame:
    rows = get_supabase().table("empresas_uso_ia").select("*").execute().data
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Traz o nome original de `empresas` para cobrir os casos em que nome_fantasia é NULL
    nomes = get_supabase().table("empresas").select("id, nome").execute().data
    df_nomes = pd.DataFrame(nomes).rename(columns={"id": "empresa_id", "nome": "nome_original"})
    df = df.merge(df_nomes, on="empresa_id", how="left")

    # nome_display: prefere nome_fantasia; cai para nome_original quando nulo
    df["nome_display"] = df["nome_fantasia"].where(df["nome_fantasia"].notna(), df["nome_original"])
    return df


@st.cache_data(ttl=120)
def fetch_recomendacoes() -> pd.DataFrame:
    rows = (
        get_supabase()
        .table("recomendacoes_nvidia")
        .select("*")
        .order("gerado_em", desc=True)
        .execute()
        .data
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Traz nome_display de empresas_uso_ia (já com fallback para nome original)
    df_uso = fetch_empresas_uso_ia()[["empresa_id", "nome_display"]]
    df = df.merge(df_uso, on="empresa_id", how="left")
    return df


# ── Helper para campos JSONB ───────────────────────────────────────────────────

def safe_json(val) -> dict | list:
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return {}
    return {}


# ── Abas (render functions — a implementar) ───────────────────────────────────

def render_tab_empresas(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("Nenhuma empresa coletada ainda.")
        return

    # Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Empresas", len(df))
    c2.metric("Com Domínio", int(df["dominio"].notna().sum()))
    c3.metric("Com Gupy", int(df["gupy_subdominio"].notna().sum()))

    st.divider()

    # Filtro de texto
    busca = st.text_input("Buscar", placeholder="Nome ou domínio...")
    if busca:
        mask = (
            df["nome"].str.contains(busca, case=False, na=False)
            | df["dominio"].str.contains(busca, case=False, na=False)
        )
        df = df[mask]
        st.caption(f"{len(df)} resultado(s) para '{busca}'")

    # Tabela
    st.dataframe(
        df[["id", "nome", "dominio", "gupy_subdominio", "created_at"]],
        use_container_width=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "nome": st.column_config.TextColumn("Empresa"),
            "dominio": st.column_config.LinkColumn("Site", display_text=r"https?://(.+)"),
            "gupy_subdominio": st.column_config.TextColumn("Subdomínio Gupy"),
            "created_at": st.column_config.DatetimeColumn(
                "Coletada em", format="DD/MM/YYYY HH:mm"
            ),
        },
        hide_index=True,
    )


def render_tab_uso_ia(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("Nenhuma empresa aprovada ainda.")
        return

    # Métricas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aprovadas", len(df))
    c2.metric("AI-Native", int((df["nivel_maturidade_ia"] == "ai-native").sum()))
    score_medio = df["score_maturidade_ia"].dropna()
    c3.metric("Score Médio", f"{score_medio.mean():.1f}/10" if not score_medio.empty else "—")
    c4.metric("Produto em Produção", int(df["produto_ia_lancado"].sum()))

    st.divider()

    # Filtros
    f1, f2, f3, f4 = st.columns(4)
    setores    = f1.multiselect("Setor", sorted(df["setor"].dropna().unique()))
    tipos_ia   = f2.multiselect("Tipo de IA", sorted(df["ia_tipo"].dropna().unique()))
    maturidade = f3.multiselect(
        "Maturidade", ["ai-native", "ai-first", "ai-enabled", "ai-adjacent"]
    )
    situacoes = df["situacao_coleta"].dropna().unique().tolist()
    situacao  = f4.selectbox("Situação", ["Todas"] + situacoes)

    mask = pd.Series([True] * len(df), index=df.index)
    if setores:     mask &= df["setor"].isin(setores)
    if tipos_ia:    mask &= df["ia_tipo"].isin(tipos_ia)
    if maturidade:  mask &= df["nivel_maturidade_ia"].isin(maturidade)
    if situacao != "Todas": mask &= df["situacao_coleta"] == situacao
    df_filtrado = df[mask]

    st.caption(f"{len(df_filtrado)} empresa(s) exibida(s)")

    # Tabela principal
    cols_exibir = [
        "empresa_id", "nome_display", "setor", "ia_tipo",
        "nivel_maturidade_ia", "score_maturidade_ia", "situacao_coleta",
    ]
    st.dataframe(
        df_filtrado[cols_exibir],
        use_container_width=True,
        column_config={
            "empresa_id":         st.column_config.NumberColumn("ID", width="small"),
            "nome_display":       st.column_config.TextColumn("Empresa"),
            "setor":              st.column_config.TextColumn("Setor"),
            "ia_tipo":            st.column_config.TextColumn("Tipo de IA"),
            "nivel_maturidade_ia": st.column_config.TextColumn("Maturidade"),
            "score_maturidade_ia": st.column_config.ProgressColumn(
                "Score IA", min_value=0, max_value=10, format="%d"
            ),
            "situacao_coleta":    st.column_config.TextColumn("Situação"),
        },
        hide_index=True,
    )

    st.divider()

    # Painel de detalhes
    nomes = df_filtrado["nome_display"].dropna().tolist()
    if not nomes:
        return

    empresa_sel = st.selectbox("Ver perfil completo de:", ["—"] + nomes)
    if empresa_sel == "—":
        return

    row = df_filtrado[df_filtrado["nome_display"] == empresa_sel].iloc[0]

    with st.expander(f"Perfil — {empresa_sel}", expanded=True):
        # Identidade
        st.markdown("##### Identidade")
        i1, i2, i3 = st.columns(3)
        i1.write(f"**CNPJ:** {row.get('cnpj') or '—'}")
        i1.write(f"**Razão Social:** {row.get('razao_social') or '—'}")
        i1.write(f"**Situação RF:** {row.get('situacao_rf') or '—'}")
        i2.write(f"**Município/UF:** {row.get('municipio') or '—'}/{row.get('uf') or '—'}")
        i2.write(f"**CNAE:** {row.get('cnae_principal') or '—'}")
        i2.write(f"**Porte:** {row.get('porte') or '—'}")
        cap = row.get("capital_social")
        i3.write(f"**Capital Social:** R$ {cap:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if cap else "**Capital Social:** —")
        i3.write(f"**Natureza Jurídica:** {row.get('natureza_juridica') or '—'}")
        i3.write(f"**Ano de Fundação:** {row.get('ano_fundacao') or '—'}")

        st.divider()

        # Produto e Mercado
        st.markdown("##### Produto e Mercado")
        p1, p2 = st.columns(2)
        p1.write(f"**Produto:** {row.get('produto') or '—'}")
        p1.write(f"**Modelo de Negócio:** {row.get('modelo_negocio') or '—'}")
        p1.write(f"**Mercado Alvo:** {row.get('mercado_alvo') or '—'}")
        p2.write(f"**Setor:** {row.get('setor') or '—'}")
        p2.write(f"**Domínio:** {row.get('dominio') or '—'}")
        p2.write(f"**Programas de Aceleração:** {row.get('programa_aceleracao') or '—'}")

        st.divider()

        # IA
        st.markdown("##### Uso de Inteligência Artificial")
        st.write(f"**Descrição:** {row.get('uso_ia_descricao') or '—'}")
        a1, a2, a3, a4 = st.columns(4)
        a1.write(f"**Tipo de IA:** {row.get('ia_tipo') or '—'}")
        a2.write(f"**IA é core product?** {'Sim' if row.get('ia_e_core_product') else 'Não'}")
        a3.write(f"**Produto IA em produção?** {'Sim' if row.get('produto_ia_lancado') else 'Não'}")
        a4.write(f"**Score de Maturidade:** {row.get('score_maturidade_ia') or '—'}/10")
        st.write(f"**Nível de Maturidade:** `{row.get('nivel_maturidade_ia') or '—'}`")


def render_tab_recomendacoes(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("Nenhuma recomendação gerada ainda.")
        return

    # Métricas de topo
    explicacoes = df["explicacao"].dropna().apply(safe_json)
    todas_techs = [t["tecnologia"] for exp in explicacoes for t in exp.get("tecnologias", [])]
    tech_top = pd.Series(todas_techs).value_counts().idxmax() if todas_techs else "—"

    c1, c2 = st.columns(2)
    c1.metric("Empresas com Recomendação", len(df))
    c2.metric("Tecnologia Mais Recomendada", tech_top)

    st.divider()

    # Seletor de empresa
    opcoes = df["nome_display"].fillna(df["empresa_id"].astype(str)).tolist()
    empresa_sel = st.selectbox("Selecionar empresa", opcoes)
    row = df[df["nome_display"] == empresa_sel].iloc[0]

    sintese    = safe_json(row.get("sintese_executiva"))
    explicacao = safe_json(row.get("explicacao"))
    roadmap    = safe_json(row.get("roadmap"))
    kit_raw    = safe_json(row.get("kit_inicio"))
    kit        = kit_raw.get("kit", []) if isinstance(kit_raw, dict) else []

    st.caption(
        f"Gerado em {pd.to_datetime(row.get('gerado_em')).strftime('%d/%m/%Y %H:%M')}"
        if row.get("gerado_em") else ""
    )

    # ── Síntese Executiva (LLM 2) ─────────────────────────────────────────────
    st.subheader("Síntese Executiva")
    if sintese.get("resumo"):
        st.info(sintese["resumo"])

    s1, s2 = st.columns(2)
    s1.write(f"**Impacto Principal:** {sintese.get('impacto_principal') or '—'}")
    s1.write(f"**Diferencial Competitivo:** {sintese.get('diferencial_competitivo') or '—'}")
    s2.write(f"**Investimento Estimado:** {sintese.get('investimento_estimado') or '—'}")
    s2.write(f"**Próximo Passo:** {sintese.get('proximo_passo') or '—'}")

    st.divider()

    # ── Tecnologias Recomendadas (LLM 1) ─────────────────────────────────────
    with st.expander("Tecnologias Recomendadas", expanded=True):
        tecnologias = explicacao.get("tecnologias", [])
        if tecnologias:
            for tech in tecnologias:
                st.markdown(f"**{tech.get('tecnologia', '—')}**")
                st.write(tech.get("justificativa", ""))
                st.divider()
        else:
            st.write("Sem dados.")

        fontes = explicacao.get("fontes", [])
        if fontes:
            st.caption("Fontes: " + " · ".join(fontes))

    # ── Roadmap 30/60/90 dias (LLM 3) ────────────────────────────────────────
    with st.expander("Roadmap de Adoção"):
        st.write(f"**Tecnologia Prioritária:** {roadmap.get('tecnologia_prioritaria') or '—'}")
        if roadmap.get("justificativa_prioridade"):
            st.write(roadmap["justificativa_prioridade"])

        plano = roadmap.get("plano", {})
        r1, r2, r3 = st.columns(3)
        r1.markdown("**30 dias**\n" + "\n".join(f"- {a}" for a in plano.get("30_dias", [])) or "—")
        r2.markdown("**60 dias**\n" + "\n".join(f"- {a}" for a in plano.get("60_dias", [])) or "—")
        r3.markdown("**90 dias**\n" + "\n".join(f"- {a}" for a in plano.get("90_dias", [])) or "—")

        deps = roadmap.get("dependencias", [])
        if deps:
            st.write("**Dependências:** " + ", ".join(deps))
        if roadmap.get("metrica_de_sucesso"):
            st.success(f"Métrica de Sucesso: {roadmap['metrica_de_sucesso']}")

    # ── Kit de Início (LLM 4) ─────────────────────────────────────────────────
    with st.expander("Kit de Início"):
        if kit:
            for item in kit:
                st.markdown(f"#### {item.get('tecnologia', '—')}")
                k1, k2 = st.columns(2)
                k1.write(f"**Tempo para 1º resultado:** {item.get('tempo_primeiro_resultado') or '—'}")
                k1.write(f"**Créditos Inception:** {item.get('creditos_inception') or '—'}")
                k2.write(f"**Tutorial:** {item.get('tutorial_entrada') or '—'}")
                if item.get("container_ngc"):
                    st.code(item["container_ngc"], language="bash")
                st.divider()
        else:
            st.write("Sem dados.")

    # ── Debug de Retrieval ────────────────────────────────────────────────────
    with st.expander("Detalhes Técnicos (Retrieval)"):
        st.caption(f"Query semântica: `{row.get('query') or '—'}`")
        if row.get("versao_base_conhecimento"):
            st.caption(f"Base de conhecimento: `{row['versao_base_conhecimento']}`")
        chunks = safe_json(row.get("chunks_reranqueados"))
        if isinstance(chunks, list) and chunks:
            st.dataframe(pd.DataFrame(chunks), use_container_width=True, hide_index=True)
        else:
            st.write("Sem chunks registrados.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
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
