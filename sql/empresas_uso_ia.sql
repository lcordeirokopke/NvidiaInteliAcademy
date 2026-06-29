-- Dados públicos enriquecidos das empresas aprovadas pelo filtro_ia
-- Populada apenas para empresas com veredito = TRUE em avaliacoes_ia
CREATE TABLE empresas_uso_ia (
    empresa_id           INTEGER PRIMARY KEY REFERENCES avaliacoes_ia(empresa_id),

    -- BrasilAPI
    cnpj                 CHAR(14),    -- somente dígitos, sem formatação
    cnpj_pendente        BOOLEAN DEFAULT FALSE,  -- TRUE: busca automática falhou, preencher manualmente
    dominio              TEXT,        -- domínio oficial, herdado de empresas.dominio
    gupy_subdominio      TEXT,        -- subdomínio Gupy, herdado de empresas.gupy_subdominio
    razao_social         TEXT,
    nome_fantasia        TEXT,
    situacao_rf          TEXT,        -- ATIVA, BAIXADA, INAPTA...
    municipio            TEXT,
    uf                   CHAR(2),
    cnae_principal       TEXT,        -- código + descrição da atividade principal
    porte                TEXT,        -- MEI, ME, EPP, DEMAIS
    capital_social       NUMERIC,     -- capital social registrado em BRL
    natureza_juridica    TEXT,        -- ex: 'Sociedade Empresária Limitada'

    -- Produto
    produto              TEXT,        -- descrição do produto/serviço principal (fonte: site/crunchbase)

    -- Mercado
    modelo_negocio       TEXT,        -- B2B, B2C, B2B2C
    mercado_alvo         TEXT,        -- Brasil, LATAM, global
    setor                TEXT,        -- domínio de mercado: Fintech, Healthtech, Edtech...

    -- Tecnologia
    uso_ia_descricao     TEXT,        -- como a empresa usa IA (1-2 frases)

    -- Maturidade AI-native: posicionamento
    ia_e_core_product    BOOLEAN,     -- TRUE: produto principal É a IA; FALSE: IA é feature
    ia_tipo              TEXT[],      -- {'generativa','preditiva','computer vision','NLP','automacao'}

    -- Maturidade AI-native: tempo e execução
    ano_fundacao         SMALLINT,    -- fundada após 2020 = provável AI-native por design
    produto_ia_lancado   BOOLEAN,     -- produto de IA já em produção (vs. "estamos construindo")

    -- Maturidade AI-native: validação externa
    acelerada_ia         BOOLEAN,     -- passou por NVIDIA Inception, YC, Microsoft for Startups, etc.
    programa_aceleracao  TEXT[],      -- ex: {'NVIDIA Inception', 'Y Combinator', 'Google for Startups'}

    -- Classificação final (calculada pelo programa a partir dos campos acima)
    score_maturidade_ia  SMALLINT,    -- 0 a 4
    nivel_maturidade_ia  TEXT,        -- 'ai-native' | 'ai-first' | 'ai-enabled' | 'ai-adjacent'

    -- Controle
    fonte_dados          TEXT,        -- 'crunchbase', 'site', 'neofeed', 'linkedin'
    enriquecido_em       TIMESTAMPTZ DEFAULT now()
);

-- Índice útil para filtrar por maturidade na próxima fase
CREATE INDEX idx_empresas_uso_ia_nivel ON empresas_uso_ia (nivel_maturidade_ia);
CREATE INDEX idx_empresas_uso_ia_core  ON empresas_uso_ia (ia_e_core_product);
