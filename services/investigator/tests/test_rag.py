import json

import httpx
from qdrant_client import QdrantClient

from fraudguard_investigator.rag import index_policy, search_policy, split_policy

POLICY = """# Title

## R1 Card testing
Many small payments.

## R2 Foreign ATM cash-out
Large withdrawal abroad.
"""


def test_split_policy_gives_one_chunk_per_rule():
    chunks = split_policy(POLICY)
    assert len(chunks) == 2
    assert chunks[0].startswith("## R1 Card testing")
    assert "# Title" not in chunks[0]


def fake_ollama() -> httpx.Client:
    """Pretend embedding model: 'card' texts -> [1, 0], everything else -> [0, 1]."""

    def handler(request: httpx.Request) -> httpx.Response:
        inputs = json.loads(request.content)["input"]
        vectors = [[1.0, 0.0] if "card" in t.lower() else [0.0, 1.0] for t in inputs]
        return httpx.Response(200, json={"embeddings": vectors})

    return httpx.Client(base_url="http://ollama", transport=httpx.MockTransport(handler))


def test_search_returns_the_most_similar_rule():
    qdrant, ollama = QdrantClient(":memory:"), fake_ollama()
    assert index_policy(qdrant, ollama, POLICY) == 2
    best = search_policy(qdrant, ollama, "suspicious card payments", k=1)[0]
    assert best.startswith("## R1 Card testing")  # which rule talks about cards?
