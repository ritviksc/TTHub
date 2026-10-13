"""Rebuild the help chatbot's index: chunk every article and embed the chunks.

Run after editing help/content/. Needs the LLM provider (university VPN off campus).
Unchanged chunks reuse their stored vector, so re-runs only embed what changed.
"""
import hashlib
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from help.models import HelpChunk
from help.services.chunking import chunk_doc
from help.services.docs import load_docs
from help.services.embeddings import embed, to_bytes
from help.services.retrieval import clear_cache


def content_hash(chunk, model):
    payload = json.dumps([model, chunk.text, sorted(chunk.roles)], ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Command(BaseCommand):
    help = "Chunk and embed the help articles for the help chatbot."

    def handle(self, *args, **options):
        model = settings.HELP_EMBED_MODEL
        chunks = [chunk for doc in load_docs() for chunk in chunk_doc(doc)]
        hashes = [content_hash(chunk, model) for chunk in chunks]
        stored = dict(HelpChunk.objects.filter(content_hash__in=hashes).values_list("content_hash", "embedding"))

        missing = [index for index, value in enumerate(hashes) if value not in stored]
        if missing:
            self.stdout.write(f"Embedding {len(missing)} of {len(chunks)} chunks with {model}...")
            for index, vector in zip(missing, embed([chunks[index].text for index in missing], model=model)):
                stored[hashes[index]] = to_bytes(vector)

        rows = [HelpChunk(slug=chunk.slug, title=chunk.title, heading=chunk.heading, text=chunk.text,
                          roles=list(chunk.roles), content_hash=value, embedding=stored[value], model=model)
                for chunk, value in zip(chunks, hashes)]
        with transaction.atomic():
            HelpChunk.objects.all().delete()
            HelpChunk.objects.bulk_create(rows)
        clear_cache()
        self.stdout.write(self.style.SUCCESS(
            f"Indexed {len(rows)} chunks from {len({chunk.slug for chunk in chunks})} articles "
            f"({len(missing)} embedded, {len(rows) - len(missing)} reused)."))
