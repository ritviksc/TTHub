from pathlib import Path

from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

IMAGE_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG"}
# Word and Excel files are zip containers, so the zip signature is the check.
OFFICE_EXTENSIONS = {".docx", ".xlsx"}

DOCUMENT_EXTENSIONS = (".pdf", *IMAGE_FORMATS, *OFFICE_EXTENSIONS)


def validate_upload(value, allowed=DOCUMENT_EXTENSIONS,
                    type_message="Use a PDF, JPG, PNG, Word or Excel document."):
    """Check an uploaded file's size and that its contents match its extension.

    Returns the file rewound, ready to save.
    """
    if value.size > MAX_UPLOAD_BYTES:
        raise serializers.ValidationError("The document must be 10 MB or smaller.")
    extension = Path(value.name).suffix.lower()
    if extension not in allowed:
        raise serializers.ValidationError(type_message)
    try:
        if extension == ".pdf":
            if value.read(5) != b"%PDF-":
                raise serializers.ValidationError("Upload a valid PDF document.")
        elif extension in OFFICE_EXTENSIONS:
            if value.read(4) != b"PK\x03\x04":
                raise serializers.ValidationError("Upload a valid Word or Excel document.")
        else:
            image = Image.open(value)
            if image.format != IMAGE_FORMATS[extension]:
                raise serializers.ValidationError("The image does not match its file extension.")
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise serializers.ValidationError("Upload a valid image document.")
    finally:
        value.seek(0)
    return value
