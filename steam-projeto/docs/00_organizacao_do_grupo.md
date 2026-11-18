# Etapa 1 - Organização do grupo

## Divisão de funções (troque [Integrante N] pelos nomes)
| Papel | Responsável | O que faz | Arquivos |
|---|---|---|---|
| Dados / coleta | [Integrante 1] | Roda e mantém a coleta da Steam, cuida dos limites da API | src/coleta.py |
| Tratamento e dicionário | [Integrante 2] | Limpeza, variáveis derivadas, dicionário de dados | src/tratamento.py, src/dicionario.py |
| Estatística e ML | [Integrante 3] | Análise exploratória, testes, modelos | src/eda.py, src/ml.py |
| Painel | [Integrante 4] | Streamlit, filtros, gráficos, prints para o relatório | app/painel.py |
| Agente RAG | [Integrante 5] | Textos, embeddings, ChromaDB, agente, 5 perguntas | src/vetorial.py, src/agente_rag.py |
| Relatório e apresentação | todos (um revisor final) | Cada um escreve a parte do relatório da sua função | docs/relatorio_final.md |

Se o grupo tiver menos gente, junte: Dados+Tratamento, Estatística+ML, Painel+Agente.

## Repositório no GitHub (passo a passo)
1. Um integrante cria o repositório `steam-ciencia-de-dados` em github.com (Public ou Private) e adiciona os outros em Settings → Collaborators.
2. No computador, dentro desta pasta:
```bash
git init
git add .
git commit -m "Estrutura inicial do projeto"
git branch -M main
git remote add origin https://github.com/USUARIO/steam-ciencia-de-dados.git
git push -u origin main
```
3. Regra do grupo: cada um trabalha no seu arquivo, faz `git pull` antes de começar e `git push` ao terminar.
4. O `.gitignore` já impede que o `.env` (chaves) vá para o GitHub.

Pasta compartilhada (Google Drive/OneDrive): enunciado, prints do painel, slides e versões do relatório.

## Steam Web API key
1. Entre em https://steamcommunity.com/dev/apikey logado na Steam (a conta precisa ter gasto pelo menos US$ 5 na loja).
2. Em "Domain Name" escreva `localhost`, aceite os termos e clique em Register.
3. Copie `.env.example` para `.env` e cole a chave em `STEAM_API_KEY=`.

Importante: os endpoints que o projeto usa (Store API, SteamSpy e GetNewsForApp) não exigem chave. Vale ter a chave para citar no relatório e caso o grupo queira usar outro endpoint da Web API.

## Datas internas (preencha quando o professor passar as oficiais)
| Marco | Data interna (grupo) | Data oficial |
|---|---|---|
| Texto da 1ª entrega revisado | 3 dias antes | [ ] |
| Base tratada + dicionário + EDA inicial | 1 semana antes da 2ª | [ ] |
| ML, painel e agente funcionando | 2 semanas antes da final | [ ] |
| Relatório completo para revisão | 1 semana antes da final | [ ] |
| Ensaio da apresentação | 2 dias antes | [ ] |
