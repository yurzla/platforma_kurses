import requests
from app.core.config import OLLAMA_URL, EMBEDDING_MODEL, EMBEDDING_DIMENSION


def get_embedding(text: str) -> list[float]:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": EMBEDDING_MODEL,
            "input": text,
        },
        timeout=120,
    )

    response.raise_for_status()
    embedding = response.json()["embeddings"][0]

    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError(f"Ожидалась размерность {EMBEDDING_DIMENSION}, получено {len(embedding)}")

    return embedding