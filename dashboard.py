from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from supabase import create_client


# ── Conexão ────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


# ── Fetches ────────────────────────────────────────────────────────────────────

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

    nomes = get_supabase().table("empresas").select("id, nome").execute().data
    df_nomes = pd.DataFrame(nomes).rename(columns={"id": "empresa_id", "nome": "nome_original"})
    df = df.merge(df_nomes, on="empresa_id", how="left")
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

    cols_uso = [
        "empresa_id", "nome_display",
        # identidade
        "cnpj", "razao_social", "nome_fantasia", "situacao_rf",
        "dominio", "gupy_subdominio", "municipio", "uf",
        "cnae_principal", "porte", "capital_social", "natureza_juridica",
        "ano_fundacao",
        # produto e mercado
        "produto", "modelo_negocio", "mercado_alvo", "setor",
        "programa_aceleracao",
        # ia
        "uso_ia_descricao", "ia_e_core_product", "ia_tipo",
        "produto_ia_lancado", "score_maturidade_ia", "nivel_maturidade_ia",
        "situacao_coleta",
    ]
    df_uso_all = fetch_empresas_uso_ia()
    cols_existentes = [c for c in cols_uso if c in df_uso_all.columns]
    df = df.merge(df_uso_all[cols_existentes], on="empresa_id", how="left")
    return df


@st.cache_data(ttl=120)
def fetch_pendentes() -> pd.DataFrame:
    df = fetch_empresas_uso_ia()
    if df.empty:
        return df
    return df[df["situacao_coleta"] == "informação pendente"].reset_index(drop=True)


@st.cache_data(ttl=120)
def fetch_excluidas() -> pd.DataFrame:
    aval = get_supabase().table("avaliacoes_ia").select("*").eq("veredito", False).execute().data
    df_aval = pd.DataFrame(aval)
    if df_aval.empty:
        return df_aval

    empresas = get_supabase().table("empresas").select("*").execute().data
    df_emp = pd.DataFrame(empresas).rename(columns={"id": "empresa_id"})

    sinais = get_supabase().table("sinais_ia").select("empresa_id, camada, encontrado").execute().data
    df_sin = pd.DataFrame(sinais)
    if not df_sin.empty:
        resumo = df_sin.groupby("empresa_id").agg(
            sinais_encontrados=("encontrado", "sum"),
            sinais_total=("encontrado", "count"),
        ).reset_index()
    else:
        resumo = pd.DataFrame(columns=["empresa_id", "sinais_encontrados", "sinais_total"])

    df = df_aval.merge(df_emp[["empresa_id", "nome", "dominio"]], on="empresa_id", how="left")
    df = df.merge(resumo, on="empresa_id", how="left")
    df = df.sort_values(["pontuacao", "sinais_encontrados"], ascending=[True, True])
    return df.reset_index(drop=True)


# ── Helper JSONB ───────────────────────────────────────────────────────────────

def safe_json(val) -> dict | list:
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return {}
    return {}


# ── Renders ────────────────────────────────────────────────────────────────────

def render_resumo_geral() -> None:
    st.title("Resumo Geral")
    st.info("construir depois")


def _sec(label: str) -> None:
    st.markdown(
        f'<p style="margin:1.5rem 0 0.3rem;font-size:1.3rem;font-weight:700;'
        f'color:#111184;text-transform:uppercase;letter-spacing:0.08em;">{label}</p>',
        unsafe_allow_html=True,
    )

def _subsec(label: str) -> None:
    st.markdown(
        f'<p style="margin:1rem 0 0.25rem;font-size:0.75rem;font-weight:600;'
        f'color:#aaa;text-transform:uppercase;letter-spacing:0.08em;">{label}</p>',
        unsafe_allow_html=True,
    )


def render_empresas(df: pd.DataFrame, busca: str) -> None:
    st.title("Empresas")

    if df.empty:
        st.warning("Nenhuma recomendação gerada ainda.")
        return

    if busca:
        df = df[df["nome_display"].str.contains(busca, case=False, na=False)]

    # Métricas
    explicacoes = df["explicacao"].dropna().apply(safe_json)
    todas_techs = [t["tecnologia"] for exp in explicacoes for t in exp.get("tecnologias", [])]
    tech_top = pd.Series(todas_techs).value_counts().idxmax() if todas_techs else "—"

    c1, c2, c3 = st.columns(3)
    c1.metric("Com Recomendação", len(df))
    c2.metric("Tecnologia Mais Recomendada", tech_top)
    c3.metric("Setores Distintos", df["setor"].nunique())

    st.divider()

    if df.empty:
        st.info(f"Nenhum resultado para '{busca}'.")
        return

    st.markdown(
        '<p style="font-size:1rem;font-weight:700;color:#fff;margin-bottom:0.2rem;">'
        'Selecionar empresa</p>',
        unsafe_allow_html=True,
    )
    opcoes = df["nome_display"].fillna(df["empresa_id"].astype(str)).tolist()
    empresa_sel = st.selectbox("Selecionar empresa", opcoes, label_visibility="collapsed")
    row = df[df["nome_display"] == empresa_sel].iloc[0]

    sintese    = safe_json(row.get("sintese_executiva"))
    explicacao = safe_json(row.get("explicacao"))
    roadmap    = safe_json(row.get("roadmap"))
    kit_raw    = safe_json(row.get("kit_inicio"))
    kit        = kit_raw.get("kit", []) if isinstance(kit_raw, dict) else []

    if row.get("gerado_em"):
        st.caption(f"Recomendação gerada em {pd.to_datetime(row['gerado_em']).strftime('%d/%m/%Y %H:%M')}")

    # ── Perfil da Empresa ────────────────────────────────────────────────────
    _sec("Perfil da Empresa")
    _subsec("Identidade")
    i1, i2, i3 = st.columns(3)
    i1.write(f"**CNPJ:** {row.get('cnpj') or '—'}")
    i1.write(f"**Razão Social:** {row.get('razao_social') or '—'}")
    i1.write(f"**Situação RF:** {row.get('situacao_rf') or '—'}")
    i2.write(f"**Município/UF:** {row.get('municipio') or '—'}/{row.get('uf') or '—'}")
    i2.write(f"**CNAE:** {row.get('cnae_principal') or '—'}")
    i2.write(f"**Porte:** {row.get('porte') or '—'}")
    cap = row.get("capital_social")
    i3.write(
        f"**Capital Social:** R$ {cap:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if cap else "**Capital Social:** —"
    )
    i3.write(f"**Natureza Jurídica:** {row.get('natureza_juridica') or '—'}")
    i3.write(f"**Domínio:** {row.get('dominio') or '—'}")
    i3.write(f"**Ano de Fundação:** {row.get('ano_fundacao') or '—'}")

    st.divider()

    st.markdown("##### Produto e Mercado")
    p1, p2 = st.columns(2)
    p1.write(f"**Produto:** {row.get('produto') or '—'}")
    p1.write(f"**Modelo de Negócio:** {row.get('modelo_negocio') or '—'}")
    p1.write(f"**Mercado Alvo:** {row.get('mercado_alvo') or '—'}")
    p2.write(f"**Setor:** {row.get('setor') or '—'}")
    p2.write(f"**Gupy:** {row.get('gupy_subdominio') or '—'}")
    p2.write(f"**Programas de Aceleração:** {row.get('programa_aceleracao') or '—'}")

    st.divider()

    st.markdown("##### Uso de Inteligência Artificial")
    st.write(f"**Descrição:** {row.get('uso_ia_descricao') or '—'}")
    a1, a2, a3, a4 = st.columns(4)
    a1.write(f"**Tipo de IA:** {row.get('ia_tipo') or '—'}")
    a2.write(f"**IA é core product?** {'Sim' if row.get('ia_e_core_product') else 'Não'}")
    a3.write(f"**Produto em produção?** {'Sim' if row.get('produto_ia_lancado') else 'Não'}")
    a4.write(f"**Score:** {row.get('score_maturidade_ia') or '—'}/10")
    st.write(f"**Maturidade:** `{row.get('nivel_maturidade_ia') or '—'}`")

    st.divider()

    # ── Síntese Executiva ────────────────────────────────────────────────────
    _sec("Síntese Executiva")
    if sintese.get("resumo"):
        st.info(sintese["resumo"])
    s1, s2 = st.columns(2)
    s1.write(f"**Impacto Principal:** {sintese.get('impacto_principal') or '—'}")
    s1.write(f"**Diferencial Competitivo:** {sintese.get('diferencial_competitivo') or '—'}")
    s2.write(f"**Investimento Estimado:** {sintese.get('investimento_estimado') or '—'}")
    s2.write(f"**Próximo Passo:** {sintese.get('proximo_passo') or '—'}")

    st.divider()

    # ── Tecnologias Recomendadas ─────────────────────────────────────────────
    _sec("Tecnologias Recomendadas")
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
        st.write("**Fontes:** " + " · ".join(fontes))

    st.divider()

    # ── Roadmap de Adoção ────────────────────────────────────────────────────
    _sec("Roadmap de Adoção")
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

    st.divider()

    # ── Kit de Início ────────────────────────────────────────────────────────
    _sec("Kit de Início")
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

    st.divider()

    # ── Detalhes Técnicos ────────────────────────────────────────────────────
    _sec("Detalhes Técnicos (Retrieval)")
    st.write(f"**Query semântica:** {row.get('query') or '—'}")
    if row.get("versao_base_conhecimento"):
        st.write(f"**Base de conhecimento:** {row['versao_base_conhecimento']}")
    chunks = safe_json(row.get("chunks_reranqueados"))
    if isinstance(chunks, list) and chunks:
        st.dataframe(pd.DataFrame(chunks), use_container_width=True, hide_index=True)
    else:
        st.write("Sem chunks registrados.")


def render_pendentes(df: pd.DataFrame, busca: str) -> None:
    st.title("Pendentes")
    st.warning(
        "⚠️ **Atenção — revisão manual necessária**\n\n"
        "Empresas pendentes são aquelas em que o pipeline identificou sinais de uso de inteligência artificial, "
        "mas que ficaram com alguma informação incompleta ou ausente necessária para gerar as recomendações de "
        "tecnologias NVIDIA. Por isso, precisam de revisão manual antes de poderem seguir para a próxima etapa."
    )

    if df.empty:
        st.success("Nenhuma empresa com pendência.")
        return

    if busca:
        df = df[df["nome_display"].str.contains(busca, case=False, na=False)]

    st.caption(f"{len(df)} empresa(s) com situação 'informação pendente'")

    # Colunas omitidas: empresa_id, nome_fantasia, cnpj_pendente, nome_original
    OMITIR = {"empresa_id", "nome_fantasia", "cnpj_pendente", "nome_original"}
    cols_exibir = [c for c in df.columns if c not in OMITIR]

    st.dataframe(
        df[cols_exibir],
        use_container_width=True,
        column_config={
            "nome_display":        st.column_config.TextColumn("Empresa"),
            "cnpj":                st.column_config.TextColumn("CNPJ"),
            "dominio":             st.column_config.LinkColumn("Site", display_text=r"https?://(.+)"),
            "gupy_subdominio":     st.column_config.TextColumn("Gupy"),
            "razao_social":        st.column_config.TextColumn("Razão Social"),
            "situacao_rf":         st.column_config.TextColumn("Situação RF"),
            "municipio":           st.column_config.TextColumn("Município"),
            "uf":                  st.column_config.TextColumn("UF", width="small"),
            "cnae_principal":      st.column_config.TextColumn("CNAE"),
            "porte":               st.column_config.TextColumn("Porte"),
            "capital_social":      st.column_config.NumberColumn("Capital Social", format="R$ %.2f"),
            "natureza_juridica":   st.column_config.TextColumn("Natureza Jurídica"),
            "produto":             st.column_config.TextColumn("Produto"),
            "modelo_negocio":      st.column_config.TextColumn("Modelo de Negócio"),
            "mercado_alvo":        st.column_config.TextColumn("Mercado Alvo"),
            "setor":               st.column_config.TextColumn("Setor"),
            "uso_ia_descricao":    st.column_config.TextColumn("Uso de IA"),
            "ia_e_core_product":   st.column_config.CheckboxColumn("IA é Core?"),
            "ia_tipo":             st.column_config.TextColumn("Tipo de IA"),
            "ano_fundacao":        st.column_config.NumberColumn("Fundação"),
            "produto_ia_lancado":  st.column_config.CheckboxColumn("Produto IA em Prod."),
            "programa_aceleracao": st.column_config.TextColumn("Aceleração"),
            "score_maturidade_ia": st.column_config.ProgressColumn(
                "Score IA", min_value=0, max_value=10, format="%d"
            ),
            "nivel_maturidade_ia": st.column_config.TextColumn("Maturidade"),
            "situacao_coleta":     st.column_config.TextColumn("Situação"),
            "enriquecido_em":      st.column_config.DatetimeColumn("Enriquecido em", format="DD/MM/YYYY"),
        },
        hide_index=True,
    )

    st.info(
        "**Nota:** a maioria das empresas pendentes apresenta os campos **Programa de Aceleração** e "
        "**Gupy** em branco. Esses campos são complementares e não determinam se uma empresa é "
        "marcada como pendente — a situação é definida por campos obrigatórios como CNPJ, produto, "
        "setor e tipo de IA."
    )


def render_excluidas(df: pd.DataFrame, busca: str) -> None:
    st.title("Excluídas")
    st.caption(
        "As empresas abaixo foram coletadas pelo pipeline mas não atingiram pontuação "
        "suficiente nos alertas de uso de IA e, por isso, foram excluídas do processo de recomendação."
    )

    if df.empty:
        st.info("Nenhuma empresa excluída registrada.")
        return

    if busca:
        df = df[df["nome"].str.contains(busca, case=False, na=False)]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Excluídas", len(df))
    c2.metric("Pontuação Média", f"{df['pontuacao'].mean():.1f}" if "pontuacao" in df.columns else "—")
    c3.metric("Média de Sinais Encontrados",
              f"{df['sinais_encontrados'].mean():.1f}" if "sinais_encontrados" in df.columns else "—")

    st.divider()

    cols = ["nome", "dominio", "pontuacao", "sinais_encontrados", "sinais_total", "avaliado_em"]
    cols_existentes = [c for c in cols if c in df.columns]

    st.dataframe(
        df[cols_existentes],
        use_container_width=True,
        column_config={
            "nome":               st.column_config.TextColumn("Empresa"),
            "dominio":            st.column_config.LinkColumn("Site", display_text=r"https?://(.+)"),
            "pontuacao":          st.column_config.ProgressColumn(
                "Pontuação", min_value=0, max_value=10, format="%.1f"
            ),
            "sinais_encontrados": st.column_config.NumberColumn("Sinais ✓"),
            "sinais_total":       st.column_config.NumberColumn("Sinais Total"),
            "avaliado_em":        st.column_config.DatetimeColumn("Avaliado em", format="DD/MM/YYYY"),
        },
        hide_index=True,
    )

    st.divider()

    nomes = df["nome"].dropna().tolist()
    if not nomes:
        return

    empresa_sel = st.selectbox("Ver detalhes de:", ["—"] + nomes, key="sel_excluidas")
    if empresa_sel == "—":
        return

    row = df[df["nome"] == empresa_sel].iloc[0]

    with st.expander(f"Detalhes — {empresa_sel}", expanded=True):
        d1, d2, d3 = st.columns(3)
        d1.write(f"**Site:** {row.get('dominio') or '—'}")
        d2.write(f"**Pontuação:** {row.get('pontuacao') or '—'}")
        d3.write(f"**Avaliado em:** {pd.to_datetime(row['avaliado_em']).strftime('%d/%m/%Y') if row.get('avaliado_em') else '—'}")

        st.markdown("##### Sinais de IA verificados")
        s1, s2 = st.columns(2)
        s1.metric("Sinais encontrados", int(row.get("sinais_encontrados") or 0))
        s2.metric("Total verificado", int(row.get("sinais_total") or 0))

        sinais_ativos = safe_json(row.get("sinais_ativos"))
        if sinais_ativos:
            st.markdown("**Camadas avaliadas:**")
            if isinstance(sinais_ativos, dict):
                for camada, encontrado in sinais_ativos.items():
                    icone = "✅" if encontrado else "❌"
                    st.write(f"{icone} {camada}")
            elif isinstance(sinais_ativos, list):
                for item in sinais_ativos:
                    st.write(f"• {item}")


def render_uso_ia(df: pd.DataFrame, busca: str, titulo: str = "Uso de IA") -> None:
    st.title(titulo)

    if df.empty:
        st.warning("Nenhuma empresa aprovada ainda.")
        return

    if busca:
        df = df[df["nome_display"].str.contains(busca, case=False, na=False)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aprovadas", len(df))
    c2.metric("AI-Native", int((df["nivel_maturidade_ia"] == "ai-native").sum()))
    score_medio = df["score_maturidade_ia"].dropna()
    c3.metric("Score Médio", f"{score_medio.mean():.1f}/10" if not score_medio.empty else "—")
    c4.metric("Produto em Produção", int(df["produto_ia_lancado"].sum()))

    st.divider()

    f1, f2, f3, f4 = st.columns(4)
    setores    = f1.multiselect("Setor", sorted(df["setor"].dropna().unique()))
    tipos_ia   = f2.multiselect("Tipo de IA", sorted(df["ia_tipo"].dropna().unique()))
    maturidade = f3.multiselect("Maturidade", ["ai-native", "ai-first", "ai-enabled", "ai-adjacent"])
    situacoes  = df["situacao_coleta"].dropna().unique().tolist()
    situacao   = f4.selectbox("Situação", ["Todas"] + situacoes)

    mask = pd.Series([True] * len(df), index=df.index)
    if setores:    mask &= df["setor"].isin(setores)
    if tipos_ia:   mask &= df["ia_tipo"].isin(tipos_ia)
    if maturidade: mask &= df["nivel_maturidade_ia"].isin(maturidade)
    if situacao != "Todas": mask &= df["situacao_coleta"] == situacao
    df_filtrado = df[mask]

    st.caption(f"{len(df_filtrado)} empresa(s) exibida(s)")

    cols_exibir = ["nome_display", "setor", "ia_tipo",
                   "nivel_maturidade_ia", "score_maturidade_ia", "situacao_coleta"]
    st.dataframe(
        df_filtrado[cols_exibir],
        use_container_width=True,
        column_config={
            "nome_display":        st.column_config.TextColumn("Empresa"),
            "setor":               st.column_config.TextColumn("Setor"),
            "ia_tipo":             st.column_config.TextColumn("Tipo de IA"),
            "nivel_maturidade_ia": st.column_config.TextColumn("Maturidade"),
            "score_maturidade_ia": st.column_config.ProgressColumn(
                "Score IA", min_value=0, max_value=10, format="%d"
            ),
            "situacao_coleta":     st.column_config.TextColumn("Situação"),
        },
        hide_index=True,
    )

    st.divider()

    nomes = df_filtrado["nome_display"].dropna().tolist()
    if not nomes:
        return

    empresa_sel = st.selectbox("Ver perfil completo de:", ["—"] + nomes)
    if empresa_sel == "—":
        return

    row = df_filtrado[df_filtrado["nome_display"] == empresa_sel].iloc[0]

    with st.expander(f"Perfil — {empresa_sel}", expanded=True):
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

        _subsec("Produto e Mercado")
        p1, p2 = st.columns(2)
        p1.write(f"**Produto:** {row.get('produto') or '—'}")
        p1.write(f"**Modelo de Negócio:** {row.get('modelo_negocio') or '—'}")
        p1.write(f"**Mercado Alvo:** {row.get('mercado_alvo') or '—'}")
        p2.write(f"**Setor:** {row.get('setor') or '—'}")
        p2.write(f"**Domínio:** {row.get('dominio') or '—'}")
        p2.write(f"**Programas de Aceleração:** {row.get('programa_aceleracao') or '—'}")

        st.divider()

        _subsec("Uso de Inteligência Artificial")
        st.write(f"**Descrição:** {row.get('uso_ia_descricao') or '—'}")
        a1, a2, a3, a4 = st.columns(4)
        a1.write(f"**Tipo de IA:** {row.get('ia_tipo') or '—'}")
        a2.write(f"**IA é core product?** {'Sim' if row.get('ia_e_core_product') else 'Não'}")
        a3.write(f"**Produto IA em produção?** {'Sim' if row.get('produto_ia_lancado') else 'Não'}")
        a4.write(f"**Score de Maturidade:** {row.get('score_maturidade_ia') or '—'}/10")
        st.write(f"**Nível de Maturidade:** `{row.get('nivel_maturidade_ia') or '—'}`")


# ── Main ───────────────────────────────────────────────────────────────────────

PAGINAS = ["Resumo Geral", "Empresas", "Pendentes", "Excluídas", "Uso de IA"]

def main() -> None:
    st.set_page_config(page_title="NVIDIA Intel Academy", layout="wide")

    # CSS: header fixo + sidebar direita
    st.markdown("""
        <style>
        /* ── Sidebar esquerda (padrão) ───────────────────────── */

        /* Esconde o handle de redimensionamento (elemento cinza arrastável) */
        [data-testid="stSidebarResizeHandle"] {
            display: none !important;
        }

        /* Garante largura fixa da sidebar */
        [data-testid="stSidebar"] {
            min-width: 18rem !important;
            max-width: 18rem !important;
        }

        /* Padding para o header fixo */
        [data-testid="stAppViewContainer"] > section.main {
            padding-top: 3.5rem;
        }

        /* ── Header fixo ─────────────────────────────────────── */
        .header-bar {
            position: fixed; top: 0; left: 0; right: 0; z-index: 999;
            background: #0f0f0f; border-bottom: 1px solid #1e1e1e;
            padding: 0.55rem 1.5rem;
            display: flex; align-items: center; justify-content: space-between;
        }
        .header-bar .logo { font-size: 1.25rem; font-weight: 700; color: #76b900; }
        .header-bar .nav  { font-size: 0.8rem; color: #888; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="header-bar">
            <span class="nav">NVIDIA · Radar de Startups</span>
            <span class="logo">🚀</span>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("## Navegação")
        pagina = st.radio("", PAGINAS, label_visibility="collapsed")
        st.divider()
        busca = st.text_input("Buscar empresa", placeholder="Filtrar por nome...")

    # Router
    if pagina == "Resumo Geral":
        render_resumo_geral()

    elif pagina == "Empresas":
        render_empresas(fetch_recomendacoes(), busca)

    elif pagina == "Pendentes":
        render_pendentes(fetch_pendentes(), busca)

    elif pagina == "Excluídas":
        render_excluidas(fetch_excluidas(), busca)

    elif pagina == "Uso de IA":
        render_uso_ia(fetch_empresas_uso_ia(), busca)


if __name__ == "__main__":
    main()
