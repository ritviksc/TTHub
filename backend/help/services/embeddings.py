"""Turn text into vectors with the provider's embedding model (bge-m3 by default)."""
import math
from array import array

from django.conf import settings

from llm.services.client import get_client

BATCH_SIZE = 32


def normalise(vector):
    """Scale to length 1, so cosine similarity is a plain dot product."""
    length = math.sqrt(sum(value * value for value in vector))
    if not length:
        raise ValueError("Embedding model returned an all-zero vector.")
    return [value / length for value in vector]


def embed(texts, model=None):
    model = model or settings.HELP_EMBED_MODEL
    client = get_client()
    vectors = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start:start + BATCH_SIZE]
        response = client.embeddings.create(model=model, input=batch)
        # The API may return items out of order; `index` is their input position.
        rows = sorted(response.data, key=lambda item: item.index)
        if len(rows) != len(batch):
            raise ValueError("Embedding model returned the wrong number of vectors.")
        vectors.extend(normalise(row.embedding) for row in rows)
    return vectors


def to_bytes(vector):
    return array("f", vector).tobytes()


def from_bytes(data):
    vector = array("f")
    vector.frombytes(bytes(data))
    return vector
