# Dicionário de dados - steam_tratada.csv

961 linhas (jogos) e 35 colunas. Coleta feita em 03/11/2026.

| Coluna | Tipo | Descrição | Exemplo | Nulos | Origem |
|---|---|---|---|---|---|
| appid | int64 | Identificador único do jogo na Steam | 730 | 0% | Store API |
| nome | str | Nome do jogo na loja | Counter-Strike 2 | 0% | Store API |
| gratuito | bool | True se o jogo é gratuito (free to play) | True | 0% | Store API |
| preco_brl | float64 | Preço atual em reais, já com desconto (0 = grátis; vazio = pago sem venda no Brasil) | 0.0 | 9% | Store API (cc=br) |
| preco_original_brl | float64 | Preço sem desconto, em reais | 0.0 | 9% | Store API |
| desconto_pct | int64 | Desconto aplicado no dia da coleta (%) | 0 | 0% | Store API |
| data_lancamento | str | Data de lançamento | 2012-08-21 | 0% | Store API |
| windows | bool | Roda no Windows | True | 0% | Store API |
| mac | bool | Roda no macOS | False | 0% | Store API |
| linux | bool | Roda no Linux / Steam Deck nativo | True | 0% | Store API |
| metacritic | float64 | Nota da crítica no Metacritic (0-100); vazio quando não há | 96.0 | 43% | Store API |
| recomendacoes | float64 | Total de recomendações exibido pela loja | 5337934.0 | 7% | Store API |
| generos | str | Gêneros, separados por vírgula | Action, Free To Play | 0% | Store API |
| categorias | str | Categorias (Single-player, Multi-player, Co-op...), separadas por vírgula | Multi-player, Cross-Platform Multiplayer | 0% | Store API |
| desenvolvedora | str | Desenvolvedora(s) | Valve | 0% | Store API |
| publicadora | str | Publicadora(s) | Valve | 0% | Store API |
| n_idiomas | int64 | Quantidade de idiomas suportados | 29 | 0% | derivada (Store API) |
| idade_minima | int64 | Idade mínima indicada pela loja (0 = livre) | 0 | 0% | Store API |
| n_conquistas | int64 | Quantidade de conquistas (achievements) | 1 | 0% | Store API |
| n_dlcs | int64 | Quantidade de DLCs à venda | 1 | 0% | Store API |
| positive | float64 | Avaliações positivas de usuários | 7642084.0 | 0% | SteamSpy |
| negative | float64 | Avaliações negativas de usuários | 1173003.0 | 0% | SteamSpy |
| jogadores_simultaneos | float64 | Pico de jogadores simultâneos no dia anterior à coleta | 1013936.0 | 0% | SteamSpy (ccu) |
| ano_lancamento | int64 | Ano extraído da data de lançamento | 2012 | 0% | derivada |
| idade_anos | float64 | Anos desde o lançamento até a data da coleta | 14.20123203285421 | 0% | derivada |
| total_avaliacoes | float64 | positive + negative | 8815087.0 | 0% | derivada |
| prop_positiva | float64 | positive / total_avaliacoes (0 a 1) | 0.8669323399757711 | 0% | derivada |
| donos_min | float64 | Limite inferior da faixa de donos estimada | 100000000.0 | 0% | derivada (SteamSpy owners) |
| donos_medio | float64 | Ponto médio da faixa de donos estimada | 150000000.0 | 0% | derivada (SteamSpy owners) |
| n_generos | int64 | Quantidade de gêneros do jogo | 2 | 0% | derivada |
| multiplayer | bool | Tem modo multijogador/online | True | 0% | derivada (categorias) |
| early_access | bool | Está ou esteve em Acesso Antecipado | False | 0% | derivada (gêneros) |
| faixa_preco | str | Grátis, Até R$30, R$30-80, R$80-150, Acima de R$150 | Grátis | 9% | derivada |
| classificacao | str | Negativa (<40%), Mista (40-70%), Positiva (70-80%), Muito positiva (80-95%), Extremamente positiva (95%+) | Muito positiva | 0% | derivada |
| sem_preco_br | bool | True para jogo pago sem preço na loja brasileira (fora de venda); nesses o preço fica vazio | False | 0% | derivada |
