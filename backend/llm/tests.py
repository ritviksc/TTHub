from django.test import TestCase
from unittest.mock import Mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings
from unittest.mock import patch
from django.core.cache import cache

from .tasks import get_models

from .services.client import generate


class GenerateTests(SimpleTestCase):
    @override_settings(DEFAULT_LLM_MODEL=None)
    def test_missing_model_does_not_call_provider(self):
        client = Mock()

        with self.assertRaises(ImproperlyConfigured):
            generate(
                client=client,
                prompt="Summarise attendance.",
                sys_prompt="Use only the supplied data.",
            )

        client.chat.completions.create.assert_not_called()
        
    @override_settings(DEFAULT_LLM_MODEL="default-model")
    def test_explicit_model_and_prompts_are_sent(self):
        client = Mock()
        client.chat.completions.create.return_value = Mock(
            choices=[
                Mock(
                    finish_reason="stop",
                    message=Mock(content="Attendance increased."),
                )
            ]
        )

        result = generate(
            client=client,
            prompt="Attendance rose from 10 to 12.",
            sys_prompt="Use only the supplied data.",
            model="chosen-model",
            max_tokens=200,
            temperature=0.1,
        )

        self.assertEqual(result, "Attendance increased.")
        client.chat.completions.create.assert_called_once_with(
            model="chosen-model",
            messages=[
                {
                    "role": "system",
                    "content": "Use only the supplied data.",
                },
                {
                    "role": "user",
                    "content": "Attendance rose from 10 to 12.",
                },
            ],
            max_tokens=200,
            temperature=0.1,
        )
        

@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "llm-cache-tests",
        }
    }
)
class ModelCacheTests(SimpleTestCase):
    def test_failed_refresh_preserves_cached_models(self):
        cache.set("llm:models", ["existing-model"], timeout=None)
        self.addCleanup(cache.delete, "llm:models")

        with patch(
            "llm.tasks.get_available_models",
            side_effect=RuntimeError("Provider unavailable"),
        ):
            with self.assertRaises(RuntimeError):
                get_models.run()

        self.assertEqual(
            cache.get("llm:models"),
            ["existing-model"],
        )