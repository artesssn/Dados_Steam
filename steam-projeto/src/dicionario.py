"""
Etapa 4 - Dicionário de dados
Gera docs/dicionario_dados.md com tipo, descrição, exemplo, % de nulos e origem
de cada coluna da base tratada.   Como rodar:  python src/dicionario.py
"""
import pandas as pd

df = pd.read_csv("data/processed/steam_tratada.csv")
D = {  # coluna: (descrição, origem)
    "appid": ("Identificador único do jogo na Steam", "Store API"),
    "nome": ("Nome do jogo na loja", "Store API"),
    "gratuito": ("True se o jogo é gratuito (free to play)", "Store API"),
    "preco_brl": ("Preço atual em reais, já com desconto (0 = grátis; vazio = pago sem venda no Brasil)", "Store API (cc=br)"),
    "preco_original_brl": ("Preço sem desconto, em reais", "Store API"),
    "desconto_pct": ("Desconto aplicado no dia da coleta (%)", "Store API"),
    "data_lancamento": ("Data de lançamento", "Store API"),
    "windows": ("Roda no Windows", "Store API"),
    "mac": ("Roda no macOS", "Store API"),
    "linux": ("Roda no Linux / Steam Deck nativo", "Store API"),
    "metacritic": ("Nota da crítica no Metacritic (0-100); vazio quando não há", "Store API"),
    "recomendacoes": ("Total de recomendações exibido pela loja", "Store API"),
    "generos": ("Gêneros, separados por vírgula", "Store API"),
    "categorias": ("Categorias (Single-player, Multi-player, Co-op...), separadas por vírgula", "Store API"),
    "desenvolvedora": ("Desenvolvedora(s)", "Store API"),
    "publicadora": ("Publicadora(s)", "Store API"),
    "n_idiomas": ("Quantidade de idiomas suportados", "derivada (Store API)"),
    "idade_minima": ("Idade mínima indicada pela loja (0 = livre)", "Store API"),
    "n_conquistas": ("Quantidade de conquistas (achievements)", "Store API"),
    "n_dlcs": ("Quantidade de DLCs à venda", "Store API"),
    "positive": ("Avaliações positivas de usuários", "SteamSpy"),
    "negative": ("Avaliações negativas de usuários", "SteamSpy"),
    "jogadores_simultaneos": ("Pico de jogadores simultâneos no dia anterior à coleta", "SteamSpy (ccu)"),
    "ano_lancamento": ("Ano extraído da data de lançamento", "derivada"),
    "idade_anos": ("Anos desde o lançamento até a data da coleta", "derivada"),
    "total_avaliacoes": ("positive + negative", "derivada"),
    "prop_positiva": ("positive / total_avaliacoes (0 a 1)", "derivada"),
    "donos_min": ("Limite inferior da faixa de donos estimada", "derivada (SteamSpy owners)"),
    "donos_medio": ("Ponto médio da faixa de donos estimada", "derivada (SteamSpy owners)"),
    "n_generos": ("Quantidade de gêneros do jogo", "derivada"),
    "multiplayer": ("Tem modo multijogador/online", "derivada (categorias)"),
    "early_access": ("Está ou esteve em Acesso Antecipado", "derivada (gêneros)"),
    "faixa_preco": ("Grátis, Até R$30, R$30-80, R$80-150, Acima de R$150", "derivada"),
    "sem_preco_br": ("True para jogo pago sem preço na loja brasileira (fora de venda); nesses o preço fica vazio", "derivada"),
    "classificacao": ("Negativa (<40%), Mista (40-70%), Positiva (70-80%), Muito positiva (80-95%), Extremamente positiva (95%+)", "derivada"),
}
linhas = []
for c in df.columns:
    desc, origem = D.get(c, ("(descrever)", "-"))
    ex = df[c].dropna().iloc[0] if df[c].notna().any() else ""
    ex = str(ex)[:40].replace("|", "/")
    linhas.append(f"| {c} | {df[c].dtype} | {desc} | {ex} | {df[c].isna().mean():.0%} | {origem} |")
txt = ("# Dicionário de dados - steam_tratada.csv\n\n"
       f"{len(df)} linhas (jogos) e {len(df.columns)} colunas. Coleta feita em {pd.Timestamp('today'):%d/%m/%Y}.\n\n"
       "| Coluna | Tipo | Descrição | Exemplo | Nulos | Origem |\n|---|---|---|---|---|---|\n" + "\n".join(linhas) + "\n")
open("docs/dicionario_dados.md", "w", encoding="utf-8").write(txt)
print(txt[:1500])
