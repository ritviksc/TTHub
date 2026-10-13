"""Split help articles into self-contained pieces for embedding."""
import re
from dataclasses import dataclass

# bge-m3 handles long inputs, but smaller chunks retrieve more precisely.
# Words are a cheap stand-in for tokens (roughly 1.3 tokens per word).
MAX_WORDS = 300
OVERLAP_WORDS = 40


@dataclass(frozen=True)
class Chunk:
    slug: str
    title: str
    heading: str
    text: str
    roles: tuple


def _sections(body):
    """(heading, text) pairs split on `## ` headings. Text before the first heading has no heading."""
    sections, heading, lines = [], "", []
    for line in body.splitlines():
        match = re.match(r"##\s+(.+?)\s*#*\s*$", line)
        if match and not line.startswith("###"):
            sections.append((heading, "\n".join(lines).strip()))
            heading, lines = match.group(1), []
        else:
            lines.append(line)
    sections.append((heading, "\n".join(lines).strip()))
    return [(heading, text) for heading, text in sections if text]


def _windows(text, max_words=MAX_WORDS, overlap=OVERLAP_WORDS):
    words = text.split()
    if len(words) <= max_words:
        return [text]
    step = max_words - overlap
    return [" ".join(words[start:start + max_words]) for start in range(0, len(words) - overlap, step)]


def chunk_doc(doc):
    chunks = []
    for heading, text in _sections(doc.body):
        # The audience, title and heading go first so the chunk makes sense on its
        # own, both to the embedding model and to the LLM reading it as context.
        # The audience tells the LLM whose job a step is ("Branch Manager › ...").
        label = " › ".join(part for part in (doc.audience_label, doc.title, heading) if part)
        for piece in _windows(text):
            chunks.append(Chunk(slug=doc.slug, title=doc.title, heading=heading,
                                text=f"{label}\n\n{piece}", roles=doc.roles))
    return chunks
