"""
Etapa 8 - Banco vetorial (embeddings + PostgreSQL com pgvector)

Textos usados pelo agente (dados textuais exigidos no enunciado):
  1. Notícias e patch notes oficiais dos jogos (ISteamNews/GetNewsForApp)
  2. Descrição de cada jogo na loja (Store API: short_description + about_the_game)
  3. Achados da análise do próprio grupo (docs/achados_eda.txt e achados_ml.txt),
     para o agente também responder com base nos números da base estruturada.

Passos: extrair -> limpar (HTML/BBCode) -> dividir em chunks de ~300 palavras
com sobreposição -> registrar metadados (título, fonte, link, data, tema)
-> gerar embeddings -> salvar na tabela `documentos` do PostgreSQL (extensão pgvector).

Antes de rodar, suba o banco:  docker compose up -d

Também gera docs/tabela_documentos.csv (a tabela da seção 9.1 do enunciado).
Como rodar:  python src/vetorial.py
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sentence_transformers import SentenceTransformer

from banco import conectar

RAW = Path("data/raw")
MODELO = "paraphrase-multilingual-MiniLM-L12-v2"   # entende português e inglês
HOJE = datetime.now().strftime("%d/%m/%Y")


def limpar(txt):
    txt = re.sub(r"\[/?(img|url|video|previewyoutube)[^\]]*\].*?(\[/\1\])?", " ", txt or "", flags=re.S)
    txt = txt.replace("\\[", "[").replace("\\]", "]").replace("[/*]", "")
    txt = re.sub(r"\[\*\]", "\n- ", txt)
    txt = re.sub(r"\[/?[a-z0-9]+[^\]]*\]", " ", txt)        # resto do BBCode
    txt = re.sub(r"<[^>]+>", " ", txt)                       # HTML
    txt = re.sub(r"https?://\S+|\{STEAM_CLAN_IMAGE\}\S*|\{STEAM_CLAN_LOC_IMAGE\}\S*", " ", txt)
    txt = re.sub(r"&[a-z]+;", " ", txt)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", txt)).strip()


def chunks(txt, tam=300, sobra=50):
    """Divide em pedaços de ~tam palavras, repetindo `sobra` palavras entre um e outro
    para não cortar uma ideia no meio."""
    p = txt.split()
    if len(p) <= tam:
        return [txt]
    return [" ".join(p[i:i + tam]) for i in range(0, len(p), tam - sobra)]


docs = []   # cada item: texto + metadados
base = pd.read_csv("data/processed/steam_tratada.csv")
nome_loja = dict(zip(base.appid.astype(str), base.nome))   # nome atual do jogo na loja

# 1. Notícias
with open(RAW / "noticias.jsonl", encoding="utf-8") as f:
    for l in f:
        n = json.loads(l)
        t = limpar(n["texto"])
        if len(t.split()) < 30:
            continue
        data = datetime.fromtimestamp(int(n["data"]), timezone.utc).strftime("%Y-%m-%d")
        jogo = nome_loja.get(str(n["appid"]), n["jogo"])
        docs.append({"texto": t, "titulo": f"{jogo}: {n['titulo']}", "fonte": n["fonte"],
                     "link": n["link"], "data": data, "tema": "Notícia / patch notes", "jogo": jogo})

# 2. Descrições dos jogos
validos = set(base.appid)
with open(RAW / "appdetails.jsonl", encoding="utf-8") as f:
    for l in f:
        d = json.loads(l)
        if not d["ok"] or not d["data"] or d["appid"] not in validos:
            continue
        g = d["data"]
        t = limpar((g.get("short_description") or "") + "\n" + (g.get("about_the_game") or ""))
        if len(t.split()) < 30:
            continue
        docs.append({"texto": t, "titulo": f"{g['name']}: descrição na loja", "fonte": "Steam Store",
                     "link": f"https://store.steampowered.com/app/{d['appid']}", "data": HOJE,
                     "tema": "Descrição do jogo", "jogo": g["name"]})

# 3. Achados da análise do grupo (gerados por eda.py e ml.py, uma frase por linha)
for arq, tema in [("docs/achados_eda.txt", "Análise do grupo (estatística)"), ("docs/achados_ml.txt", "Análise do grupo (Machine Learning)")]:
    if not Path(arq).exists():
        continue
    for linha in Path(arq).read_text(encoding="utf-8").splitlines():
        if " | " in linha:
            titulo, frase = linha.split(" | ", 1)
            docs.append({"texto": frase, "titulo": f"{tema}: {titulo}", "fonte": "Projeto do grupo",
                         "link": arq, "data": HOJE, "tema": tema, "jogo": ""})

# Tabela 9.1 do enunciado (um documento por linha)
pd.DataFrame([{"Documento": d["titulo"], "Fonte": d["fonte"], "Link": d["link"],
               "Data de acesso": HOJE, "Data do texto": d["data"], "Tema": d["tema"]} for d in docs]
             ).to_csv("docs/tabela_documentos.csv", index=False)

# Chunks
ids, textos, metas = [], [], []
for i, d in enumerate(docs):
    for j, c in enumerate(chunks(d["texto"])):
        ids.append(f"d{i}_c{j}")
        textos.append(c)
        metas.append({k: str(v) for k, v in d.items() if k != "texto"})
print(f"{len(docs)} documentos -> {len(textos)} chunks")

# Embeddings (o título entra junto no texto: ajuda a achar o jogo/assunto certo)
modelo = SentenceTransformer(MODELO)
embs = modelo.encode([m["titulo"] + "\n" + t for m, t in zip(metas, textos)],
                     batch_size=64, show_progress_bar=True)       # matriz 2724 x 384

# PostgreSQL + pgvector
con = conectar()
con.execute("DROP TABLE IF EXISTS documentos")     # recria do zero a cada execução
con.execute("""
    CREATE TABLE documentos (
        id        TEXT PRIMARY KEY,      -- d<documento>_c<chunk>
        titulo    TEXT,
        fonte     TEXT,
        link      TEXT,
        data      TEXT,
        tema      TEXT,
        jogo      TEXT,
        texto     TEXT,
        embedding VECTOR(384)            -- tipo novo que o pgvector adiciona ao Postgres
    )""")
with con.cursor() as cur:
    cur.executemany(
        "INSERT INTO documentos (id, titulo, fonte, link, data, tema, jogo, texto, embedding) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        [(i, m["titulo"], m["fonte"], m["link"], m["data"], m["tema"], m["jogo"], t, e)
         for i, m, t, e in zip(ids, metas, textos, embs)])

# Índices: HNSW acelera a busca por vizinhos mais próximos (distância cosseno);
# o índice comum em `jogo` acelera o filtro "só textos deste jogo".
con.execute("CREATE INDEX ON documentos USING hnsw (embedding vector_cosine_ops)")
con.execute("CREATE INDEX ON documentos (jogo)")
print("Chunks no banco vetorial:", con.execute("SELECT count(*) FROM documentos").fetchone()[0])
