"""
Etapa 7 - Painel analítico (Streamlit) + aba do agente RAG

Como rodar (a partir da pasta do projeto):
    streamlit run app/painel.py
Abre no navegador em http://localhost:8501

As telas estão explicadas em docs/guia_do_sistema.md.
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Painel Steam", page_icon="🎮", layout="wide")
ORDEM_PRECO = ["Grátis", "Até R$30", "R$30-80", "R$80-150", "Acima de R$150"]


def sem_cifrao(txt):
    """O Streamlit lê "$...$" como fórmula; escapar o "$" mantém o "R$" como texto."""
    return str(txt).replace("$", "\\$")


@st.cache_data
def carregar():
    df = pd.read_csv("data/processed/steam_tratada.csv")
    df["faixa_preco"] = pd.Categorical(df["faixa_preco"], ORDEM_PRECO, ordered=True)
    df["modelo_preco"] = df["gratuito"].map({True: "Grátis", False: "Pago"})
    df["tem_multiplayer"] = df["multiplayer"].map({True: "Com multiplayer", False: "Sem multiplayer"})
    df["plataformas"] = df.apply(lambda r: ", ".join(p for p, ok in [("Windows", r.windows), ("macOS", r.mac),
                                                                       ("Linux", r.linux)] if ok), axis=1)
    df["desenvolvedora"] = df["desenvolvedora"].fillna("")
    return df


df = carregar()
generos_todos = sorted({g for gs in df.generos.dropna() for g in gs.split(", ") if g})

# ======================================================================= FILTROS
st.sidebar.header("Filtros")

st.sidebar.subheader("Lançamento e catálogo")
ano_min, ano_max = int(df.ano_lancamento.min()), int(df.ano_lancamento.max())
anos = st.sidebar.slider("Ano de lançamento", ano_min, ano_max, (ano_min, ano_max), step=1)
generos = st.sidebar.multiselect("Gêneros", generos_todos, placeholder="Todos os gêneros")
dev = st.sidebar.text_input("Desenvolvedora", placeholder="Parte do nome, ex.: valve")
modelo = st.sidebar.radio("Modelo de preço", ["Todos", "Grátis", "Pagos"], horizontal=True)
teto = int(df.preco_brl.max()) + 1
preco = st.sidebar.slider("Preço no Brasil (R$)", 0, teto, (0, teto))
com_sem_preco = st.sidebar.checkbox("Incluir jogos sem preço disponível", value=True)

st.sidebar.subheader("Avaliações e popularidade")
pos = st.sidebar.slider("Avaliações positivas (%)", 0, 100, (0, 100))
min_aval = st.sidebar.number_input("Mínimo de avaliações", min_value=0, value=0, step=1000)
meta = st.sidebar.slider("Metacritic", 0, 100, (0, 100))
com_sem_meta = st.sidebar.checkbox("Incluir jogos sem nota Metacritic", value=True)

st.sidebar.subheader("Características")
plats = st.sidebar.multiselect("Exigir suporte às plataformas", ["Windows", "macOS", "Linux"], placeholder="Nenhuma exigida")
multi = st.sidebar.radio("Multiplayer", ["Todos", "Somente com multiplayer", "Somente sem multiplayer"])
acesso = st.sidebar.radio("Acesso antecipado", ["Todos", "Somente acesso antecipado", "Somente lançamentos completos"])
idi_max = int(df.n_idiomas.max())
idiomas = st.sidebar.slider("Idiomas suportados", 0, idi_max, (0, idi_max))

# Cada filtro vira uma condição verdadeiro/falso por jogo; o jogo fica se passar em todas.
f = df[df.ano_lancamento.between(*anos)]
if generos:   # qualquer um dos gêneros escolhidos
    f = f[f.generos.fillna("").apply(lambda s: any(g in s.split(", ") for g in generos))]
if dev.strip():
    f = f[f.desenvolvedora.str.contains(dev.strip(), case=False, regex=False)]
if modelo == "Grátis":
    f = f[f.gratuito]
elif modelo == "Pagos":
    f = f[~f.gratuito]
f = f[f.preco_brl.between(*preco) | (f.preco_brl.isna() & com_sem_preco)]
f = f[(f.prop_positiva * 100).between(*pos)]
f = f[f.total_avaliacoes >= min_aval]
f = f[f.metacritic.between(*meta) | (f.metacritic.isna() & com_sem_meta)]
for p, col in [("Windows", "windows"), ("macOS", "mac"), ("Linux", "linux")]:
    if p in plats:   # precisa suportar TODAS as plataformas escolhidas
        f = f[f[col]]
if multi != "Todos":
    f = f[f.multiplayer == (multi == "Somente com multiplayer")]
if acesso != "Todos":
    f = f[f.early_access == (acesso == "Somente acesso antecipado")]
f = f[f.n_idiomas.between(*idiomas)]

# ======================================================================= CABEÇALHO
st.title("🎮 O que faz um jogo dar certo na Steam?")
st.write("Dados públicos da Steam Store e do SteamSpy: avaliação, preço, gêneros e popularidade. "
         "Use os filtros à esquerda para escolher o recorte e a aba **Agente de dados** para fazer perguntas.")
st.caption(f"**{len(f)}** de {len(df)} jogos correspondem aos filtros atuais.")
aba_painel, aba_agente = st.tabs(["Painel analítico", "Agente de dados"])

# Opções usadas nas abas Composição e Comparações: rótulo -> (coluna, separar valores com vírgula?)
DIMENSOES = {"Faixa de preço": ("faixa_preco", False), "Gênero": ("generos", True),
             "Perfil de avaliação": ("classificacao", False), "Modelo de preço": ("modelo_preco", False),
             "Multiplayer": ("tem_multiplayer", False), "Plataformas": ("plataformas", True)}


def por_categoria(dados, rotulo):
    """Uma linha por (jogo, categoria). Gênero e plataforma: um jogo pode cair em várias."""
    col, separar = DIMENSOES[rotulo]
    d = dados.assign(categoria=dados[col].astype(str))
    if separar:
        d = d.assign(categoria=d.categoria.str.split(", ")).explode("categoria")
    return d[d.categoria.notna() & (d.categoria.str.strip() != "") & (d.categoria != "nan")]


with aba_painel:
    if f.empty:
        st.warning("Nenhum jogo corresponde a esses filtros. Afrouxe algum filtro na barra lateral.")
    else:
        # --------------------------------------------------------- Indicadores
        pagos = f[f.preco_brl > 0]
        k = st.columns(5)
        k[0].metric("Jogos no recorte", f"{len(f)}")
        k[1].metric("Avaliações positivas (média)", f"{f.prop_positiva.mean():.1%}")
        k[2].metric("Preço mediano dos pagos", f"R$ {pagos.preco_brl.median():.2f}" if len(pagos) else "-")
        k[3].metric("Jogos gratuitos", f"{f.gratuito.mean():.0%}")
        k[4].metric("Avaliações somadas", f"{f.total_avaliacoes.sum() / 1e6:.1f} mi")

        st.markdown("**Mais detalhes do recorte**")
        d = st.columns(3)
        d[0].metric("Jogadores simultâneos (mediana)", f"{f.jogadores_simultaneos.median():,.0f}".replace(",", "."))
        d[1].metric("Metacritic (média disponível)", f"{f.metacritic.mean():.0f}" if f.metacritic.notna().any() else "-")
        d[2].metric("Idiomas suportados (mediana)", f"{f.n_idiomas.median():.0f}")

        if f.gratuito.any() and (~f.gratuito).any():
            g, p = f[f.gratuito].prop_positiva.mean(), f[~f.gratuito].prop_positiva.mean()
            st.info(f"Neste recorte, os jogos grátis têm {g:.1%} de avaliações positivas em média, "
                    f"contra {p:.1%} dos pagos.")

        # --------------------------------------------------------- Gráficos
        t1, t2, t3 = st.tabs(["Composição", "Comparações", "Evolução"])

        with t1:   # pizza
            c = st.columns(3)
            dim = c[0].selectbox("Distribuir por", list(DIMENSOES), key="comp_dim")
            tam = c[1].selectbox("Tamanho das fatias", ["Quantidade de jogos", "Total de avaliações"])
            n_cat = c[2].slider("Categorias exibidas", 3, 15, 8)
            dd = por_categoria(f, dim)
            serie = (dd.groupby("categoria").size() if tam == "Quantidade de jogos"
                     else dd.groupby("categoria").total_avaliacoes.sum()).sort_values(ascending=False)
            if len(serie) > n_cat:   # as menores viram "Outros"
                serie = pd.concat([serie.head(n_cat), pd.Series({"Outros": serie.iloc[n_cat:].sum()})])
            fig = px.pie(names=serie.index, values=serie.values, hole=0.35, title=f"{tam} por {dim.lower()}")
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(fig, width="stretch")
            if DIMENSOES[dim][1]:
                st.caption("Um jogo com vários valores aparece em mais de uma fatia: a soma conta ocorrências, não jogos únicos.")

        with t2:   # colunas
            c = st.columns(3)
            dim = c[0].selectbox("Comparar por", list(DIMENSOES), key="cmp_dim")
            ind = c[1].selectbox("Indicador", ["Quantidade de jogos", "Média de avaliações positivas",
                                               "Mediana de jogadores simultâneos", "Preço mediano"])
            minimo = c[2].slider("Mínimo de jogos por grupo", 1, 50, 5)
            dd = por_categoria(f, dim)
            if ind == "Preço mediano":   # grátis e sem preço no Brasil não entram
                dd = dd[dd.preco_brl > 0]
            calc = {"Quantidade de jogos": ("appid", "count"), "Média de avaliações positivas": ("prop_positiva", "mean"),
                    "Mediana de jogadores simultâneos": ("jogadores_simultaneos", "median"),
                    "Preço mediano": ("preco_brl", "median")}[ind]
            tab = (dd.groupby("categoria").agg(valor=calc, jogos=("appid", "count"))
                     .query("jogos >= @minimo").sort_values("valor", ascending=False).head(15).reset_index())
            if tab.empty:
                st.info("Nenhum grupo tem o mínimo de jogos escolhido. Diminua o mínimo.")
            else:
                fig = px.bar(tab, x="categoria", y="valor", hover_data={"jogos": True}, title=f"{ind} por {dim.lower()}",
                             labels={"categoria": dim, "valor": ind, "jogos": "Jogos no grupo"})
                if ind == "Média de avaliações positivas":
                    fig.update_yaxes(tickformat=".0%")
                st.plotly_chart(fig, width="stretch")

        with t3:   # linhas
            ind = st.selectbox("Indicador ao longo do tempo", ["Média de avaliações positivas", "Quantidade de jogos",
                                                               "Total de avaliações", "Mediana de jogadores simultâneos",
                                                               "Preço mediano"])
            dd = f[f.preco_brl > 0] if ind == "Preço mediano" else f
            calc = {"Média de avaliações positivas": ("prop_positiva", "mean"), "Quantidade de jogos": ("appid", "count"),
                    "Total de avaliações": ("total_avaliacoes", "sum"),
                    "Mediana de jogadores simultâneos": ("jogadores_simultaneos", "median"),
                    "Preço mediano": ("preco_brl", "median")}[ind]
            ano = dd.groupby("ano_lancamento").agg(valor=calc, jogos=("appid", "count")).reset_index()
            fig = px.line(ano, x="ano_lancamento", y="valor", markers=True, hover_data={"jogos": True},
                          title=f"{ind} por ano de lançamento",
                          labels={"ano_lancamento": "Ano de lançamento", "valor": ind, "jogos": "Jogos"})
            fig.update_xaxes(dtick=1)   # anos de um em um
            if ind == "Média de avaliações positivas":
                fig.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig, width="stretch")

        # --------------------------------------------------------- Lista e conclusões
        with st.expander("Ver jogos do recorte"):
            ordens = {"Avaliações totais": "total_avaliacoes", "Avaliações positivas": "prop_positiva",
                      "Jogadores simultâneos": "jogadores_simultaneos", "Preço": "preco_brl",
                      "Metacritic": "metacritic", "Ano": "ano_lancamento"}
            ordem = st.selectbox("Ordenar jogos por", list(ordens))
            st.dataframe(
                f.sort_values(ordens[ordem], ascending=False)[
                    ["nome", "ano_lancamento", "generos", "preco_brl", "prop_positiva", "total_avaliacoes",
                     "jogadores_simultaneos", "metacritic", "n_idiomas"]],
                hide_index=True, width="stretch", height=420,
                column_config={"nome": "Nome", "ano_lancamento": st.column_config.NumberColumn("Ano", format="%d"),
                               "generos": "Gêneros", "preco_brl": st.column_config.NumberColumn("Preço (R$)", format="%.2f"),
                               "prop_positiva": st.column_config.ProgressColumn("% positivas", min_value=0, max_value=1, format="%.2f"),
                               "total_avaliacoes": st.column_config.NumberColumn("Avaliações", format="%d"),
                               "jogadores_simultaneos": st.column_config.NumberColumn("Jogadores simultâneos", format="%d"),
                               "metacritic": st.column_config.NumberColumn("Metacritic", format="%d"),
                               "n_idiomas": "Idiomas"})

    with st.expander("Conclusões gerais do estudo"):
        for linha in Path("docs/achados_eda.txt").read_text(encoding="utf-8").splitlines():
            if " | " in linha:
                titulo, frase = linha.split(" | ", 1)
                st.markdown(sem_cifrao(f"- **{titulo}:** {frase}"))
        st.caption("Estas conclusões descrevem a base completa e não mudam com os filtros.")

# ======================================================================= AGENTE
with aba_agente:
    st.write("Pergunte sobre os jogos, patch notes ou sobre a nossa análise. O agente busca nos textos "
             "guardados no banco do projeto (PostgreSQL + pgvector) e cita as fontes.")
    pergunta = st.text_input("Sua pergunta", placeholder="Ex.: O que mudou na última atualização do Valheim?")
    if pergunta:
        sys.path.insert(0, "src")
        from agente_rag import responder
        with st.spinner("Buscando..."):
            resp, fontes, trechos = responder(pergunta)
        st.markdown(sem_cifrao(resp).replace("\n", "  \n"))   # mantém R$ e as quebras de linha
        with st.expander("Fontes e trechos usados"):
            for fo, t in zip(fontes, trechos):
                st.markdown(sem_cifrao(f"**{fo}**  \n{t['texto'][:500]}..."))
