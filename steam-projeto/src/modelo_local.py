"""
Carrega o modelo de embeddings da pasta do projeto (modelos/minilm), sem baixar nada.

O arquivo principal do modelo (model.safetensors, 470 MB) foi dividido em partes de 24 MB
(model.safetensors.parte00, parte01...) porque o GitHub não aceita arquivos grandes.
Na primeira vez, esta função junta as partes sozinha. Se a pasta não existir,
baixa o modelo da internet, como antes.
"""
import hashlib
from pathlib import Path

from sentence_transformers import SentenceTransformer

NOME = "paraphrase-multilingual-MiniLM-L12-v2"
PASTA = Path(__file__).resolve().parent.parent / "modelos" / "minilm"


def _juntar_partes():
    alvo = PASTA / "model.safetensors"
    partes = sorted(PASTA.glob("model.safetensors.parte*"))
    if alvo.exists() or not partes:
        return
    print(f"Juntando {len(partes)} partes do modelo (só na primeira vez)...")
    tmp = alvo.with_suffix(".tmp")
    with open(tmp, "wb") as saida:
        for p in partes:
            saida.write(p.read_bytes())
    esperado = PASTA / "model.safetensors.sha256"
    if esperado.exists():
        h = hashlib.sha256(tmp.read_bytes()).hexdigest()
        if h != esperado.read_text().strip():
            tmp.unlink()
            raise RuntimeError("As partes do modelo estão incompletas ou corrompidas. Baixe a pasta modelos/minilm de novo.")
    tmp.rename(alvo)


def carregar_modelo():
    if (PASTA / "config.json").exists():
        _juntar_partes()
        return SentenceTransformer(str(PASTA))
    return SentenceTransformer(NOME)          # sem a pasta: baixa da internet (~470 MB, só na 1ª vez)
