"""
Etapa 8 - Agente de dados com RAG (PostgreSQL + pgvector)

Fluxo (seção 9.4 do enunciado):
  1. a pergunta vira embedding (vetor de 384 números)
  2. o PostgreSQL/pgvector devolve os trechos mais próximos (operador <=>, distância cosseno)
  3. os trechos vão para o modelo de linguagem (LLM)
  4. a resposta volta citando as fontes [1], [2]...

Tudo roda SOMENTE dentro do projeto: os textos ficam no nosso banco e o LLM roda
no próprio computador. Nenhuma pergunta é enviada para a internet.

Modelo de linguagem (LLM) local - escolha um:
  - Ollama (recomendado): instale em ollama.com, rode `ollama pull qwen2.5:7b`
           e coloque OLLAMA=1 no .env
  - Arquivo GGUF (Linux/macOS): pip install llama-cpp-python e coloque
           LLAMA_GGUF=caminho/do/modelo.gguf no .env
Sem LLM configurado, o agente roda em "modo só busca": mostra os trechos
encontrados, sem redigir a resposta. Serve para testar a busca.

Antes de rodar: banco no ar (docker compose up -d) e python src/vetorial.py já executado.
    python src/agente_rag.py "O que mudou no último patch do Valheim?"
    python src/agente_rag.py --teste      # roda as 5 perguntas da apresentação
"""
import os
import re
import sys
import unicodedata

import requests
from dotenv import load_dotenv

load_dotenv()

INSTRUCAO = ("Você é um agente de dados sobre jogos da Steam. Responda em português, "
             "usando SOMENTE os trechos fornecidos. Explique em frases completas o que os trechos dizem "
             "(não repita só o título). Cite as fontes no formato [1], [2]. "
             "Se os trechos não tiverem a resposta, diga que não encontrou essa informação.")

PERGUNTAS_TESTE = [
    "O que mudou na atualização mais recente do Counter-Strike 2?",
    "Jogos gratuitos são mais bem avaliados que os pagos?",
    "Quais gêneros têm a melhor avaliação dos jogadores?",
    "Quais novidades o Valheim anunciou recentemente?",
    "Qual variável mais pesou no modelo que prevê se um jogo será bem avaliado?",
]

# apelidos que os jogadores usam -> nome do jogo no banco
APELIDOS = {
    "csgo": "Counter-Strike 2", "cs go": "Counter-Strike 2", "cs2": "Counter-Strike 2", "cs 2": "Counter-Strike 2",
    "counter strike global offensive": "Counter-Strike 2", "cs 1 6": "Counter-Strike", "cs 16": "Counter-Strike",
    "gta": "Grand Theft Auto V Legacy", "gta v": "Grand Theft Auto V Legacy", "gta 5": "Grand Theft Auto V Legacy",
    "r6": "Tom Clancy's Rainbow Six Siege", "rainbow six": "Tom Clancy's Rainbow Six Siege",
    "tf2": "Team Fortress 2", "cod": "Call of Duty®", "skyrim": "The Elder Scrolls V: Skyrim Special Edition",
    "witcher": "The Witcher 3: Wild Hunt — Remastered", "witcher 3": "The Witcher 3: Wild Hunt — Remastered",
    "bg3": "Baldur's Gate 3", "baldurs gate": "Baldur's Gate 3", "rdr2": "Red Dead Redemption 2",
    "red dead": "Red Dead Redemption 2", "helldivers": "HELLDIVERS™ 2", "apex": "Apex Legends™",
    "civ 6": "Sid Meier’s Civilization® VI", "civilization": "Sid Meier’s Civilization® VI",
    "ets2": "Euro Truck Simulator 2", "dbd": "Dead by Daylight", "naraka": "NARAKA: BLADEPOINT",
    "isaac": "The Binding of Isaac: Rebirth", "wukong": "Black Myth: Wukong", "sekiro": "Sekiro™: Shadows Die Twice - GOTY Edition",
    "dark souls": "DARK SOULS™ III", "bannerlord": "Mount & Blade II: Bannerlord", "hoi4": "Hearts of Iron IV",
    "ark": "ARK: Survival Evolved", "pubg": None,
}

# Tudo que é pesado (modelo de embeddings, conexão com o banco) só carrega na 1ª pergunta.
# Assim o "import agente_rag" é instantâneo e não fica pela metade se o Streamlit recarregar a página.
_modelo = None
_con = None
_jogos = []


def preparar():
    """Carrega o modelo de embeddings e conecta no banco (uma vez só)."""
    global _modelo, _con, _jogos
    if _modelo is None:
        from modelo_local import carregar_modelo     # usa modelos/minilm se existir (sem internet)
        _modelo = carregar_modelo()
    if _con is None or _con.closed:
        from banco import conectar
        _con = conectar()
        # nomes de todos os jogos que têm texto no banco (do mais longo para o mais curto)
        _jogos = [j for (j,) in _con.execute(
            "SELECT jogo FROM documentos WHERE jogo <> '' GROUP BY jogo ORDER BY length(jogo) DESC")]


def _norm(txt):
    """minúsculas, sem acento, sem ®/™ e sem pontuação: "Counter-Strike® 2" -> " counter strike 2 " """
    txt = unicodedata.normalize("NFKD", txt.lower()).encode("ascii", "ignore").decode()
    return " " + " ".join(re.findall(r"[a-z0-9]+", txt)) + " "


def achar_jogo(pergunta):
    """Se a pergunta cita um jogo da base (nome ou apelido), devolve o nome dele."""
    p = _norm(pergunta)
    for apelido, jogo in APELIDOS.items():            # 1º: apelidos (csgo, gta, r6...)
        if jogo and _norm(apelido) in p and jogo in _jogos:
            return jogo
    for j in _jogos:                                   # 2º: nome completo ("Counter-Strike 2")
        if _norm(j) in p:
            return j
    for j in _jogos:                                   # 3º: nome antes dos dois-pontos ("Sea of Thieves")
        curto = _norm(j.split(":")[0])
        if len(curto.strip()) >= 4 and curto in p:
            return j
    return None


def _palavras(txt):
    """Palavras com 4+ letras, sem acento e em minúsculas (para comparar pergunta e texto)."""
    txt = unicodedata.normalize("NFKD", txt.lower()).encode("ascii", "ignore").decode()
    # sem o "s" final e cortado em 6 letras: junta variações (caro/caros, jogado/jogados, variavel/variaveis)
    return {(w[:-1] if w.endswith("s") else w)[:6] for w in re.findall(r"[a-z0-9]{4,}", txt)} - _COMUNS


_COMUNS = {"qual", "quai", "mais", "jogo", "jogos", "sera", "como", "para", "pelo", "pela", "este", "esta", "isso", "sobre", "tem"}


SQL_BUSCA = """
    SELECT titulo, fonte, link, data, tema, jogo, texto,
           embedding <=> %(emb)s AS distancia          -- <=> = distância cosseno (0 = idêntico)
    FROM documentos
    WHERE (%(jogo)s::text IS NULL AND tema <> 'Ficha do jogo')   -- pergunta geral: sem as 961 fichas
       OR jogo = %(jogo)s                                       -- pergunta sobre um jogo: só os textos dele
    ORDER BY distancia
    LIMIT %(n)s
"""


# pergunta de ranking ("o mais jogado", "o melhor", "o mais caro"...): prioriza os textos "Ranking: ..."
_RANKING = re.compile(r" (mais|menos|melhor|melhores|pior|piores|maior|maiores|menor|top|barat\w*|car[oa]s?|popular\w*|"
                      r"ranking|recentes?|antigos?|promoc\w*|desconto\w*) ")
# gêneros como aparecem nos títulos dos rankings ("Ranking: melhores jogos de Estratégia") e como a pessoa escreve
_GENEROS = {"acao": "acao", "action": "acao", "tiro": "acao", "aventura": "aventura", "adventure": "aventura", "indie": "indie",
            "rpg": "rpg", "simulacao": "simulacao", "simulador": "simulacao", "simulation": "simulacao", "estrategia": "estrategia",
            "strategy": "estrategia", "free to play": "gratuitos", "casual": "casual", "mmo": "mmo", "multijogador massivo": "mmo",
            "esporte": "esportes", "esportes": "esportes", "futebol": "esportes", "sports": "esportes", "corrida": "corrida",
            "racing": "corrida", "acesso antecipado": "acesso antecipado", "early access": "acesso antecipado"}
_RANK_GENERO = re.compile(r"ranking: (?:jogos de (.+?) mais jogados|melhores jogos de (.+))$", re.I)


def _genero_da_pergunta(pergunta):
    p = _norm(pergunta)
    return next((g for chave, g in _GENEROS.items() if f" {chave} " in p), None)


def _linha(r):
    titulo, fonte, link, data, tema, jg, texto, dist = r
    return {"texto": texto, "titulo": titulo, "fonte": fonte, "link": link, "data": data, "tema": tema,
            "jogo": jg, "distancia": round(dist, 3), "score": 0.0}


def buscar(pergunta, k=5):
    """Busca híbrida: 1) semântica no pgvector pega 4k candidatos;
    2) reordena somando bônus para palavras da pergunta que aparecem no título/texto."""
    preparar()
    emb = _modelo.encode(pergunta)                # numpy array com 384 números
    jogo = achar_jogo(pergunta)                    # pergunta sobre um jogo: busca só nos textos dele
    cand = [_linha(r) for r in _con.execute(SQL_BUSCA, {"emb": emb, "jogo": jogo, "n": k * 4}).fetchall()]
    qp = _palavras(pergunta)
    genero = _genero_da_pergunta(pergunta)
    ranking = not jogo and _RANKING.search(_norm(pergunta)) and not (" genero" in _norm(pergunta) and not genero)
    if ranking:   # os rankings são poucos (~40): garante que todos concorram, mesmo fora dos 4k vizinhos
        vistos = {c["titulo"] for c in cand}
        cand += [_linha(r) for r in _con.execute(
            "SELECT titulo, fonte, link, data, tema, jogo, texto, embedding <=> %(emb)s FROM documentos "
            "WHERE tema = 'Ranking da base'", {"emb": emb}).fetchall() if r[0] not in vistos]
    for c in cand:
        comum = len(qp & _palavras(c["titulo"] + " " + c["texto"])) / max(len(qp), 1)
        no_titulo = len(qp & _palavras(c["titulo"])) / max(len(qp), 1)     # o título resume o assunto do texto
        c["score"] = (1 - c["distancia"]) + 0.3 * comum + 0.2 * no_titulo
        if c["tema"] == "Ranking da base":
            m = _RANK_GENERO.search(c["titulo"])
            g = m and _norm(m.group(1) or m.group(2)).split()[0]
            if g:                      # ranking de um gênero: só sobe se a pergunta falar desse gênero
                c["score"] += 0.3 if genero and g == genero.split()[0] else -0.3
            elif ranking:
                c["score"] += 0.2
        c["score"] = round(c["score"], 3)
    # pergunta sobre "última atualização / novidades": dá um bônus para as notícias mais novas
    if jogo and re.search(r"ultim|recent|novidad|atualiz|patch|update|mudou", _norm(pergunta)):
        noticia = lambda c: c["tema"].startswith("Notícia")      # só notícias (fichas/descrições têm a data da coleta)
        datas = sorted({c["data"] for c in cand if c["data"] and noticia(c)}, reverse=True)
        for c in cand:
            if noticia(c) and c["data"] in datas:
                c["score"] = round(c["score"] + 0.2 * (1 - datas.index(c["data"]) / max(len(datas), 1)), 3)
    top = sorted(cand, key=lambda c: c["score"], reverse=True)[:k]
    # pergunta sobre um jogo: a ficha com os números dele (preço, jogadores, nota...) sempre vai junto
    if jogo and not any(c["tema"] == "Ficha do jogo" for c in top):
        ficha = [c for c in cand if c["tema"] == "Ficha do jogo"]
        if not ficha:
            r = _con.execute("SELECT titulo, fonte, link, data, tema, jogo, texto, embedding <=> %(emb)s FROM documentos "
                             "WHERE tema = 'Ficha do jogo' AND jogo = %(jogo)s", {"emb": emb, "jogo": jogo}).fetchone()
            ficha = [_linha(r)] if r else []
        if ficha:
            top = top[:k - 1] + ficha[:1]
    return top


def montar_prompt(pergunta, trechos):
    ctx = "\n\n".join(f"[{i}] {t['titulo']} ({t['fonte']}, {t['data']})\n{t['texto'][:800]}"
                      for i, t in enumerate(trechos, 1))
    extra = ""
    jogo = achar_jogo(pergunta)
    if jogo:
        # troca o apelido pelo nome oficial na pergunta ("csgo" -> "Counter-Strike 2"), senão o modelo acha
        # que os trechos são de outro jogo e responde que não encontrou
        for apelido, nome in sorted(APELIDOS.items(), key=lambda x: -len(x[0])):   # "gta 5" antes de "gta"
            if nome == jogo:
                padrao = r"(?<![a-z0-9])" + r"[\W_]*".join(map(re.escape, apelido.split())) + r"(?![a-z0-9])"
                pergunta = re.sub(padrao, jogo, pergunta, flags=re.I)
        extra = "\n(Se a pergunta for sobre a atualização mais recente, use o trecho com a data mais nova.)"
    return f"Trechos:\n{ctx}\n\nPergunta: {pergunta}{extra}"


def _mensagens(prompt):
    return [{"role": "system", "content": INSTRUCAO}, {"role": "user", "content": prompt}]


def _ollama(prompt, stream):
    """Chama o Ollama local. keep_alive deixa o modelo na memória por 30 min (a 2ª pergunta é bem mais rápida)."""
    try:
        r = requests.post("http://localhost:11434/api/chat", timeout=600, stream=stream,
                          json={"model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), "stream": stream, "keep_alive": "30m",
                                "messages": _mensagens(prompt),
                                "options": {"temperature": 0.2, "num_predict": 350, "num_ctx": 4096}})
        r.raise_for_status()
    except requests.ConnectionError:
        raise RuntimeError("O Ollama não está rodando. Abra o aplicativo Ollama (ou rode `ollama serve`) e tente de novo.")
    except requests.HTTPError:
        raise RuntimeError(f"O Ollama respondeu com erro. Confira se o modelo foi baixado: `ollama pull {os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')}`")
    return r


def chamar_llm(prompt):
    if os.getenv("OLLAMA"):
        return _ollama(prompt, False).json()["message"]["content"]
    if os.getenv("LLAMA_GGUF"):
        r = _gguf().create_chat_completion(messages=_mensagens(prompt), max_tokens=350, temperature=0.2)
        return r["choices"][0]["message"]["content"]
    return None   # sem LLM configurado


def chamar_llm_stream(prompt):
    """Igual ao chamar_llm, mas devolve o texto aos pedaços (o painel mostra enquanto o modelo escreve)."""
    import json
    if os.getenv("OLLAMA"):
        for linha in _ollama(prompt, True).iter_lines():
            if linha:
                yield json.loads(linha).get("message", {}).get("content", "")
    elif os.getenv("LLAMA_GGUF"):
        for ch in _gguf().create_chat_completion(messages=_mensagens(prompt), max_tokens=350, temperature=0.2, stream=True):
            yield ch["choices"][0]["delta"].get("content", "")


_llama = None


def _gguf():
    global _llama
    if _llama is None:
        from llama_cpp import Llama
        _llama = Llama(model_path=os.environ["LLAMA_GGUF"], n_ctx=4096, n_threads=os.cpu_count(), verbose=False)
    return _llama


def tem_llm():
    return bool(os.getenv("OLLAMA") or os.getenv("LLAMA_GGUF"))


def modo_busca(trechos):
    """Modo só busca (o padrão do projeto): devolve os trechos encontrados no pgvector, sem LLM."""
    return "Trechos mais parecidos com a pergunta, encontrados no banco vetorial:\n\n" + "\n\n".join(
        f"[{i}] {t['titulo']} ({t['fonte']}, {t['data']}) - similaridade {1 - t['distancia']:.2f}\n{t['texto'][:400]}..."
        for i, t in enumerate(trechos, 1))


def fontes_de(trechos):
    return [f"[{i}] {t['titulo']} - {t['fonte']} - {t['link']}" for i, t in enumerate(trechos, 1)]


def responder(pergunta, k=5):
    trechos = buscar(pergunta, k)
    resposta = chamar_llm(montar_prompt(pergunta, trechos))
    if resposta is None:
        resposta = modo_busca(trechos)
    return resposta, fontes_de(trechos), trechos


if __name__ == "__main__":
    perguntas = PERGUNTAS_TESTE if "--teste" in sys.argv else [" ".join(sys.argv[1:]) or PERGUNTAS_TESTE[0]]
    for p in perguntas:
        resp, fontes, _ = responder(p)
        print("=" * 80, "\nPERGUNTA:", p, "\n\nRESPOSTA:\n", resp, "\n\nFONTES:\n" + "\n".join(fontes), "\n")
