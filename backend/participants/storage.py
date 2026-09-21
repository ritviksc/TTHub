from pathlib import Path
from uuid import uuid4

from django.core.files.storage import storages


def consent_storage():
    # A separate alias keeps medical documents outside publicly served media.
    return storages["private"]


def consent_upload_path(instance, filename):
    return f"gp_consents/{instance.pk}/{uuid4().hex}{Path(filename).suffix.lower()}"
