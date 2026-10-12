"""Available report models from deployment configuration or the provider cache."""
import re
from django.conf import settings
from django.core.cache import cache
from redis.exceptions import RedisError
from .client import get_available_models


def is_report_model(value):
    # Providers can advertise embeddings alongside chat models. These known
    # non-generative families cannot answer the chat-completions report request.
    name = value.lower().rsplit('/', 1)[-1]
    return not (name.startswith(('bge-', 'e5-', 'gte-', 'whisper', 'text-embedding', 'embed-'))
                or 'embedding' in name or 'rerank' in name)


def clean_models(values):
    return list(dict.fromkeys(value for value in values if isinstance(value, str)
                             and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/+\-]{0,199}', value)
                             and is_report_model(value)))


def report_models():
    default = (settings.DEFAULT_LLM_MODEL or '').strip()
    configured = getattr(settings, 'REPORT_LLM_MODELS', [])
    if configured:
        models = clean_models(configured)
    else:
        try:
            models = cache.get('llm:models')
        except (RedisError, OSError):
            models = None
        if not models:
            try:
                models = get_available_models()
            except Exception:
                # Do not cache an outage as an empty catalogue: Retry must be able
                # to discover the other models as soon as the provider recovers.
                models = []
            else:
                if models:
                    try:
                        cache.set('llm:models', models, timeout=300)
                    except (RedisError, OSError):
                        pass
        models = clean_models([default, *models])
    return {'models': models, 'default': default if default in models else (models[0] if models else None)}
