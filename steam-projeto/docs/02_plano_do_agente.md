# Plano de construção do agente de dados (2ª entrega)

## Objetivo
Responder perguntas em português sobre os jogos da base (novidades, atualizações, descrição) e sobre os resultados da nossa análise, sempre citando a fonte de onde tirou a informação.

## Textos que o agente consulta
| Conjunto | Fonte | Como é coletado | Por que |
|---|---|---|---|
| Notícias e patch notes oficiais | Steam News (`ISteamNews/GetNewsForApp`, feed `steam_community_announcements`) | `src/coleta.py`, 5 por jogo, 80 jogos mais avaliados | atualizações e mudanças anunciadas pelos próprios estúdios |
| Descrição dos jogos | Steam Store API (`short_description` + `about_the_game`) | junto com os detalhes de cada jogo | o que cada jogo é e oferece |
| Achados da análise do grupo | `docs/achados_eda.txt` e `docs/achados_ml.txt` | gerados por `eda.py` e `ml.py` | ligar o agente à base estruturada |

A tabela 9.1 (documento, fonte, link, data de acesso, tema) é gerada automaticamente em `docs/tabela_documentos.csv`.

## Preparação dos textos
1. **Extrair:** o conteúdo vem em JSON das APIs.
2. **Limpar:** remover HTML, BBCode (`[img]`, `[url]`, `[list]`), links e entidades (`&quot;`). Descartar textos com menos de 30 palavras.
3. **Dividir:** chunks de 300 palavras com 50 de sobreposição, para não cortar uma ideia no meio.
4. **Registrar metadados** em cada chunk: título, fonte, link, data, tema e jogo.
5. **Organizar:** todos os chunks na tabela `documentos` do PostgreSQL, uma linha por chunk.

## Embeddings e banco vetorial
- Modelo: `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers). É gratuito, roda no computador e entende português e inglês, o que importa porque os patch notes estão em inglês e as perguntas em português.
- O título entra junto com o texto na hora de gerar o embedding, para a busca achar o jogo certo.
- Banco: PostgreSQL 16 com a extensão **pgvector**. O embedding fica numa coluna `VECTOR(384)`, com índice HNSW e distância cosseno (operador `<=>`).

## Funcionamento (RAG)
1. A pergunta vira embedding com o mesmo modelo.
2. Se a pergunta cita um jogo da base, a busca é filtrada pelos textos daquele jogo.
3. Os 5 trechos mais próximos são recuperados.
4. Os trechos vão para o LLM com a instrução de responder **só** com base neles e citar [1], [2]...
5. A resposta é mostrada com a lista de fontes (título, fonte, link).

LLM: Qwen2.5-7B rodando localmente (Ollama). O agente usa somente a base interna do projeto: nenhuma pergunta vai para a internet. Sem LLM configurado, o agente mostra só os trechos encontrados.

## Como vamos avaliar
- 5 perguntas fixas para a apresentação (em `src/agente_rag.py --teste`), misturando perguntas sobre patch notes e sobre a análise.
- Para cada uma, conferir: o trecho certo foi recuperado? A resposta só diz o que está nos trechos? As fontes estão corretas?

## Limitações previstas
- Patch notes em inglês, perguntas em português (o modelo multilíngue reduz, mas não elimina, a perda).
- Só as 5 notícias mais recentes de cada jogo: o agente não sabe de atualizações antigas.
- Planos gratuitos de LLM têm limite de uso por minuto.
