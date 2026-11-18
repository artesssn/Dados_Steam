# Apresentação final - roteiro e falas (cerca de 18 minutos)

Regra do enunciado: **todos os integrantes falam**. Cada parte tem um responsável e o texto sugerido da fala.

| # | Parte | Quem | Tempo | Slide / tela |
|---|---|---|---|---|
| 1 | Problema e objetivos | [Integrante 1] | 2 min | slides 1-3 |
| 2 | Base e tratamento | [Integrante 2] | 3 min | slides 4-5 |
| 3 | Análises | [Integrante 3] | 4 min | slides 6-9 |
| 4 | Machine Learning | [Integrante 3 ou 4] | 2 min | slides 10-11 |
| 5 | Demo do painel | [Integrante 4] | 3 min | navegador |
| 6 | Demo do agente (5 perguntas) | [Integrante 5] | 3 min | navegador |
| 7 | Conclusões e recomendações | [Integrante 1] | 1 min | slide 12 |

## Slides (conteúdo de cada um)
1. **Capa:** "O que faz um jogo dar certo na Steam?", nomes, disciplina.
2. **Problema:** a Steam tem dezenas de milhares de jogos e a avaliação dos usuários decide a compra. Pergunta: que características acompanham jogos bem avaliados e populares?
3. **Objetivos e pipeline:** desenho coleta → tratamento → análise → ML → painel → agente.
4. **Base:** fontes (Store API, SteamSpy, Steam News), 1000 jogos coletados, 961 na base final, 35 colunas, coleta em 03/11/2026.
5. **Tratamento:** tabela de linhas por etapa; decisões (datas em inglês, preço vazio para jogos fora de venda, tempo de jogo descartado).
6. **Descritiva:** média de 84,9% de positivas, mediana 88,4%, distribuição concentrada no alto (figura 01).
7. **Grátis × pago:** 78,6% × 86,0%, p < 0,001; gratuitos têm mais jogadores (figura 03).
8. **Gêneros e preço:** Indie no topo (88,2%), Massively Multiplayer embaixo (73,3%); faixa R$30-80 é a melhor (figuras 04 e 05).
9. **Correlação:** só o Metacritic tem correlação moderada (+0,45); o resto é fraco (figura 07).
10. **ML:** tabela de modelos; Random Forest com F1 macro 0,68 contra 0,44 do baseline (figura 09).
11. **Variáveis e perfis:** importância das variáveis (figura 10) e 4 perfis do K-Means.
12. **Conclusões e recomendações** (seção 12 do relatório).

## Falas sugeridas
**1. Problema (Integrante 1):** "A Steam tem dezenas de milhares de jogos. Quando você abre a página de um, a primeira coisa que vê é a porcentagem de avaliações positivas. Nosso projeto pergunta: o que os jogos bem avaliados têm em comum? Preço? Gênero? Ser gratuito? Para responder, montamos um pipeline completo, da coleta na API até um agente que responde perguntas."

**2. Base (Integrante 2):** "Coletamos os mil jogos com mais donos segundo o SteamSpy e buscamos os detalhes de cada um na API da loja, com preço em reais. Depois de tirar duplicados, jogos sem data e jogos com menos de 50 avaliações, ficamos com 961. Duas decisões importantes: pedimos os dados em inglês porque as datas em português não eram reconhecidas, e deixamos vazio o preço dos 87 jogos que não estão à venda no Brasil, para não confundir com jogos gratuitos."

**3. Análises (Integrante 3):** "A média é de 85% de avaliações positivas, e a maioria dos jogos populares é bem avaliada. O primeiro achado é que os gratuitos são mais jogados, mas pior avaliados: 78,6% contra 86%, e o teste de Mann-Whitney confirma que a diferença é significativa. Por gênero, Indie lidera e multijogador massivo fica em último. Por preço, a melhor faixa é a intermediária, entre 30 e 80 reais. E a única correlação forte o bastante para comentar é com a nota da crítica."

**4. ML (Integrante 3/4):** "Testamos se dá para prever se um jogo terá 80% ou mais de positivas só com as características da loja. Um modelo que sempre chuta 'sim' acerta 77%, por isso olhamos o F1 macro. O Random Forest chegou a 0,68, contra 0,44 do chute. Ele ajuda, mas não resolve: a qualidade de um jogo depende de coisas que não estão na loja."

**5. Painel (Integrante 4):** abrir `streamlit run app/painel.py`. Mostrar os indicadores, filtrar "Grátis" e mostrar a média caindo para 78,6%, filtrar o gênero "Indie", passar o mouse num ponto do gráfico preço × avaliação e mostrar a tabela de top jogos.

**6. Agente (Integrante 5):** na aba "Agente de dados", fazer as 5 perguntas:
1. O que mudou na atualização mais recente do Counter-Strike 2?
2. Jogos gratuitos são mais bem avaliados que os pagos?
3. Quais gêneros têm a melhor avaliação dos jogadores?
4. Quais novidades o Valheim anunciou recentemente?
5. Qual variável mais pesou no modelo que prevê se um jogo será bem avaliado?

Em cada uma, abrir "Fontes e trechos usados" para mostrar de onde veio a resposta. Explicar em uma frase: "a pergunta vira um vetor, buscamos os trechos mais parecidos no ChromaDB e o modelo de linguagem responde só com base neles."

**7. Conclusão (Integrante 1):** ler as conclusões e as 2 recomendações da seção 12 do relatório.

## Perguntas que o professor pode fazer (e respostas)
- **Por que não usaram o número de avaliações no modelo?** Porque ele faz parte do resultado: causaria vazamento de dados.
- **Por que Spearman e Mann-Whitney?** A % de positivas não é normal (assimetria de −1,53). Testes não paramétricos não exigem normalidade.
- **A amostra representa a Steam inteira?** Não, só os jogos mais populares. Os jogos ruins quase não aparecem, por isso a média é alta.
- **Por que não usaram tempo de jogo?** O SteamSpy hoje devolve 0 para todos os jogos; trocamos por jogadores simultâneos.
- **E se o agente não souber?** Ele é instruído a dizer que não encontrou a informação, e sempre mostra as fontes.

## Plano B para a demo
- Deixe o painel aberto antes de começar e faça as 5 perguntas uma vez antes, para o modelo de embeddings já estar carregado.
- Tire prints do painel e das 5 respostas do agente e coloque nos slides escondidos ao final, para o caso de a internet ou a API do LLM falhar.
- Leve o projeto num pendrive ou no GitHub.
