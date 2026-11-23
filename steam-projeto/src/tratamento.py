"""
Etapa 4 - Tratamento dos dados

Junta a Store API com o SteamSpy, limpa e cria as variáveis derivadas.
Entrada : data/raw/steamspy_all.csv e data/raw/appdetails.jsonl
Saída   : data/processed/steam_tratada.csv  (base final usada nas análises)
          data/processed/relatorio_tratamento.txt (o que foi removido e por quê)

Como rodar:  python src/tratamento.py
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

RAW, PROC = Path("data/raw"), Path("data/processed")
PROC.mkdir(parents=True, exist_ok=True)
log = []                      # vai registrar cada passo do tratamento


def registrar(msg, df):
    linha = f"{msg}: {len(df)} linhas"
    log.append(linha)
    print(linha)


# ------------------------------------------------------------ 1. Carregar
spy = pd.read_csv(RAW / "steamspy_all.csv")
with open(RAW / "appdetails.jsonl", encoding="utf-8") as f:
    det = [json.loads(l) for l in f]
det = [d["data"] for d in det if d["ok"] and d["data"]]


def contar_idiomas(txt):
    """'English<strong>*</strong>, French, ...' -> 2. Remove o HTML antes de contar."""
    txt = re.sub(r"<[^>]+>", "", txt or "")
    txt = txt.split("languages with full audio")[0]
    return len([x for x in txt.split(",") if x.strip()])


linhas = []
for d in det:
    preco = d.get("price_overview") or {}
    linhas.append({
        "appid": d.get("steam_appid"),
        "nome": d.get("name"),
        "tipo": d.get("type"),
        "gratuito": bool(d.get("is_free")),
        # preço vem em centavos; sem price_overview = grátis OU pago sem venda no Brasil
        "preco_brl": preco["final"] / 100 if preco else (0.0 if d.get("is_free") else np.nan),
        "preco_original_brl": preco["initial"] / 100 if preco else (0.0 if d.get("is_free") else np.nan),
        "desconto_pct": preco.get("discount_percent", 0),
        "data_lancamento": (d.get("release_date") or {}).get("date"),
        "windows": (d.get("platforms") or {}).get("windows", False),
        "mac": (d.get("platforms") or {}).get("mac", False),
        "linux": (d.get("platforms") or {}).get("linux", False),
        "metacritic": (d.get("metacritic") or {}).get("score"),
        "recomendacoes": (d.get("recommendations") or {}).get("total"),
        "generos": ", ".join(g["description"] for g in d.get("genres", [])),
        "categorias": ", ".join(c["description"] for c in d.get("categories", [])),
        "desenvolvedora": ", ".join(d.get("developers", [])),
        "publicadora": ", ".join(d.get("publishers", [])),
        "n_idiomas": contar_idiomas(d.get("supported_languages")),
        "idade_minima": int(d.get("required_age") or 0) if str(d.get("required_age") or 0).isdigit() else 0,
        "n_conquistas": (d.get("achievements") or {}).get("total", 0),
        "n_dlcs": len(d.get("dlc") or []),
    })
store = pd.DataFrame(linhas)
registrar("Jogos com detalhes na Store API", store)

# ------------------------------------------------------------ 2. Juntar
df = store.merge(
    spy[["appid", "positive", "negative", "owners", "ccu"]],
    on="appid", how="left")

# ------------------------------------------------------------ 3. Limpar
df = df.drop_duplicates("appid")
registrar("Depois de remover duplicados", df)

df = df[df["tipo"] == "game"]              # tira DLC, software, demos, trilhas
registrar("Só tipo 'game'", df)

df["data_lancamento"] = pd.to_datetime(df["data_lancamento"], format="mixed", errors="coerce")
df = df.dropna(subset=["data_lancamento"])  # sem data não entra na análise por ano
registrar("Com data de lançamento válida", df)

# ------------------------------------------------------------ 4. Variáveis derivadas
df["ano_lancamento"] = df["data_lancamento"].dt.year
df["idade_anos"] = (pd.Timestamp("today") - df["data_lancamento"]).dt.days / 365.25
df["total_avaliacoes"] = df["positive"] + df["negative"]
df = df[df["total_avaliacoes"] >= 50]       # poucas avaliações = proporção instável
registrar("Com pelo menos 50 avaliações", df)

df["prop_positiva"] = df["positive"] / df["total_avaliacoes"]
# owners vem como "1,000,000 .. 2,000,000": guardamos o limite de baixo e o ponto médio
faixa = df["owners"].str.replace(",", "").str.split(r"\s*\.\.\s*", expand=True).astype(float)
df["donos_min"], df["donos_medio"] = faixa[0], (faixa[0] + faixa[1]) / 2
# Obs.: o SteamSpy hoje devolve tempo de jogo = 0 para todos os jogos, por isso não usamos essa variável.
df = df.rename(columns={"ccu": "jogadores_simultaneos"})   # pico de jogadores ao mesmo tempo (dia anterior)
df["n_generos"] = df["generos"].str.count(",") + (df["generos"] != "").astype(int)
df["multiplayer"] = df["categorias"].str.contains("Multi-player|PvP|Online", regex=True)
df["early_access"] = df["generos"].str.contains("Early Access")
df.loc[df["gratuito"], ["preco_brl", "preco_original_brl"]] = 0   # alguns gratuitos mostram preço de pacote: vira 0
df["faixa_preco"] = pd.cut(df["preco_brl"], [-0.01, 0, 30, 80, 150, 10_000],
                           labels=["Grátis", "Até R$30", "R$30-80", "R$80-150", "Acima de R$150"])
df["classificacao"] = pd.cut(df["prop_positiva"], [0, .40, .70, .80, .95, 1.0],
                             labels=["Negativa", "Mista", "Positiva", "Muito positiva", "Extremamente positiva"],
                             include_lowest=True)
df["sem_preco_br"] = df["preco_brl"].isna()   # jogo pago que não está à venda no Brasil (preço fica vazio)

df = df.drop(columns=["tipo", "owners"])
df.to_csv(PROC / "steam_tratada.csv", index=False)
registrar("BASE FINAL", df)

nulos = df.isna().sum()
log.append("\nValores nulos por coluna (os que restaram):\n" + nulos[nulos > 0].to_string())
(PROC / "relatorio_tratamento.txt").write_text("\n".join(log), encoding="utf-8")
