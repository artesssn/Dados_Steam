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
from modelo_local import carregar_modelo

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

# 4. Os números da base estruturada viram texto (rankings + uma ficha por jogo).
#    Sem isso o agente não responde perguntas simples como "qual o jogo mais jogado?",
#    porque esses números só existiam na planilha, fora do banco vetorial.
def num(v, casas=0):
    """1234567.8 -> '1.234.568' (formato brasileiro)"""
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v):
    return num(100 * v, 1) + "%"


def preco(r):
    if r.gratuito:
        return "gratuito (free to play)"
    if pd.isna(r.preco_brl):
        return "sem preço na loja brasileira"
    return f"R$ {num(r.preco_brl, 2)}"


GENERO_PT = {"Action": "Ação", "Adventure": "Aventura", "Indie": "Indie", "RPG": "RPG", "Simulation": "Simulação",
             "Strategy": "Estratégia", "Free To Play": "Gratuitos (Free To Play)", "Casual": "Casual",
             "Massively Multiplayer": "MMO (multijogador massivo)", "Sports": "Esportes", "Early Access": "Acesso antecipado",
             "Racing": "Corrida"}
COLETA = "novembro de 2026"
b = base.copy()
b["generos"] = b["generos"].fillna("")
pos_jogados = b["jogadores_simultaneos"].rank(ascending=False, method="min")


def ranking(titulo, intro, df, linha, n=15):
    itens = "\n".join(f"{i}. {linha(r)}" for i, (_, r) in enumerate(df.head(n).iterrows(), 1))
    docs.append({"texto": f"{intro}\n{itens}", "titulo": f"Ranking: {titulo}", "fonte": "Base do projeto (SteamSpy + Steam Store)",
                 "link": "data/processed/steam_tratada.csv", "data": HOJE, "tema": "Ranking da base", "jogo": ""})


jog = lambda r: f"{r.nome}: {num(r.jogadores_simultaneos)} jogadores simultâneos"
ranking("jogos mais jogados", f"Os jogos mais jogados da base (jogo mais jogado, mais populares agora), pelo pico de jogadores "
        f"simultâneos medido pelo SteamSpy na coleta de {COLETA}. O mais jogado é {b.sort_values('jogadores_simultaneos', ascending=False).iloc[0].nome}.",
        b.sort_values("jogadores_simultaneos", ascending=False), jog)
ranking("jogos gratuitos mais jogados", "Os jogos gratuitos (free to play) mais jogados, por jogadores simultâneos:",
        b[b.gratuito].sort_values("jogadores_simultaneos", ascending=False), jog, 10)
ranking("jogos pagos mais jogados", "Os jogos pagos mais jogados, por jogadores simultâneos:",
        b[~b.gratuito].sort_values("jogadores_simultaneos", ascending=False), lambda r: f"{jog(r)}, {preco(r)}", 10)
ranking("jogos com mais donos (mais vendidos ou baixados)", "Os jogos com mais donos estimados pelo SteamSpy (mais vendidos, mais baixados):",
        b.sort_values(["donos_medio", "total_avaliacoes"], ascending=False), lambda r: f"{r.nome}: cerca de {num(r.donos_medio)} donos")
ranking("jogos com mais avaliações", "Os jogos com mais avaliações de usuários na Steam (os mais avaliados, mais comentados):",
        b.sort_values("total_avaliacoes", ascending=False), lambda r: f"{r.nome}: {num(r.total_avaliacoes)} avaliações, {pct(r.prop_positiva)} positivas")
bons = b[b.total_avaliacoes >= 1000]
ranking("jogos mais bem avaliados", "Os jogos mais bem avaliados (melhores jogos, maior porcentagem de avaliações positivas, "
        "entre os que têm pelo menos 1.000 avaliações):", bons.sort_values("prop_positiva", ascending=False),
        lambda r: f"{r.nome}: {pct(r.prop_positiva)} positivas ({r.classificacao}), {num(r.total_avaliacoes)} avaliações")
ranking("jogos mais mal avaliados", "Os jogos mais mal avaliados (piores jogos, menor porcentagem de avaliações positivas, "
        "entre os que têm pelo menos 1.000 avaliações):", bons.sort_values("prop_positiva"),
        lambda r: f"{r.nome}: {pct(r.prop_positiva)} positivas ({r.classificacao})", 10)
pagos = b[~b.gratuito & b.preco_brl.notna()]
ranking("jogos mais caros", "Os jogos mais caros da base na loja brasileira (preço atual):",
        pagos.sort_values("preco_brl", ascending=False), lambda r: f"{r.nome}: {preco(r)}", 10)
ranking("jogos pagos mais baratos", "Os jogos pagos mais baratos da base na loja brasileira:",
        pagos.sort_values("preco_brl"), lambda r: f"{r.nome}: {preco(r)}", 10)
ranking("maiores descontos", "Os jogos com os maiores descontos (promoções) no momento da coleta:",
        b[b.desconto_pct > 0].sort_values("desconto_pct", ascending=False),
        lambda r: f"{r.nome}: {r.desconto_pct}% de desconto, de R$ {num(r.preco_original_brl, 2)} por R$ {num(r.preco_brl, 2)}", 10)
ranking("melhores notas no Metacritic", "Os jogos com as maiores notas da crítica no Metacritic:",
        b[b.metacritic.notna()].sort_values("metacritic", ascending=False), lambda r: f"{r.nome}: nota {num(r.metacritic)}", 10)
ranking("lançamentos mais recentes", "Os jogos lançados mais recentemente (lançamentos novos) entre os da base:",
        b.assign(_d=pd.to_datetime(b.data_lancamento, errors="coerce")).sort_values("_d", ascending=False),
        lambda r: f"{r.nome}: lançado em {r.data_lancamento}", 10)
ranking("jogos mais antigos", "Os jogos mais antigos (lançados há mais tempo) da base:",
        b.assign(_d=pd.to_datetime(b.data_lancamento, errors="coerce")).sort_values("_d"),
        lambda r: f"{r.nome}: lançado em {r.data_lancamento}", 10)
ranking("jogos com mais conquistas", "Os jogos com mais conquistas (achievements):",
        b.sort_values("n_conquistas", ascending=False), lambda r: f"{r.nome}: {num(r.n_conquistas)} conquistas", 10)
ranking("jogos com mais DLCs", "Os jogos com mais DLCs (conteúdos adicionais):",
        b.sort_values("n_dlcs", ascending=False), lambda r: f"{r.nome}: {num(r.n_dlcs)} DLCs", 10)
dev = b.desenvolvedora.fillna("").str.split(",").str[0].str.strip()
cont = dev[dev != ""].value_counts().head(10)
docs.append({"texto": "As desenvolvedoras (estúdios) com mais jogos na base:\n" +
             "\n".join(f"{i}. {d}: {n} jogos" for i, (d, n) in enumerate(cont.items(), 1)),
             "titulo": "Ranking: desenvolvedoras com mais jogos", "fonte": "Base do projeto (SteamSpy + Steam Store)",
             "link": "data/processed/steam_tratada.csv", "data": HOJE, "tema": "Ranking da base", "jogo": ""})
for g, gpt in GENERO_PT.items():
    sub = b[b.generos.str.split(", ").apply(lambda l: g in l)]
    ranking(f"jogos de {gpt} mais jogados", f"Os jogos do gênero {gpt} ({g}) mais jogados e populares, "
            f"por jogadores simultâneos ({len(sub)} jogos desse gênero na base):",
            sub.sort_values("jogadores_simultaneos", ascending=False),
            lambda r: f"{r.nome}: {num(r.jogadores_simultaneos)} jogadores, {pct(r.prop_positiva)} positivas", 10)
    sb = sub[sub.total_avaliacoes >= 1000]
    ranking(f"melhores jogos de {gpt}", f"Os jogos do gênero {gpt} ({g}) mais bem avaliados (melhores, mínimo 1.000 avaliações):",
            sb.sort_values("prop_positiva", ascending=False),
            lambda r: f"{r.nome}: {pct(r.prop_positiva)} positivas, {num(r.total_avaliacoes)} avaliações", 10)
docs.append({"texto": f"A base do projeto tem {len(b)} jogos da Steam, coletados em {COLETA} pela API do SteamSpy "
             f"(jogadores, donos, avaliações) e pela Steam Store API (preço em reais, gêneros, datas). "
             f"{int(b.gratuito.sum())} jogos são gratuitos e {int((~b.gratuito).sum())} são pagos. "
             f"Em média {pct(b.prop_positiva.mean())} das avaliações de um jogo são positivas. "
             f"Os lançamentos vão de {int(b.ano_lancamento.min())} a {int(b.ano_lancamento.max())}.",
             "titulo": "Sobre a base de dados do projeto", "fonte": "Base do projeto (SteamSpy + Steam Store)",
             "link": "data/processed/steam_tratada.csv", "data": HOJE, "tema": "Ranking da base", "jogo": ""})

# ficha de cada jogo (o campo "jogo" permite filtrar quando a pergunta cita o nome)
for _, r in b.iterrows():
    plat = ", ".join(p for p, ok in [("Windows", r.windows), ("Mac", r.mac), ("Linux", r.linux)] if ok)
    t = (f"{r.nome} - preço: {preco(r)}"
         + (f" (com {r.desconto_pct}% de desconto)" if r.desconto_pct > 0 else "") + ". "
         f"Lançamento: {r.data_lancamento}. Gêneros: {r.generos or 'não informado'}. "
         f"Desenvolvedora: {r.desenvolvedora}. Publicadora: {r.publicadora}. "
         f"Avaliações: {pct(r.prop_positiva)} positivas de {num(r.total_avaliacoes)} ({r.classificacao}). "
         f"Jogadores simultâneos: {num(r.jogadores_simultaneos)} (posição {int(pos_jogados[_])} entre os {len(b)} mais jogados da base). "
         f"Donos estimados: cerca de {num(r.donos_medio)}. "
         + (f"Nota no Metacritic: {num(r.metacritic)}. " if pd.notna(r.metacritic) else "")
         + f"Plataformas: {plat}. Idiomas: {r.n_idiomas}. Conquistas: {r.n_conquistas}. DLCs: {r.n_dlcs}. "
         f"Multiplayer: {'sim' if r.multiplayer else 'não'}. Acesso antecipado: {'sim' if r.early_access else 'não'}. "
         f"Idade mínima: {r.idade_minima if r.idade_minima else 'livre'}.")
    docs.append({"texto": t, "titulo": f"{r.nome}: ficha com os números do jogo", "fonte": "Base do projeto (SteamSpy + Steam Store)",
                 "link": f"https://store.steampowered.com/app/{r.appid}", "data": HOJE, "tema": "Ficha do jogo", "jogo": r.nome})

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
modelo = carregar_modelo()          # usa modelos/minilm se existir (sem internet)
embs = modelo.encode([m["titulo"] + "\n" + t for m, t in zip(metas, textos)],
                     batch_size=64, show_progress_bar=True)       # matriz n_chunks x 384

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
