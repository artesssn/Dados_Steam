# Guia do sistema e das telas

Este guia apresenta o fluxo do projeto e explica, tela por tela, o que aparece no painel, como usar os filtros e como interpretar os resultados.

## 1. Visão geral

O projeto analisa jogos da Steam combinando dados estruturados, análise estatística, modelos de Machine Learning e busca em textos com um agente RAG.

O fluxo geral é:

1. **Coleta:** obtém avaliações, estimativas de donos e jogadores simultâneos do SteamSpy; detalhes dos jogos e preços da Steam Store; e notícias e atualizações dos jogos.
2. **Tratamento:** combina as fontes, remove registros inadequados, calcula indicadores e salva a base usada pelo painel.
3. **Análise:** gera estatísticas, gráficos e resultados de Machine Learning.
4. **Busca textual:** transforma descrições, notícias, atualizações e conclusões do projeto em documentos pesquisáveis.
5. **Painel:** apresenta os dados em gráficos interativos e permite fazer perguntas ao agente.

O painel usa a base já salva em `data/processed/steam_tratada.csv`. Para apenas abrir e navegar pelo painel, não é necessário repetir a coleta.

## 2. Como abrir o sistema

No terminal, a partir da pasta principal do projeto:

```bash
source .venv/bin/activate
streamlit run app/painel.py
```

Abra o endereço indicado pelo Streamlit — normalmente `http://localhost:8501`. Se aparecer um pedido de e-mail de boas-vindas, deixe o campo vazio e pressione **Enter**.

Na primeira instalação, crie o ambiente virtual e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
docker compose up -d        # banco vetorial: PostgreSQL + pgvector, já carregado com banco_pronto/
```

O painel analítico funciona sem o banco. A aba **Agente de dados** precisa do PostgreSQL ligado (`docker compose up -d`).

## 3. Mapa de navegação

Na parte superior do painel existem duas abas principais:

- **Painel analítico:** filtros, indicadores, gráficos, lista de jogos e conclusões do estudo.
- **Agente de dados:** campo para perguntar sobre jogos, atualizações e resultados das análises.

Dentro de **Painel analítico**, há três abas de gráficos: **Composição**, **Comparações** e **Evolução**.

## 4. Tela principal — Painel analítico

### 4.1 Cabeçalho e quantidade de jogos

No topo aparecem o título do projeto, uma breve explicação e a quantidade de jogos que corresponde aos filtros atuais, comparada ao total da base.

Os filtros são combinados: um jogo precisa atender a todos os grupos de filtros ativos. Se nenhum jogo corresponder, o painel mostra um aviso; a aba do agente continua disponível.

### 4.2 Barra lateral — filtros

Os filtros ficam à esquerda da tela:

#### Lançamento e catálogo

- **Ano de lançamento:** seleciona o intervalo de anos. O início e o fim podem ser ajustados ano a ano.
- **Gêneros:** permite escolher um ou mais gêneros. Quando vários são escolhidos, o jogo pode corresponder a qualquer um deles.
- **Desenvolvedora:** busca por parte do nome, sem diferenciar maiúsculas e minúsculas.
- **Modelo de preço:** mostra todos os jogos, somente os grátis ou somente os pagos.
- **Preço no Brasil (R$):** limita o intervalo de preços.
- **Incluir jogos sem preço disponível:** mantém jogos cujo preço brasileiro não consta na base.

#### Avaliações e popularidade

- **Avaliações positivas (%):** limita a proporção de avaliações positivas.
- **Mínimo de avaliações:** remove jogos abaixo do número escolhido.
- **Metacritic:** limita a nota Metacritic.
- **Incluir jogos sem nota Metacritic:** mantém registros sem essa nota.

#### Características

- **Exigir suporte às plataformas:** se uma ou mais plataformas forem escolhidas, o jogo precisa oferecer suporte a todas as selecionadas. Sem seleção, nenhuma plataforma é exigida.
- **Multiplayer:** mostra todos, somente jogos com multiplayer ou somente jogos sem multiplayer.
- **Acesso antecipado:** mostra todos, somente acesso antecipado ou somente lançamentos completos.
- **Idiomas suportados:** limita a quantidade de idiomas.

### 4.3 Indicadores do recorte

Logo abaixo dos filtros e do cabeçalho, os cartões resumem os jogos encontrados:

- **Jogos no recorte:** quantidade de jogos após a aplicação dos filtros.
- **Avaliações positivas (média):** média da proporção de avaliações positivas.
- **Preço mediano dos pagos:** mediana dos preços maiores que zero.
- **Jogos gratuitos:** proporção de jogos grátis no recorte.
- **Avaliações somadas:** soma das avaliações positivas e negativas disponíveis.

Na linha **Mais detalhes do recorte** aparecem a mediana de jogadores simultâneos, a média do Metacritic disponível e a mediana de idiomas suportados.

Quando o recorte inclui jogos grátis e pagos, uma mensagem compara a média de avaliações positivas entre os dois grupos.

## 5. Abas de gráficos

Todos os gráficos do painel usam um destes formatos: pizza, colunas ou linhas.

### 5.1 Aba “Composição” — gráfico de pizza

Mostra como os jogos ou as avaliações se distribuem entre categorias.

Controles:

- **Distribuir por:** escolhe faixa de preço, gênero, perfil de avaliação, modelo de preço, multiplayer ou plataformas.
- **Tamanho das fatias:** escolhe quantidade de jogos ou total de avaliações.
- **Categorias exibidas:** define quantas categorias principais aparecem. As demais são reunidas em “Outros”.

Ao distribuir por gênero, um jogo com vários gêneros aparece em mais de uma fatia. Por isso, a soma das fatias representa ocorrências por gênero, e não necessariamente jogos únicos.

Passe o cursor sobre as fatias para ver os valores.

### 5.2 Aba “Comparações” — gráfico de colunas

Compara grupos e ordena os resultados pelo indicador selecionado.

Controles:

- **Comparar por:** escolhe gênero, faixa de preço, perfil de avaliação, modelo de preço, multiplayer ou plataformas.
- **Indicador:** escolhe quantidade de jogos, média de avaliações positivas, mediana de jogadores simultâneos ou preço mediano.
- **Mínimo de jogos por grupo:** evita comparar categorias com poucas observações.

O gráfico mostra até 15 grupos. Para o preço mediano, jogos grátis e jogos sem preço brasileiro são desconsiderados. O cursor sobre uma coluna mostra o indicador e a quantidade de jogos do grupo.

### 5.3 Aba “Evolução” — gráfico de linhas

Mostra como um indicador varia conforme o ano de lançamento. O eixo horizontal apresenta os anos de um em um.

No menu **Indicador ao longo do tempo**, escolha:

- média de avaliações positivas;
- quantidade de jogos;
- total de avaliações;
- mediana de jogadores simultâneos;
- preço mediano.

O preço mediano considera somente jogos com preço maior que zero. Os valores do gráfico são calculados depois da aplicação dos filtros.

## 6. Lista de jogos e conclusões

### Ver jogos do recorte

Expanda **Ver jogos do recorte**, abaixo dos gráficos, para consultar a tabela dos jogos filtrados. O menu **Ordenar jogos por** permite ordenar por avaliações totais, avaliações positivas, jogadores simultâneos, preço, Metacritic ou ano.

A tabela inclui nome, ano, gêneros, preço, avaliações, jogadores simultâneos, Metacritic e idiomas. Se houver muitos resultados, role dentro da tabela para ver os demais.

### Conclusões gerais do estudo

Expanda **Conclusões gerais do estudo**, no final do painel, para ler os achados da análise exploratória. Esses textos descrevem a base completa e **não mudam** quando os filtros são alterados.

## 7. Tela “Agente de dados”

Selecione **Agente de dados** na navegação superior.

1. Digite uma pergunta no campo **Sua pergunta**, por exemplo: “Jogos gratuitos são mais bem avaliados que os pagos?”.
2. O agente busca trechos relacionados na base textual do projeto.
3. A resposta aparece abaixo do campo, acompanhada de referências numeradas quando há um modelo de linguagem configurado.
4. Expanda **Fontes e trechos usados** para conferir os textos que embasaram a resposta.

O agente funciona em modo só busca: a pergunta é vetorizada, o pgvector devolve os 5 trechos mais parecidos e o painel mostra cada um com fonte, data, similaridade e link. Opcionalmente, um LLM local configurado no `.env` (Ollama ou arquivo GGUF) pode redigir uma resposta a partir desses trechos. O agente consulta somente a base interna do projeto: nenhuma pergunta é enviada para a internet. O banco vetorial (PostgreSQL + pgvector) precisa estar ligado; ele já sobe preenchido com o arquivo de `banco_pronto/` (o `python src/vetorial.py` só é necessário para refazê-lo).

## 8. Etapas de dados e arquivos importantes

| Etapa | Arquivo ou pasta | Função |
|---|---|---|
| Coleta | `src/coleta.py` | Baixa dados da SteamSpy, da Steam Store e notícias. |
| Dados brutos | `data/raw/` | Guarda os dados recebidos das fontes. |
| Tratamento | `src/tratamento.py` | Cria a base limpa em `data/processed/steam_tratada.csv`. |
| Dicionário | `src/dicionario.py` | Gera a documentação das variáveis da base. |
| Análise exploratória | `src/eda.py` | Gera estatísticas, gráficos e resultados da análise. |
| Machine Learning | `src/ml.py` | Compara modelos de classificação e calcula perfis de jogos. |
| Banco textual | `src/vetorial.py`, `src/banco.py`, `docker-compose.yml` | Prepara os documentos e grava textos e embeddings na tabela `documentos` do PostgreSQL com pgvector. |
| Aplicação web | `app/painel.py` | Implementa as telas descritas neste guia. |
| Resposta do agente | `src/agente_rag.py` | Busca trechos e, se configurado, redige respostas com um LLM. |

Para refazer todas as etapas, siga a ordem e os comandos do [README do projeto](../README.md). A coleta completa faz requisições às APIs e pode levar cerca de 30 minutos; use `python src/coleta.py --teste` para uma execução reduzida.

## 9. Como interpretar os números

- **Avaliações positivas** são uma proporção de avaliações, não uma medida direta de vendas ou lucro.
- **Jogadores simultâneos** e **donos estimados** vêm do SteamSpy e são estimativas/indicadores de popularidade, não contagens oficiais de vendas.
- **Preço** é o preço registrado para o Brasil na coleta; pode não estar disponível para todos os jogos e pode mudar com o tempo.
- **Metacritic** está ausente para muitos jogos. Use o filtro correspondente para decidir se os jogos sem nota entram no recorte.
- Comparações entre grupos pequenos podem ser instáveis; ajuste **Mínimo de jogos por grupo** na aba Comparações.
- A base e os dados da Steam podem mudar quando uma nova coleta é executada. Os relatórios existentes refletem a coleta usada para gerá-los.
