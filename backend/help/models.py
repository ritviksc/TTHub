from django.db import models


class HelpChunk(models.Model):
    """One embedded piece of a help article. The whole table is the RAG index.

    Rows are rebuilt by `python manage.py build_help_index`; nothing else writes them.
    """
    slug = models.SlugField(max_length=100)
    title = models.CharField(max_length=200)
    heading = models.CharField(max_length=200, blank=True)
    text = models.TextField()
    roles = models.JSONField(default=list)
    # Hash of the embedded text, roles and model, so unchanged chunks reuse their vector.
    content_hash = models.CharField(max_length=64)
    # L2-normalised float32 vector, see help/services/embeddings.py.
    embedding = models.BinaryField()
    model = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["slug", "id"]

    def __str__(self):
        return f"{self.slug} › {self.heading}" if self.heading else self.slug
