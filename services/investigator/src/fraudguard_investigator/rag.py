import re

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

COLLECTION = "aml_policy"
EMBED_MODEL = "nomic-embed-text"


def split_policy(text: str) -> list[str]:
    """Split the policy into one chunk per '## ' section (the title stays in the chunk)."""
    sections = re.split(r"\n(?=## )", text)  # split before every line starting with "## "
    return [s.strip() for s in sections if s.startswith("## ")]  # keep only the rule sections


def embed(ollama: httpx.Client, texts: list[str]) -> list[list[float]]:
    """Turn texts into vectors with the local Ollama embedding model."""
    response = ollama.post("/api/embed", json={"model": EMBED_MODEL, "input": texts})
    response.raise_for_status()
    return response.json()["embeddings"]


def index_policy(qdrant: QdrantClient, ollama: httpx.Client, text: str) -> int:
    """(Re)build the collection from the policy text. Returns the number of chunks stored."""
    chunks = split_policy(text)
    vectors = embed(ollama, chunks)
    if qdrant.collection_exists(COLLECTION):
        qdrant.delete_collection(COLLECTION)
    qdrant.create_collection(
        COLLECTION, vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE)
    )
    qdrant.upsert(
        COLLECTION,
        [
            PointStruct(id=i, vector=v, payload={"text": c})
            for i, (c, v) in enumerate(zip(chunks, vectors, strict=True))
        ],
    )
    return len(chunks)


def search_policy(
    qdrant: QdrantClient, ollama: httpx.Client, question: str, k: int = 2
) -> list[str]:
    """Return the k policy chunks most similar in meaning to the question."""
    hits = qdrant.query_points(COLLECTION, query=embed(ollama, [question])[0], limit=k).points
    return [h.payload["text"] for h in hits]
