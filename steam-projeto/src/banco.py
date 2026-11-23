"""
Conexão com o PostgreSQL + pgvector (banco vetorial do agente).

O endereço do banco vem da variável DATABASE_URL no .env. Se ela não existir,
usa o padrão do docker-compose.yml do projeto:
    postgresql://steam:steam@localhost:5432/steam

Para subir o banco (precisa do Docker Desktop instalado):
    docker compose up -d
"""
import os

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector

load_dotenv()
URL = os.getenv("DATABASE_URL", "postgresql://steam:steam@localhost:5432/steam")


def conectar():
    """Abre a conexão e ensina o psycopg a converter o tipo `vector` <-> lista/array do numpy."""
    con = psycopg.connect(URL, autocommit=True)
    con.execute("CREATE EXTENSION IF NOT EXISTS vector")   # liga o pgvector neste banco
    register_vector(con)
    return con
