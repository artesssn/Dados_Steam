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
from sentence_transformers import SentenceTransformer

from banco import conectar

load_dotenv()
_modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
_con = conectar()

INSTRUCAO = ("Você é um agente de dados sobre jogos da Steam. Responda em português, "
             "usando SOMENTE os trechos fornecidos. Cite as fontes no formato [1], [2]. "
             "Se os trechos não tiverem a resposta, diga que não encontrou essa informação.")

PERGUNTAS_TESTE = [
    "O que mudou na atualização mais recente do Counter-Strike 2?",
    "Jogos gratuitos são mais bem avaliados que os pagos?",
    "Quais gêneros têm a melhor avaliação dos jogadores?",
    "Quais novidades o Valheim anunciou recentemente?",
    "Qual variável mais pesou no modelo que prevê se um jogo será bem avaliado?",
]


# nomes de todos os jogos que têm texto no banco (do mais longo para o mais curto)
_jogos = [j for (j,) in _con.execute("SELECT jogo FROM documentos WHERE jogo <> '' GROUP BY jogo ORDER BY length(jogo) DESC")]


def achar_jogo(pergunta):
    """Se a pergunta cita um jogo da base, devolve o nome dele (o mais longo que bater)."""
    p = pergunta.lower()
    limpo = lambda s: s.lower().replace("®", "").replace("™", "").strip()
    for j in _jogos:                       # 1ª tentativa: nome completo ("Counter-Strike 2")
        if limpo(j) in p:
            return j
    for j in _jogos:                       # 2ª tentativa: nome antes dos dois-pontos
        curto = limpo(j).split(":")[0].strip()
        if len(curto) >= 4 and curto in p:
            return j
    return None


def _palavras(txt):
    """Palavras com 4+ letras, sem acento e em minúsculas (para comparar pergunta e texto)."""
    txt = unicodedata.normalize("NFKD", txt.lower()).encode("ascii", "ignore").decode()
    return {w[:6] for w in re.findall(r"[a-z0-9]{4,}", txt)} - _COMUNS   # [:6] junta variações: variavel/variaveis


_COMUNS = {"qual", "quai", "mais", "jogo", "jogos", "sera", "como", "para", "pelo", "pela", "este", "esta", "isso", "sobre", "tem"}


SQL_BUSCA = """
    SELECT titulo, fonte, link, data, tema, jogo, texto,
           embedding <=> %(emb)s AS distancia          -- <=> = distância cosseno (0 = idêntico)
    FROM documentos
    WHERE %(jogo)s::text IS NULL OR jogo = %(jogo)s     -- filtro opcional por jogo
    ORDER BY distancia
    LIMIT %(n)s
"""


def buscar(pergunta, k=5):
    """Busca híbrida: 1) semântica no pgvector pega 4k candidatos;
    2) reordena somando um bônus para palavras da pergunta que aparecem no título/texto."""
    emb = _modelo.encode(pergunta)                # numpy array com 384 números
    jogo = achar_jogo(pergunta)                    # pergunta sobre um jogo: busca só nos textos dele
    linhas = _con.execute(SQL_BUSCA, {"emb": emb, "jogo": jogo, "n": k * 4}).fetchall()
    qp = _palavras(pergunta)
    cand = []
    for titulo, fonte, link, data, tema, jg, texto, dist in linhas:
        comum = len(qp & _palavras(titulo + " " + texto)) / max(len(qp), 1)
        cand.append({"texto": texto, "titulo": titulo, "fonte": fonte, "link": link, "data": data, "tema": tema,
                     "jogo": jg, "distancia": round(dist, 3), "score": round((1 - dist) + 0.3 * comum, 3)})
    return sorted(cand, key=lambda c: c["score"], reverse=True)[:k]


def montar_prompt(pergunta, trechos):
    ctx = "\n\n".join(f"[{i}] {t['titulo']} ({t['fonte']}, {t['data']})\n{t['texto'][:1500]}"
                      for i, t in enumerate(trechos, 1))
    return f"Trechos:\n{ctx}\n\nPergunta: {pergunta}"


def chamar_llm(prompt):
    if os.getenv("OLLAMA"):
        r = requests.post("http://localhost:11434/api/chat", timeout=180,
                          json={"model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), "stream": False,
                                "messages": [{"role": "system", "content": INSTRUCAO},
                                             {"role": "user", "content": prompt}]})
        r.raise_for_status()
        return r.json()["message"]["content"]
    if os.getenv("LLAMA_GGUF"):
        global _llama
        if _llama is None:
            from llama_cpp import Llama
            _llama = Llama(model_path=os.environ["LLAMA_GGUF"], n_ctx=4096, n_threads=os.cpu_count(), verbose=False)
        r = _llama.create_chat_completion(messages=[{"role": "system", "content": INSTRUCAO},
                                                    {"role": "user", "content": prompt}], max_tokens=350, temperature=0.2)
        return r["choices"][0]["message"]["content"]
    return None   # sem LLM configurado


_llama = None


def responder(pergunta, k=5):
    trechos = buscar(pergunta, k)
    resposta = chamar_llm(montar_prompt(pergunta, trechos))
    if resposta is None:
        resposta = ("(Modo só busca: configure OLLAMA=1 ou LLAMA_GGUF no .env "
                    "para o agente redigir a resposta.) Trechos mais relevantes:\n" +
                    "\n".join(f"[{i}] {t['titulo']}: {t['texto'][:250]}..." for i, t in enumerate(trechos, 1)))
    fontes = [f"[{i}] {t['titulo']} - {t['fonte']} - {t['link']}" for i, t in enumerate(trechos, 1)]
    return resposta, fontes, trechos


if __name__ == "__main__":
    perguntas = PERGUNTAS_TESTE if "--teste" in sys.argv else [" ".join(sys.argv[1:]) or PERGUNTAS_TESTE[0]]
    for p in perguntas:
        resp, fontes, _ = responder(p)
        print("=" * 80, "\nPERGUNTA:", p, "\n\nRESPOSTA:\n", resp, "\n\nFONTES:\n" + "\n".join(fontes), "\n")
