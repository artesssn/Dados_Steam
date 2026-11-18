"""
Etapa 6 - Machine Learning

Pergunta: dá para prever, só com características do jogo (preço, gêneros,
plataformas, idiomas...), se ele vai ser "muito bem avaliado" (>= 80% positivas)?

- Alvo (y): 1 se prop_positiva >= 0,80, senão 0
- NÃO usamos positive, negative, total_avaliacoes nem recomendacoes como
  entrada: elas são o próprio resultado e causariam vazamento de dados.
- Comparamos 3 modelos: baseline (chuta a classe mais comum), Regressão
  Logística e Random Forest, com validação cruzada de 5 partes.
- Extra: K-Means agrupa os jogos em perfis.

Saída: docs/resultados_ml.md e figuras/09_*, 10_*, 11_*
Como rodar:  python src/ml.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, classification_report,
                             f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FIG, DOCS = Path("figuras"), Path("docs")
df = pd.read_csv("data/processed/steam_tratada.csv")
df = df[df["preco_brl"].notna()].reset_index(drop=True)   # tira jogos pagos sem preço no Brasil
out = ["# Resultados de Machine Learning\n"]

# ----------------------------------------------------- 1. Alvo e features
df["alvo"] = (df["prop_positiva"] >= 0.80).astype(int)
GENEROS = ["Action", "Adventure", "RPG", "Strategy", "Simulation", "Indie", "Casual",
           "Massively Multiplayer", "Sports", "Racing", "Early Access"]
for g in GENEROS:
    df["gen_" + g] = df["generos"].fillna("").str.contains(g, regex=False).astype(int)
df["controle"] = df["categorias"].fillna("").str.contains("Controller").astype(int)
df["coop"] = df["categorias"].fillna("").str.contains("Co-op").astype(int)

FEATURES = ["preco_brl", "gratuito", "n_idiomas", "n_generos", "multiplayer", "ano_lancamento",
            "mac", "linux", "n_conquistas", "n_dlcs", "idade_minima", "controle", "coop"] + ["gen_" + g for g in GENEROS]
X = df[FEATURES].astype(float)
y = df["alvo"]
out.append(f"- Jogos: {len(df)} | classe 1 (>=80% positivas): {y.sum()} ({y.mean():.0%}) | classe 0: {(1 - y).sum()}\n"
           f"- Features ({len(FEATURES)}): {', '.join(FEATURES)}\n")

# ----------------------------------------------------- 2. Treino e teste
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
modelos = {
    "Baseline (classe mais comum)": DummyClassifier(strategy="most_frequent"),
    "Regressão Logística": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced")),
    "Random Forest": RandomForestClassifier(n_estimators=400, min_samples_leaf=3, class_weight="balanced", random_state=42),
}
linhas = []
for nome, m in modelos.items():
    cv = cross_val_score(m, X_tr, y_tr, cv=5, scoring="f1_macro")
    m.fit(X_tr, y_tr)
    p = m.predict(X_te)
    prob = m.predict_proba(X_te)[:, 1]
    linhas.append({"modelo": nome, "F1 macro (CV 5)": f"{cv.mean():.3f} ± {cv.std():.3f}",
                   "acurácia": accuracy_score(y_te, p), "precisão": precision_score(y_te, p, zero_division=0),
                   "recall": recall_score(y_te, p), "F1 macro": f1_score(y_te, p, average="macro"),
                   "ROC AUC": roc_auc_score(y_te, prob) if len(set(prob)) > 1 else 0.5})
res = pd.DataFrame(linhas).set_index("modelo")
out.append("## Comparação dos modelos (conjunto de teste, 25%)\n" + res.round(3).to_markdown() + "\n")

rf = modelos["Random Forest"]
CERCA = "`" * 3   # três crases: bloco de código no markdown
out.append("\n## Relatório do Random Forest\n" + CERCA + "\n" + classification_report(y_te, rf.predict(X_te),
           target_names=["< 80%", ">= 80%"]) + CERCA + "\n")
ConfusionMatrixDisplay.from_estimator(rf, X_te, y_te, display_labels=["< 80%", ">= 80%"], cmap="Blues")
plt.title("Matriz de confusão - Random Forest"); plt.tight_layout(); plt.savefig(FIG / "09_matriz_confusao.png", dpi=130); plt.close()

imp = pd.Series(rf.feature_importances_, index=FEATURES).sort_values(ascending=False)
plt.figure(figsize=(7, 6)); sns.barplot(x=imp.head(15).values, y=imp.head(15).index, color="#2f8fb0")
plt.title("Importância das variáveis (Random Forest)"); plt.tight_layout(); plt.savefig(FIG / "10_importancia.png", dpi=130); plt.close()
out.append("## Importância das variáveis (top 10)\n" + imp.head(10).round(3).to_frame("importância").to_markdown() + "\n")
out.append("\n![Matriz](../figuras/09_matriz_confusao.png)\n\n![Importância](../figuras/10_importancia.png)\n")

# ----------------------------------------------------- 3. Clusterização (extra)
cl_cols = ["preco_brl", "jogadores_simultaneos", "n_idiomas", "prop_positiva", "n_conquistas"]
import numpy as np
Z = StandardScaler().fit_transform(np.log1p(df[cl_cols].fillna(0).clip(lower=0)))   # log: suaviza valores enormes (ex.: jogadores)
km = KMeans(n_clusters=4, n_init=20, random_state=42).fit(Z)
df["perfil"] = km.labels_
perfis = df.groupby("perfil").agg(jogos=("appid", "count"), preco=("preco_brl", "mean"),
                                  jogadores=("jogadores_simultaneos", "median"), idiomas=("n_idiomas", "mean"),
                                  pct_positiva=("prop_positiva", "mean"), conquistas=("n_conquistas", "median"),
                                  exemplo=("nome", lambda s: ", ".join(s.head(3))))
out.append("## Clusterização K-Means (4 perfis)\n" + perfis.round(2).to_markdown() + "\n")
plt.figure(figsize=(7, 4)); sns.scatterplot(data=df, x="preco_brl", y="prop_positiva", hue="perfil", palette="deep", alpha=.6)
plt.title("Perfis de jogos (K-Means)"); plt.tight_layout(); plt.savefig(FIG / "11_clusters.png", dpi=130); plt.close()
df[["appid", "nome", "perfil"]].to_csv("data/processed/perfis_kmeans.csv", index=False)

NOMES = {"preco_brl": "preço", "ano_lancamento": "ano de lançamento", "n_conquistas": "número de conquistas",
         "n_idiomas": "número de idiomas", "n_dlcs": "número de DLCs", "multiplayer": "ter multijogador",
         "n_generos": "número de gêneros", "gratuito": "ser gratuito", "idade_minima": "idade mínima",
         "controle": "suporte a controle", "coop": "ter cooperativo", "mac": "rodar no Mac", "linux": "rodar no Linux"}
NOMES.update({"gen_" + g: "gênero " + g for g in GENEROS})
r_rf, r_lr, r_bl = res.loc["Random Forest"], res.loc["Regressão Logística"], res.loc["Baseline (classe mais comum)"]
achados = [
    f"O modelo de Machine Learning tenta prever se um jogo terá 80% ou mais de avaliações positivas, usando só características do jogo "
    f"(preço, gêneros, plataformas, idiomas, conquistas, DLCs). {y.mean():.0%} dos jogos da base estão nessa classe.",
    f"Resultados no teste: Random Forest com F1 macro {r_rf['F1 macro']:.2f} e ROC AUC {r_rf['ROC AUC']:.2f}; "
    f"Regressão Logística com F1 macro {r_lr['F1 macro']:.2f} e ROC AUC {r_lr['ROC AUC']:.2f}; "
    f"o baseline que sempre chuta a classe mais comum tem F1 macro {r_bl['F1 macro']:.2f}.",
    "No modelo que prevê se um jogo será bem avaliado, as variáveis que mais pesaram (importância no Random Forest) foram: " +
    ", ".join(f"{NOMES.get(k, k)} ({v:.2f})" for k, v in imp.head(5).items()) +
    ". Importância alta não diz se a variável aumenta ou diminui a avaliação, só que ela ajuda a separar as classes.",
    "A clusterização K-Means separou os jogos em 4 perfis: " +
    "; ".join(f"perfil {i}: {r.jogos} jogos, preço médio R$ {r.preco:.0f}, {r.pct_positiva:.0%} positivas (ex.: {r.exemplo})" for i, r in perfis.iterrows()) + ".",
]
TITULOS = ["Objetivo do modelo de Machine Learning", "Desempenho dos modelos (métricas)", "Variáveis mais importantes do modelo (o que mais pesou)", "Perfis de jogos encontrados pela clusterização K-Means"]
(DOCS / "achados_ml.txt").write_text("\n".join(f"{t} | {a}" for t, a in zip(TITULOS, achados)), encoding="utf-8")
(DOCS / "resultados_ml.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
