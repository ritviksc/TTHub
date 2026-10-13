"""Find the help chunks closest in meaning to a question, for one role only."""
from dataclasses import dataclass
from threading import Lock

from django.conf import settings
from django.db.models import Count, Max

from ..models import HelpChunk
from .embeddings import embed, from_bytes

TOP_K = 5


@dataclass(frozen=True)
class Indexed:
    slug: str
    title: str
    heading: str
    text: str
    roles: tuple
    vector: object


@dataclass(frozen=True)
class Match:
    slug: str
    title: str
    heading: str
    text: str
    score: float


_lock = Lock()
_cache = {"version": None, "rows": []}


def _index():
    """Every stored chunk with its vector, held in memory until the index is rebuilt.

    A few hundred 1024-float vectors is about a megabyte, so a plain list is
    enough; numpy, FAISS or a vector database would only add dependencies.
    """
    model = settings.HELP_EMBED_MODEL
    stats = HelpChunk.objects.filter(model=model).aggregate(latest=Max("created_at"), count=Count("id"))
    version = (model, stats["latest"], stats["count"])
    with _lock:
        if _cache["version"] != version:
            _cache["rows"] = [
                Indexed(row.slug, row.title, row.heading, row.text, tuple(row.roles), from_bytes(row.embedding))
                for row in HelpChunk.objects.filter(model=model)
            ]
            _cache["version"] = version
        return _cache["rows"]


def clear_cache():
    with _lock:
        _cache["version"] = None
        _cache["rows"] = []


def retrieve(role, question, k=TOP_K, min_score=None):
    """Up to k chunks this role may see, best first, each at least min_score similar."""
    min_score = settings.HELP_MIN_SCORE if min_score is None else min_score
    # Filter by role before scoring, so other roles' content is never a candidate.
    rows = [row for row in _index() if role in row.roles]
    if not rows:
        return []
    query = embed([question])[0]
    scored = [(sum(a * b for a, b in zip(row.vector, query)), row) for row in rows]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [Match(row.slug, row.title, row.heading, row.text, round(score, 4))
            for score, row in scored[:k] if score >= min_score]
