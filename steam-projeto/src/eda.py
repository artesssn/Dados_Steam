"""
Etapa 5 - Análise exploratória e estatística

Gera os números e gráficos do relatório.
Entrada : data/processed/steam_tratada.csv
Saída   : figuras/*.png  e  docs/resultados_eda.md (todos os números, prontos para citar)

Como rodar:  python src/eda.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                       # salva os gráficos sem abrir janela
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats

FIG, DOCS = Path("figuras"), Path("docs")
FIG.mkdir(exist_ok=True); DOCS.mkdir(exist_ok=True)
sns.set_theme(style="whitegrid", palette="deep")
df = pd.read_csv("data/processed/steam_tratada.csv", parse_dates=["data_lancamento"])
ORDEM_PRECO = ["Grátis", "Até R$30", "R$30-80", "R$80-150", "Acima de R$150"]
df["faixa_preco"] = pd.Categorical(df["faixa_preco"], ORDEM_PRECO, ordered=True)   # o CSV perde a ordem


def pval(p):
    return "p < 0,001" if p < 0.001 else f"p = {p:.3f}"
out = ["# Resultados da análise exploratória\n"]


def salvar(nome, titulo):
    plt.title(titulo); plt.tight_layout(); plt.savefig(FIG / nome, dpi=130); plt.close()
    out.append(f"\n![{titulo}](../figuras/{nome})\n")


# 1. Quantidade de registros
out.append(f"## 1. Registros\n- Jogos analisados: **{len(df)}**\n- Período: {df.ano_lancamento.min()} a {df.ano_lancamento.max()}\n"
           f"- Gratuitos: {df.gratuito.sum()} ({df.gratuito.mean():.0%})\n")

# 2. Estatística descritiva (média, mediana, mín, máx, desvio padrão)
cols = {"preco_brl": "Preço (R$)", "prop_positiva": "% positivas", "total_avaliacoes": "Nº avaliações",
        "jogadores_simultaneos": "Jogadores simultâneos", "n_idiomas": "Nº idiomas", "metacritic": "Metacritic"}
desc = df[list(cols)].agg(["count", "mean", "median", "min", "max", "std"]).T
desc.index = [cols[c] for c in desc.index]
desc.columns = ["n", "média", "mediana", "mínimo", "máximo", "desvio padrão"]
out.append("## 2. Estatística descritiva\n" + desc.round(2).to_markdown() + "\n")
pagos = df[~df.gratuito & (df.preco_brl > 0)]
out.append(f"\nSó jogos pagos (n={len(pagos)}): preço médio R$ {pagos.preco_brl.mean():.2f}, "
           f"mediana R$ {pagos.preco_brl.median():.2f}.\n")

# 3. Distribuições
plt.figure(figsize=(7, 4)); sns.histplot(df.prop_positiva * 100, bins=25)
plt.xlabel("% de avaliações positivas"); plt.ylabel("Jogos")
salvar("01_dist_avaliacao.png", "Distribuição da % de avaliações positivas")
plt.figure(figsize=(7, 4)); sns.histplot(pagos.preco_brl, bins=30)
plt.xlabel("Preço (R$)"); plt.ylabel("Jogos")
salvar("02_dist_preco.png", "Distribuição de preços (jogos pagos)")
out.append(f"Assimetria da % positivas: {stats.skew(df.prop_positiva):.2f} "
           "(negativo = cauda para a esquerda, a maioria dos jogos é bem avaliada).\n")

# 4. Comparações entre grupos
g = df.groupby("gratuito").agg(jogos=("appid", "count"), pct_positiva=("prop_positiva", "mean"),
                               mediana_donos=("donos_medio", "median"), mediana_jogadores=("jogadores_simultaneos", "median"))
g.index = g.index.map({True: "Grátis", False: "Pago"})
out.append("## 3. Comparações\n### Grátis × pago\n" + g.round(3).to_markdown() + "\n")
t = stats.mannwhitneyu(df[df.gratuito].prop_positiva, df[~df.gratuito].prop_positiva)
out.append(f"\nTeste de Mann-Whitney (% positivas, grátis × pago): {pval(t.pvalue)} "
           f"({'diferença significativa' if t.pvalue < .05 else 'sem diferença significativa'} a 5%).\n")
plt.figure(figsize=(6, 4)); sns.boxplot(data=df.assign(Tipo=df.gratuito.map({True: "Grátis", False: "Pago"})),
                                         x="Tipo", y="prop_positiva")
plt.ylabel("% positivas"); salvar("03_box_gratis_pago.png", "Avaliação: grátis × pago")

gen = df.assign(genero=df.generos.str.split(", ")).explode("genero")
gen = gen[gen.genero.notna() & (gen.genero != "")]
tg = gen.groupby("genero").agg(jogos=("appid", "count"), pct_positiva=("prop_positiva", "mean"),
                               preco_medio=("preco_brl", "mean")).query("jogos >= 15").sort_values("pct_positiva", ascending=False)
out.append("\n### Por gênero (gêneros com 15+ jogos)\n" + tg.round(3).to_markdown() + "\n")
plt.figure(figsize=(7, 5)); sns.barplot(x=tg.pct_positiva * 100, y=tg.index, color="#2f8fb0")
plt.xlabel("% positivas (média)"); plt.ylabel("")
salvar("04_genero_avaliacao.png", "Avaliação média por gênero")

fp = df.groupby("faixa_preco", observed=True).agg(jogos=("appid", "count"), pct_positiva=("prop_positiva", "mean"))
out.append("\n### Por faixa de preço\n" + fp.round(3).to_markdown() + "\n")
plt.figure(figsize=(7, 4)); sns.boxplot(data=df, x="faixa_preco", y="prop_positiva")
plt.xlabel(""); plt.ylabel("% positivas"); salvar("05_faixa_preco.png", "Avaliação por faixa de preço")

ano = df.groupby("ano_lancamento").agg(jogos=("appid", "count"), pct_positiva=("prop_positiva", "mean"))
plt.figure(figsize=(8, 4)); ano.jogos.plot(marker="o"); plt.xlabel("Ano"); plt.ylabel("Jogos na base")
salvar("06_jogos_por_ano.png", "Jogos da base por ano de lançamento")

# 5. Correlação
num = df[["preco_brl", "prop_positiva", "total_avaliacoes", "jogadores_simultaneos", "n_idiomas",
          "ano_lancamento", "metacritic", "n_conquistas", "desconto_pct"]]
corr = num.corr(method="spearman")       # Spearman: robusto a valores extremos
plt.figure(figsize=(8, 6)); sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
salvar("07_correlacao.png", "Correlação de Spearman entre variáveis")
out.append("## 4. Correlação (Spearman) com a % positivas\n" +
           corr["prop_positiva"].drop("prop_positiva").sort_values().round(3).to_frame("rho").to_markdown() + "\n")
plt.figure(figsize=(7, 4)); sns.scatterplot(data=df[df.metacritic.notna()], x="metacritic", y="prop_positiva", alpha=.5)
salvar("08_metacritic_usuarios.png", "Nota da crítica (Metacritic) × avaliação dos jogadores")

top = df.nlargest(10, "total_avaliacoes")[["nome", "total_avaliacoes", "prop_positiva", "preco_brl"]]
out.append("## 5. Top 10 jogos mais avaliados\n" + top.round(3).to_markdown(index=False) + "\n")

# Achados em frases (é isso que o agente RAG consulta: frase busca melhor que tabela)
gp = g["pct_positiva"]
achados = [
    f"A base tem {len(df)} jogos da Steam lançados entre {df.ano_lancamento.min()} e {df.ano_lancamento.max()}, "
    f"todos com pelo menos 50 avaliações; {df.gratuito.mean():.0%} são gratuitos.",
    f"Em média, {df.prop_positiva.mean():.1%} das avaliações de um jogo são positivas (mediana {df.prop_positiva.median():.1%}, "
    f"desvio padrão {df.prop_positiva.std():.1%}). A distribuição é concentrada nos valores altos: a maioria dos jogos é bem avaliada.",
    f"O preço médio dos jogos pagos é R$ {pagos.preco_brl.mean():.2f} e a mediana é R$ {pagos.preco_brl.median():.2f}; "
    f"o mais caro custa R$ {pagos.preco_brl.max():.2f}.",
    f"Jogos gratuitos têm em média {gp.get('Grátis', float('nan')):.1%} de avaliações positivas, contra {gp.get('Pago', float('nan')):.1%} "
    f"dos jogos pagos. Teste de Mann-Whitney: {pval(t.pvalue)}, "
    f"{'a diferença é estatisticamente significativa' if t.pvalue < .05 else 'a diferença não é estatisticamente significativa'}. "
    f"Em popularidade, a mediana de jogadores simultâneos é {g.loc['Grátis', 'mediana_jogadores']:,.0f} nos gratuitos e "
    f"{g.loc['Pago', 'mediana_jogadores']:,.0f} nos pagos; a mediana de donos estimados é {g.loc['Grátis', 'mediana_donos']:,.0f} "
    f"nos gratuitos e {g.loc['Pago', 'mediana_donos']:,.0f} nos pagos.",
    "Gêneros com melhor avaliação média (com 15 ou mais jogos): " +
    "; ".join(f"{i} ({r.pct_positiva:.1%}, {int(r.jogos)} jogos)" for i, r in tg.head(5).iterrows()) +
    ". Gêneros com pior avaliação média: " + "; ".join(f"{i} ({r.pct_positiva:.1%})" for i, r in tg.tail(3).iterrows()) + ".",
    "Avaliação média por faixa de preço: " + "; ".join(f"{i}: {r.pct_positiva:.1%} ({int(r.jogos)} jogos)" for i, r in fp.iterrows()) + ".",
    "Correlação de Spearman com a % de avaliações positivas: " +
    "; ".join(f"{k} {v:+.2f}" for k, v in corr["prop_positiva"].drop("prop_positiva").sort_values().items()) +
    ". Valores perto de 0 indicam relação fraca.",
    f"Os jogos mais avaliados da base são: " + ", ".join(f"{r.nome} ({r.total_avaliacoes:,.0f} avaliações, {r.prop_positiva:.0%} positivas)" for r in top.head(5).itertuples()) + ".",
]
TITULOS = ['Tamanho e período da base', 'Avaliação média dos jogos', 'Preço dos jogos pagos', 'Jogos gratuitos versus pagos: avaliação e popularidade', 'Gêneros mais e menos bem avaliados', 'Avaliação por faixa de preço', 'Correlação das variáveis com a avaliação', 'Jogos mais avaliados da base']
(DOCS / "achados_eda.txt").write_text("\n".join(f"{t} | {a}" for t, a in zip(TITULOS, achados)), encoding="utf-8")
(DOCS / "resultados_eda.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out)[:3000])
