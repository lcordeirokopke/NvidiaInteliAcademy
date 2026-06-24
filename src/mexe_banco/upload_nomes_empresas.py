import json
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "nomes_empresas", "nomes_empresas.json")

with open(JSON_PATH, encoding="utf-8") as f:
    dados = json.load(f)

response = (
    supabase.table("nomes_empresas")
    .upsert(dados, on_conflict="url")
    .execute()
)

print(f"Registros enviados: {len(response.data)}")
