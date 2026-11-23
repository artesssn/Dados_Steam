"""
Etapa 3 - Coleta de dados (API da Steam)

O que este script faz, em ordem:
  1. Baixa a lista de jogos do SteamSpy (1000 jogos por página, já com
     avaliações positivas/negativas, donos estimados e jogadores simultâneos).
  2. Para cada jogo, busca os detalhes na Store API da Steam
     (preço, gêneros, data de lançamento, plataformas...).
  3. Para os jogos mais avaliados, baixa notícias e patch notes
     (textos que vão alimentar o agente RAG).

Tudo é salvo em data/raw/. Se o script parar no meio, rode de novo:
ele pula o que já foi baixado (arquivos .jsonl guardam o progresso).

Como rodar (a partir da pasta do projeto):
    python src/coleta.py              # coleta completa
    python src/coleta.py --teste      # só 20 jogos, para testar rápido
"""
import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

SESSAO = requests.Session()
SESSAO.headers["User-Agent"] = "projeto-academico-ciencia-de-dados"


def pegar_json(url, params=None, tentativas=4):
    """GET com novas tentativas. A Steam responde 429 quando passamos do limite."""
    for t in range(tentativas):
        try:
            r = SESSAO.get(url, params=params, timeout=30)
            if r.status_code == 429:          # limite de requisições: espera e tenta de novo
                espera = 60 * (t + 1)
                print(f"  limite atingido, esperando {espera}s...")
                time.sleep(espera)
                continue
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:
            print(f"  erro ({e}), tentativa {t + 1}/{tentativas}")
            time.sleep(5)
    return None


# ---------------------------------------------------------------- 1. SteamSpy
def coletar_steamspy(paginas=1):
    """SteamSpy 'all': 1000 jogos por página, ordenados por donos.
    O endpoint 'all' aceita só 1 requisição por minuto."""
    destino = RAW / "steamspy_all.csv"
    if destino.exists():
        print("SteamSpy já baixado, pulando.")
        return pd.read_csv(destino)
    partes = []
    for p in range(paginas):
        print(f"SteamSpy página {p}...")
        dados = pegar_json("https://steamspy.com/api.php", {"request": "all", "page": p})
        partes.append(pd.DataFrame.from_dict(dados, orient="index"))
        if p < paginas - 1:
            time.sleep(61)
    df = pd.concat(partes, ignore_index=True)
    df.to_csv(destino, index=False)
    print(f"SteamSpy: {len(df)} jogos salvos.")
    return df


# ------------------------------------------------------------ 2. Store API
def coletar_appdetails(appids, pausa=1.6):
    """Detalhes da Store API. l=english para as datas virem em formato que o
    pandas entende ('21 Aug, 2012'); cc=br para o preço vir em reais.
    Limite aproximado: 200 requisições a cada 5 minutos -> pausa de 1,6s."""
    destino = RAW / "appdetails.jsonl"
    feitos = set()
    if destino.exists():
        with open(destino, encoding="utf-8") as f:
            feitos = {json.loads(l)["appid"] for l in f}
    faltam = [a for a in appids if a not in feitos]
    print(f"Store API: {len(feitos)} já baixados, faltam {len(faltam)}.")
    with open(destino, "a", encoding="utf-8") as f:
        for i, appid in enumerate(faltam, 1):
            d = pegar_json("https://store.steampowered.com/api/appdetails",
                           {"appids": appid, "cc": "br", "l": "english"})
            item = (d or {}).get(str(appid), {})
            registro = {"appid": appid, "ok": bool(item.get("success")),
                        "data": item.get("data")}
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
            f.flush()
            if i % 50 == 0:
                print(f"  {i}/{len(faltam)}")
            time.sleep(pausa)


# ------------------------------------------------------- 3. Notícias (RAG)
def coletar_noticias(jogos, por_jogo=5):
    """Notícias e patch notes oficiais (ISteamNews/GetNewsForApp).
    Não precisa de chave. Esses textos são a base do agente RAG."""
    destino = RAW / "noticias.jsonl"
    feitos = set()
    if destino.exists():
        with open(destino, encoding="utf-8") as f:
            feitos = {json.loads(l)["appid"] for l in f}
    with open(destino, "a", encoding="utf-8") as f:
        for appid, nome in jogos:
            if appid in feitos:
                continue
            d = pegar_json("https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/",
                           {"appid": appid, "count": por_jogo, "maxlength": 0, "format": "json",
                            "feeds": "steam_community_announcements"})  # só anúncios oficiais do jogo
            for n in ((d or {}).get("appnews") or {}).get("newsitems", []):
                f.write(json.dumps({
                    "appid": appid, "jogo": nome, "titulo": n.get("title"),
                    "texto": n.get("contents"), "link": n.get("url"),
                    "fonte": "Steam - anúncios oficiais (" + (n.get("feedlabel") or "Community Announcements") + ")",
                    "data": n.get("date"),
                }, ensure_ascii=False) + "\n")
            time.sleep(1)
    print("Notícias salvas.")


if __name__ == "__main__":
    teste = "--teste" in sys.argv
    spy = coletar_steamspy(paginas=1)
    spy["total"] = spy["positive"] + spy["negative"]
    spy = spy.sort_values("total", ascending=False)
    n = 20 if teste else len(spy)
    coletar_appdetails(spy["appid"].head(n).tolist())
    top = spy.head(10 if teste else 80)
    coletar_noticias(list(zip(top["appid"], top["name"])))
