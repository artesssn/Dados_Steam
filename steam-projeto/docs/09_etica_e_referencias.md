# Considerações éticas

- **Somente dados públicos.** Todas as informações vêm de páginas e APIs abertas da Steam e do SteamSpy. Não houve login, raspagem de áreas restritas nem pesquisa com pessoas, então não é necessário submeter ao Comitê de Ética.
- **Sem dados pessoais.** A base é sobre jogos, não sobre pessoas. Avaliações de usuários foram usadas apenas como contagens agregadas (positivas e negativas). Nenhum nome, ID de usuário ou texto de avaliação individual foi coletado.
- **Textos do agente** são comunicados oficiais publicados pelos próprios estúdios e descrições da loja. O agente sempre mostra a fonte e o link, para que a informação possa ser conferida.
- **Respeito aos termos e limites das APIs.** A coleta usa pausas entre requisições (1,6 s na Store API, 61 s no SteamSpy) e identifica o projeto como acadêmico.
- **Limites de interpretação.** Os resultados mostram associação, não causa: um gênero bem avaliado não garante que um novo jogo desse gênero será bem avaliado. A amostra é dos jogos mais populares, então não representa jogos pequenos. As faixas de donos do SteamSpy são estimativas.
- **Uso de IA.** O agente usa um modelo de linguagem, que pode errar. Por isso ele é instruído a responder só com os trechos recuperados e a dizer quando não encontrar a informação.

# Referências

- VALVE CORPORATION. *Steam Web API Documentation*. Disponível em: https://partner.steamgames.com/doc/webapi_overview. Acesso em: [data].
- VALVE CORPORATION. *Steam Store API - appdetails*. Disponível em: https://store.steampowered.com/api/appdetails. Acesso em: [data].
- VALVE CORPORATION. *ISteamNews/GetNewsForApp*. Disponível em: https://partner.steamgames.com/doc/webapi/ISteamNews. Acesso em: [data].
- STEAMSPY. *SteamSpy API*. Disponível em: https://steamspy.com/api.php. Acesso em: [data].
- PEDREGOSA, F. et al. Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, v. 12, p. 2825-2830, 2011.
- REIMERS, N.; GUREVYCH, I. Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. In: *EMNLP*, 2019.
- LEWIS, P. et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. In: *NeurIPS*, 2020.
- CHROMA. *Chroma documentation*. Disponível em: https://docs.trychroma.com. Acesso em: [data].
- STREAMLIT. *Streamlit documentation*. Disponível em: https://docs.streamlit.io. Acesso em: [data].
- MCKINNEY, W. Data Structures for Statistical Computing in Python. In: *Proceedings of the 9th Python in Science Conference*, 2010.
