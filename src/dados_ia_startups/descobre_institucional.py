from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

_RAIZ = Path(__file__).resolve().parent.parent.parent
load_dotenv(_RAIZ / ".env")

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Paths tentados em ordem de prioridade — para na primeira evidência forte
_PATHS = [
    "/",
    "/produto", "/product", "/platform", "/plataforma", "/solucao", "/solution",
    "/sobre", "/about", "/about-us", "/quem-somos",
    "/tecnologia", "/technology", "/tech", "/como-funciona", "/how-it-works",
    "/cases", "/clientes", "/customers", "/recursos", "/features",
    "/blog",
    # Paths adicionais para sites que escondem conteúdo em páginas internas
    "/empresa", "/nossa-empresa", "/our-company",
    "/servicos", "/services", "/solucoes", "/solutions",
    "/produtos", "/products",
    "/inteligencia-artificial", "/ia", "/ai",
    "/inovacao", "/innovation",
    "/logistica", "/logistic",  # para Loggi
    "/saude", "/health", "/medical",  # para NeuralMed
]

# Sinais fortes: tecnologia específica — peso alto
_SINAIS_FORTES = [
    # Frameworks e bibliotecas
    "tensorflow", "pytorch", "keras", "scikit-learn", "xgboost", "lightgbm",
    "hugging face", "transformers", "langchain", "llamaindex", "openai",
    "anthropic", "gpt", "claude", "gemini", "llama", "mistral",
    # Infraestrutura de ML
    "vertex ai", "sagemaker", "azure ml", "azure machine learning",
    "databricks", "mlflow", "kubeflow", "airflow", "prefect", "metaflow",
    "weights & biases", "wandb", "dvc", "bentoml", "seldon", "triton",
    # Conceitos técnicos de ML
    "embeddings", "fine-tuning", "finetuning", "feature store", "rag",
    "retrieval augmented", "vector database", "banco vetorial",
    "modelo treinado", "trained model", "treinamento do modelo",
    "rede neural", "neural network", "transformer", "attention mechanism",
    "gradient descent", "backpropagation", "overfitting", "underfitting",
    "hiperparâmetro", "hyperparameter", "epoch", "batch size",
    "inferência", "inference", "serving de modelo", "model serving",
    "mlops", "llmops", "reinforcement learning", "aprendizado por reforço",
    "generative ai", "ia generativa", "genai", "foundation model",
    "large language model", "llm", "slm", "multimodal",
    # Dados e engenharia
    "data lake", "data lakehouse", "data warehouse", "data mesh",
    "feature engineering", "engenharia de features",
    "etl", "elt", "dbt", "spark", "flink", "kafka", "dask",
    "pipeline de machine learning", "ml pipeline",
    "data catalog", "catálogo de dados", "data lineage",
    "data quality", "qualidade de dados", "observabilidade de dados",
    # Casos de uso técnicos
    "processamento de linguagem natural", "natural language processing",
    "visão computacional", "computer vision", "reconhecimento de imagem",
    "image recognition", "object detection", "detecção de objetos",
    "speech recognition", "reconhecimento de voz", "text to speech",
    "sentiment analysis", "análise de sentimento",
    "fraud detection", "detecção de fraude", "anomaly detection",
    "detecção de anomalia", "recommendation engine", "motor de recomendação",
    "sistemas de recomendação", "churn prediction", "previsão de churn",
    "demand forecasting", "previsão de demanda", "credit scoring",
    "precificação dinâmica", "dynamic pricing",
]

# Sinais fracos: termos genéricos — podem ser marketing
_SINAIS_FRACOS = [
    # Termos amplos PT
    "inteligência artificial", "machine learning", "aprendizado de máquina",
    "deep learning", "ciência de dados", "mineração de dados",
    "automação inteligente", "hiperautomação", "hyperautomation",
    "processamento inteligente", "decisão baseada em dados",
    "data driven", "orientado a dados", "cultura de dados",
    "preditivo", "prescritivo", "cognitivo",
    "scoring", "propensão", "segmentação", "clusterização",
    "previsão", "forecast", "insights automáticos",
    # Termos amplos EN
    "artificial intelligence", "data science", "data-driven",
    "predictive analytics", "prescriptive analytics",
    "business intelligence", "augmented analytics",
    "intelligent automation", "smart automation",
    # Infraestrutura genérica
    "big data", "relatório automatizado", "automated report",
    "api de dados", "data api",
    # Abreviações
    " ia ", " ai ", " ml ", " nlp ", " cv ",
    "rpa", "bpm",
]


# Blocklist: se o termo aparecer junto com qualquer uma dessas frases → descarta
_BLOCKLIST: dict[str, list[str]] = {
    "analytics":      ["google analytics", "meta pixel", "cookie", "preferências de cookie",
                       "pixel de rastreamento", "gtag", "facebook pixel"],
    "modelos":        ["modelos de negócio", "modelo comercial", "novos modelos de",
                       "novos modelos.", "novos modelos,", "novos modelos ",
                       "modelo de gestão", "modelos de atendimento", "modelo de franquia"],
    "treinamento":    ["treinamento de equipe", "treinamento de clientes", "academy",
                       "treinamento para", "curso", "capacitação", "onboarding"],
    "pipeline":       ["pipeline de vendas", "pipeline comercial", "pipeline de leads",
                       "funil de vendas"],
    "personalização": ["personalização de cookies", "personalização de comunicação",
                       "personalização de e-mail", "preferências de personalização"],
    "otimização":     ["otimização de campanhas", "otimização de anúncios",
                       "otimização de seo", "otimização de conversão"],
    "previsão":       ["previsão do tempo", "previsão climática"],
    "recomendação":   ["carta de recomendação", "recomendação de uso"],
    # Headline é VC — ter empresa de IA no portfólio não é usar IA
    "mistral":        ["mistral ai", "portfólio", "portfolio", "invested", "investimento"],
    " ai ":           ["portfólio", "portfolio", "invested", "investimento",
                       "mistral ai", "openai", "anthropic"],
    # Kavak — cores e filiais de carros
    "silver":         ["vermelho", "azul", "preto", "branco", "filiais", "arena"],
}

# Pontuação mínima para marcar encontrado=true
_PESO_FORTE = 3
_PESO_FRACO = 1
_THRESHOLD = 4


def _termo_bloqueado(termo: str, trecho: str) -> bool:
    frases_proibidas = _BLOCKLIST.get(termo, [])
    trecho_lower = trecho.lower()
    return any(f in trecho_lower for f in frases_proibidas)


def _extrair_texto(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ").split())


def _trecho(texto: str, termo: str, janela: int = 200) -> str:
    idx = texto.lower().find(termo.lower())
    if idx == -1:
        return ""
    inicio = max(0, idx - janela // 2)
    fim = min(len(texto), idx + len(termo) + janela // 2)
    return "..." + texto[inicio:fim].strip() + "..."


def _buscar_pagina(url: str, debug: bool = False, tentativas: int = 3) -> str | None:
    for tentativa in range(1, tentativas + 1):
        try:
            r = _SESSION.get(url, timeout=12, allow_redirects=True)
            if r.status_code == 200 and "text/html" in r.headers.get("Content-Type", ""):
                r.encoding = r.apparent_encoding
                return r.text
            if debug:
                print(f"      [debug] {url} → status={r.status_code} (tentativa {tentativa})")
            return None
        except requests.RequestException as e:
            if debug:
                print(f"      [debug] {url} → erro (tentativa {tentativa}): {e}")
            if tentativa < tentativas:
                time.sleep(2 * tentativa)

    # Fallback: tenta http:// se https:// falhou
    if url.startswith("https://"):
        url_http = url.replace("https://", "http://", 1)
        if debug:
            print(f"      [debug] fallback http: {url_http}")
        try:
            r = _SESSION.get(url_http, timeout=12, allow_redirects=True)
            if r.status_code == 200 and "text/html" in r.headers.get("Content-Type", ""):
                r.encoding = r.apparent_encoding
                return r.text
        except requests.RequestException:
            pass

    return None


def _pontuar_pagina(texto: str, debug: bool = False) -> tuple[int, str, str, str]:
    """
    Percorre todos os sinais da página acumulando pontuação.
    Retorna (pontuação_total, melhor_termo, melhor_trecho, tipo_sinal).
    O melhor termo é o de maior peso não bloqueado encontrado.
    """
    pontuacao = 0
    melhor_termo = ""
    melhor_trecho = ""
    melhor_tipo = ""
    texto_lower = texto.lower()

    for termo in _SINAIS_FORTES:
        if termo in texto_lower:
            trecho = _trecho(texto, termo)
            if _termo_bloqueado(termo, trecho):
                if debug:
                    print(f"        [blocklist] '{termo}' bloqueado")
                continue
            pontuacao += _PESO_FORTE
            if not melhor_termo:
                melhor_termo, melhor_trecho, melhor_tipo = termo, trecho, "forte"
            if debug:
                print(f"        [+{_PESO_FORTE}] forte: '{termo}'  total={pontuacao}")

    for termo in _SINAIS_FRACOS:
        if termo in texto_lower:
            trecho = _trecho(texto, termo)
            if _termo_bloqueado(termo, trecho):
                if debug:
                    print(f"        [blocklist] '{termo}' bloqueado")
                continue
            pontuacao += _PESO_FRACO
            if not melhor_termo:
                melhor_termo, melhor_trecho, melhor_tipo = termo, trecho, "fraco"
            if debug:
                print(f"        [+{_PESO_FRACO}] fraco: '{termo}'  total={pontuacao}")

    return pontuacao, melhor_termo, melhor_trecho, melhor_tipo


def _analisar(dominio: str, debug: bool = False) -> dict | None:
    """
    Acumula pontuação em todas as páginas. Retorna resultado se threshold atingido.
    """
    pontuacao_total = 0
    melhor: tuple[str, str, str, str] = ("", "", "", "")  # url, termo, trecho, tipo

    for path in _PATHS:
        url = f"https://{dominio}{path}"
        html = _buscar_pagina(url, debug=debug)
        if not html:
            time.sleep(0.5)
            continue

        texto = _extrair_texto(html)
        pontos, termo, trecho, tipo = _pontuar_pagina(texto, debug=debug)

        if debug and pontos > 0:
            print(f"      [debug] {url} → +{pontos} ponto(s)")

        pontuacao_total += pontos
        if termo and not melhor[1]:
            melhor = (url, termo, trecho, tipo)

        # Se já passou do threshold, não precisa continuar raspando
        if pontuacao_total >= _THRESHOLD:
            break

        time.sleep(1)

    if pontuacao_total >= _THRESHOLD and melhor[1]:
        if debug:
            print(f"      [debug] pontuação final={pontuacao_total} ≥ {_THRESHOLD} → POSITIVO")
        return {
            "fonte_url": melhor[0],
            "termo": melhor[1],
            "evidencia": melhor[2],
            "tipo_sinal": melhor[3],
            "pontuacao": pontuacao_total,
        }

    if debug:
        print(f"      [debug] pontuação final={pontuacao_total} < {_THRESHOLD} → negativo")
    return None


_SAIDA = _RAIZ / "data" / "institucional"


def pesquisar(debug: bool = False) -> None:
    rows = (
        supabase.table("empresas")
        .select("id, nome, dominio")
        .not_.is_("dominio", "null")
        .execute()
        .data
    )
    empresas = [r for r in rows if r.get("dominio")]
    print(f"[info] {len(empresas)} empresa(s) com dominio no Supabase\n")

    todos_registros: list[dict] = []

    for empresa in empresas:
        empresa_id = empresa["id"]
        nome = empresa["nome"]
        dominio = empresa["dominio"]

        print(f"[→] {nome}  ({dominio})")

        resultado = _analisar(dominio, debug=debug)

        if resultado:
            supabase.table("sinais_ia").insert({
                "empresa_id": empresa_id,
                "camada": "institucional",
                "encontrado": True,
                "evidencia": resultado["evidencia"],
                "fonte_url": resultado["fonte_url"],
            }).execute()
            print(f"    [✓] sinal {resultado['tipo_sinal']}: '{resultado['termo']}' (pontuação={resultado['pontuacao']}) em {resultado['fonte_url']}")
            todos_registros.append({
                "empresa_id": empresa_id,
                "nome_empresa": nome,
                "dominio": dominio,
                "encontrado": True,
                **resultado,
                "coletado_em": datetime.now(timezone.utc).isoformat(),
            })
        else:
            supabase.table("sinais_ia").insert({
                "empresa_id": empresa_id,
                "camada": "institucional",
                "encontrado": False,
                "evidencia": None,
                "fonte_url": f"https://{dominio}",
            }).execute()
            print(f"    [✗] nenhum sinal encontrado")
            todos_registros.append({
                "empresa_id": empresa_id,
                "nome_empresa": nome,
                "dominio": dominio,
                "encontrado": False,
                "fonte_url": f"https://{dominio}",
                "termo": None,
                "evidencia": None,
                "tipo_sinal": None,
                "coletado_em": datetime.now(timezone.utc).isoformat(),
            })

        time.sleep(1)

    _SAIDA.mkdir(parents=True, exist_ok=True)
    caminho = _SAIDA / "institucional.json"
    existentes: list[dict] = []
    if caminho.exists():
        existentes = json.loads(caminho.read_text(encoding="utf-8"))
    ids_existentes = {r["empresa_id"] for r in existentes}
    novos = [r for r in todos_registros if r["empresa_id"] not in ids_existentes]
    caminho.write_text(
        json.dumps(existentes + novos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[json] {len(novos)} registro(s) salvo(s) em {caminho}")

    positivos = sum(1 for r in todos_registros if r["encontrado"])
    print(f"[resumo] {positivos}/{len(empresas)} empresa(s) com sinal institucional de IA")


if __name__ == "__main__":
    import sys
    debug = "--debug" in sys.argv
    pesquisar(debug=debug)
