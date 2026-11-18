# Primeira entrega - Projeto Final de Ciência de Dados

**Grupo:** [nomes]   **Turma:** [ ]   **Data:** [ ]

## 1. Tema
Fatores associados ao sucesso de jogos na plataforma Steam: preço, gênero, plataformas e avaliação dos jogadores.

## 2. Problema (pergunta principal)
Quais características de um jogo vendido na Steam (preço, gratuidade, gêneros, plataformas, idiomas, ano de lançamento) estão associadas a uma melhor avaliação dos jogadores e a uma base maior de usuários?

## 3. Justificativa
A Steam é a maior loja de jogos para PC, com dezenas de milhares de títulos e milhares de lançamentos por ano. Com tanta oferta, a avaliação dos usuários se tornou um dos principais filtros de compra: aparece na página de cada jogo e influencia o algoritmo de recomendação da loja. Entender que características acompanham jogos bem avaliados ajuda desenvolvedores independentes e publicadoras a decidir preço, gênero e plataformas, e ajuda jogadores a interpretar a nota que veem na loja. O tema também é viável: os dados são públicos, atualizados e acessíveis por API, e há textos oficiais (notícias e patch notes) que permitem construir o agente de dados.

## 4. Objetivos
**Objetivo geral:** analisar dados públicos da Steam para identificar fatores associados à avaliação e à popularidade dos jogos, apresentando os resultados em um painel interativo e em um agente de dados que responde perguntas sobre o tema.

**Objetivos específicos:**
1. Coletar dados de jogos pela Store API da Steam e pelo SteamSpy.
2. Tratar e documentar a base, com dicionário de dados.
3. Descrever a base com estatística descritiva e comparar grupos (grátis × pago, gêneros, faixas de preço, anos).
4. Medir a correlação entre as variáveis e a proporção de avaliações positivas.
5. Avaliar se é possível prever se um jogo será muito bem avaliado (≥ 80% positivas) com Machine Learning.
6. Construir um painel analítico com indicadores e filtros.
7. Montar um agente RAG que responda perguntas usando notícias e patch notes oficiais e os resultados do grupo.

## 5. Perguntas que o grupo pretende responder
1. Jogos gratuitos são mais ou menos bem avaliados que os pagos? E têm mais jogadores?
2. O preço tem relação com a avaliação?
3. Quais gêneros são mais bem avaliados?
4. Jogos mais recentes são avaliados de forma diferente dos mais antigos?
5. A nota da crítica (Metacritic) concorda com a avaliação dos jogadores?
6. É possível prever, antes do lançamento, se um jogo será muito bem avaliado?

## 6. Base pública escolhida
| Fonte | O que fornece | Acesso |
|---|---|---|
| Steam Store API (`store.steampowered.com/api/appdetails`) | preço em R$, gêneros, categorias, data de lançamento, plataformas, idiomas, Metacritic, conquistas, DLCs | pública, sem chave, JSON |
| SteamSpy (`steamspy.com/api.php`) | avaliações positivas e negativas, faixa de donos estimados, jogadores simultâneos | pública, sem chave, JSON |
| Kaggle - datasets da Steam (plano B) | base pronta caso a coleta falhe | download CSV |

Recorte: os cerca de 1000 jogos com mais donos segundo o SteamSpy, mantendo só os do tipo "game" com pelo menos 50 avaliações.

## 7. Fontes textuais previstas (agente de dados)
- Notícias e patch notes oficiais dos jogos (Steam News API, `ISteamNews/GetNewsForApp`, feed de anúncios oficiais).
- Descrições oficiais dos jogos na loja (Store API).
- Os achados da própria análise do grupo (estatísticas e resultados do modelo), para o agente responder também sobre a base estruturada.

## 8. Ferramentas planejadas
| Etapa | Ferramenta |
|---|---|
| Coleta | Python, requests |
| Tratamento e análise | pandas, NumPy, SciPy |
| Gráficos | Matplotlib, Seaborn, Plotly |
| Machine Learning | scikit-learn (Regressão Logística, Random Forest, K-Means) |
| Painel | Streamlit |
| Embeddings | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) |
| Banco vetorial | PostgreSQL com a extensão pgvector |
| LLM do agente | Qwen2.5-7B local via Ollama (sem API externa) |
| Versionamento | GitHub |
