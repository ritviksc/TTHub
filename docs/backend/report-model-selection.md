# Choosing a report model

Super admins and branch managers can choose the AI model before requesting an attendance or physical-testing explanation. Super admins also choose one for ACC drafts. Instructors can't see the model catalogue or request AI analysis. Statistics are always available without AI.

All the report screens share one selector. It loads `GET /api/reporting/models/`, which returns `models` and `default`. The analysis request takes an optional `model`; if it's left out, the catalogue default is used. An unknown or malformed model is rejected with a validation error before any job is created or queued.

## Configuration

- `DEFAULT_LLM_MODEL` is the preferred default.
- `REPORT_LLM_MODELS` (optional) is a comma-separated list of models admins may choose. If the default isn't in the list, the first model listed becomes the default.

Without `REPORT_LLM_MODELS`, the catalogue uses the cached `llm:models` list, or fetches the provider's list with a four-second timeout. A successful, non-empty list is cached for five minutes. A failed or empty fetch isn't cached, so **Refresh models** works again as soon as the provider is back. The configured default is always included. Provider credentials and endpoints are never sent to the browser, and errors don't expose details.

Known non-chat models (embedding models such as `bge-m3`, rerankers, speech models) are filtered out of both the list and request validation, because they can't answer a report request. Use `REPORT_LLM_MODELS` to limit the list to models that suit the reports. If generation fails, the system doesn't fall back to another model.

## Saved model and audit

Each analysis job records `model_name` when it is queued, and the worker uses exactly that model, even if the default changes while the job waits. Status responses and completed explanations show the model used. Reports that didn't need AI (no data) say so.

Audit entries for report requests include the model identifier, shown as `Model: …` in the audit log. This is the identifier sent to the provider, not a verified model version or billing record.

## How to check it

1. Sign in as a super admin or branch manager and open either report.
2. Load statistics, choose a model and request an explanation.
3. Check the explanation shows the model you chose, then open Administration → Audit log, filter to Reports and check the same model appears.
4. As an instructor, check the catalogue and analysis endpoints are denied.

The automated tests (`python manage.py test reporting`) use a fake catalogue and provider. They cover permissions, unsupported models, both report types, the saved model surviving a default change, the audit summary and provider or cache outages.

## Key files

- `backend/llm/services/catalog.py`: model catalogue, filtering and caching
- `backend/reporting/views.py`, `serializers.py`, `tasks.py`: catalogue endpoint, validation and worker hand-off
- `frontend/src/components/reporting/ModelSelector.vue`: the selector
