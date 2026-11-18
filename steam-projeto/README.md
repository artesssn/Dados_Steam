# O que faz um jogo dar certo na Steam?
Projeto Final de Ciência de Dados: coleta, tratamento, análise, Machine Learning, painel e agente RAG com dados públicos da Steam.

## Como rodar do zero (Windows, macOS ou Linux)
Precisa de Python 3.10 ou mais novo e do [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para o banco vetorial).
```bash
# 1. ambiente e bibliotecas (uma vez só)
python -m venv .venv
# Windows:  .venv\Scripts\activate      macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
docker compose up -d            # PostgreSQL + pgvector (deixe o Docker Desktop aberto)

# 2. pipeline, nesta ordem (sempre a partir desta pasta)
python src/coleta.py            # ~30 min; use --teste para só 20 jogos. Pode parar e rodar de novo.
python src/tratamento.py        # base final em data/processed/steam_tratada.csv
python src/dicionario.py        # docs/dicionario_dados.md
python src/eda.py               # gráficos em figuras/ e números em docs/resultados_eda.md
python src/ml.py                # modelos em docs/resultados_ml.md
python src/vetorial.py          # embeddings -> tabela documentos no pgvector (baixa o modelo na 1ª vez)
python src/agente_rag.py --teste    # as 5 perguntas da apresentação

# 3. painel + agente no navegador
streamlit run app/painel.py
```
O agente roda **somente dentro do projeto**: os textos ficam no nosso PostgreSQL e o LLM roda no próprio computador, sem API externa. Para ele redigir as respostas:
- **Ollama (recomendado):** instale em https://ollama.com, rode `ollama pull qwen2.5:7b` e tire o `#` de `OLLAMA=1` no `.env`.
- **Arquivo GGUF (Linux/macOS):** `pip install llama-cpp-python` e `LLAMA_GGUF=caminho/do/modelo.gguf` no `.env`.

**Sem Docker?** Instale o PostgreSQL 16 e a extensão pgvector (https://github.com/pgvector/pgvector#installation), crie o banco `steam` e ajuste `DATABASE_URL` no `.env`.

Para ver os dados no banco: `docker exec -it steam-pgvector psql -U steam -c "SELECT titulo, jogo FROM documentos LIMIT 5;"`

Sem LLM, o agente funciona em modo busca (mostra os trechos encontrados). Teste com `python src/agente_rag.py --teste`.

## Estrutura
| Pasta / arquivo | Etapa | Conteúdo |
|---|---|---|
| `docs/00_organizacao_do_grupo.md` | 1 | papéis, GitHub, chave da API, datas |
| `docs/01_primeira_entrega.md` | 2 | texto da 1ª entrega |
| `src/coleta.py` | 3 | coleta (SteamSpy, Store API, notícias) |
| `src/tratamento.py`, `src/dicionario.py` | 4 | limpeza, variáveis derivadas, dicionário |
| `docs/02_plano_do_agente.md` | 4 | plano do agente (2ª entrega) |
| `src/eda.py` | 5 | estatística, testes, gráficos |
| `src/ml.py` | 6 | classificação e clusterização |
| `app/painel.py` | 7 | painel Streamlit (+ aba do agente) |
| `src/banco.py`, `src/vetorial.py`, `src/agente_rag.py`, `docker-compose.yml` | 8 | banco vetorial (PostgreSQL + pgvector) e agente RAG |
| `docs/09_etica_e_referencias.md` | 9 | ética e referências |
| `docs/relatorio_final.md` | 10 | relatório completo (14 itens) |
| `docs/11_apresentacao.md` | 11 | roteiro e falas da apresentação |
| `data/raw/`, `data/processed/` | - | dados brutos e base tratada |
| `figuras/` | - | gráficos usados no relatório |

## Observação
Os números do relatório são da coleta feita em 03/11/2026. Rodar a coleta de novo traz dados atualizados e os números mudam um pouco; rode `eda.py` e `ml.py` de novo e atualize o relatório.
