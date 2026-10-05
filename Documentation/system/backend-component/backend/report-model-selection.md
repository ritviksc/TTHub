# Choosing a report model

Super admins and branch admins can select an AI model before requesting attendance or physical-testing analysis. Instructors cannot access the model catalogue or reporting analysis endpoints. Statistics remain available without AI.

The selector is shared by both report screens. It loads `GET /api/reporting/models/`, which returns `models` and `default`. The analysis POST accepts an optional `model`; omitted values use the catalogue default. Unavailable or malformed choices return a validation error before job creation or queue submission.

## Configuration

`DEFAULT_LLM_MODEL` remains the preferred default. Optionally set `REPORT_LLM_MODELS` to a comma-separated list of model identifiers supported by the configured chat provider. This list controls which models admins can choose; if the preferred default is not included, the first listed model is selected. No provider credentials or endpoints are sent to the browser.

Without an explicit list, the catalogue uses the existing `llm:models` cache or fetches the provider's model list with a four-second timeout. Successful, nonempty catalogue results are cached for five minutes. Failed or empty discovery is not cached, so Refresh models can recover immediately when the provider becomes available. The configured default is included as a fallback. Cache/provider failures do not expose error details. The existing `llm.tasks.get_models` task can also refresh the shared cache (its existing indefinite cache lifetime remains unchanged).

Discovery filters known non-chat families (including BGE embeddings), on both catalogue display and request validation. This also filters previously cached entries. Provider identifiers are not a full compatibility or quality assessment; use `REPORT_LLM_MODELS` to include only models compatible with the existing chat request. There is no silent fallback to another model if generation fails.

## Persistence and audit

Both analysis-job tables have `model_name`, saved when the request is queued. Celery passes that exact value to the existing explanation service; changing the default while a report waits does not change its selection. Status responses return the recorded model, and completed explanations display it.

Audit request/status entries include the model identifier, and the plain-language log description shows `Model: …`. This is the identifier sent to the provider, not a separately verified provider-resolved model version or billing record. Reports with no data skip AI and say no AI was needed. Existing completed reports are left blank and displayed as model not recorded. Legacy unfinished jobs without a model capture the current default when claimed by the updated worker.

Apply the reporting migration and restart Django and Celery before using model selection, so the web process and workers run the same code. No credentials or model infrastructure are changed by this feature.

## Verification

1. Log in as a super admin or branch admin and open either reporting page.
2. Load statistics with data, choose a model and request an explanation.
3. Confirm the displayed model matches the selection. Open Administration → Audit log and filter to Reports; confirm the report entry shows that model.
4. Repeat for the other report type. With more than one model configured, choose another one.
5. Confirm instructors cannot open the catalogue/report API, and an unknown model is rejected.

Tests use a fake catalogue/provider. They cover role permissions, unsupported choices, both report types, saved model selection surviving a default change, worker forwarding, audit summaries, cache reuse and provider/cache outages. Live provider generation and browser interaction are separate manual checks.

## Files

- `backend/llm/services/catalog.py`: shared model catalogue and fallback handling.
- `backend/llm/services/client.py`: bounded discovery timeout.
- `backend/config/settings.py`: optional deployment model list.
- `backend/reporting/{models.py,serializers.py,views.py,urls.py,tasks.py}` and migration `0003_attendanceanalysisjob_model_name_and_more.py`: model persistence, validation, catalogue endpoint and worker forwarding.
- `backend/audit/{services.py,presentation.py}`: recorded model and readable log description.
- `frontend/src/apis.js`: catalogue GET through existing retry helper.
- `frontend/src/components/reporting/{ModelSelector.vue,AttendanceReport.vue,ReportAnalysis.vue}`: shared selector, request payloads and completed-model labels.
- `backend/reporting/{test_model_selection.py,tests.py,test_physical.py,test_job_deadline.py}`: model tests and existing worker-test updates.

## Follow-up bug check

A saved failed attendance job used `ONCAMPUS/BAAI/bge-m3`, while a nearby Gemma job succeeded. The previous catalogue offered all provider IDs, including embedding models. Regression tests now verify exclusion and POST rejection of that cached embedding ID, and recovery on the very next request after a provider outage. The selector always offers Refresh models. Live catalogue verification was attempted but the provider connection was unavailable from the development-agent environment; no participant data was sent for that check.
