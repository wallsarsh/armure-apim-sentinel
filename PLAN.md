# AI Provider Abstraction — Implementation Tasks

> **Branch:** main
> **Status:** Not started
> **Depends on:** Python 3.14+, Frappe v16, `openai` SDK, existing notification adapter pattern

---

## Phase 1 — Package scaffolding & abstract interface

### Task 1.1 — Create `ai/` package

- [ ] Create directory `armure_apim_sentinel/ai/`
- [ ] Create `armure_apim_sentinel/ai/__init__.py` (empty)

### Task 1.2 — Define abstract base and data types

- [ ] Create `armure_apim_sentinel/ai/base_provider.py`
- [ ] Define `AuditResult` dataclass (`anomaly_score: int`, `report: str`, `alerts_count: int`)
- [ ] Define `AIProvider` ABC with two abstract methods:
  - `audit_logs(self, logs: list[dict]) -> AuditResult`
  - `explain_error(self, log: dict) -> str`

### Task 1.3 — Extract shared prompt templates

- [ ] Create `armure_apim_sentinel/ai/prompts.py`
- [ ] Port `AUDIT_PROMPT` from `server.ts:943-960` with `{log_count}`, `{logs_json}` placeholders
- [ ] Port `EXPLAIN_ERROR_PROMPT` from `server.ts:894-905` with `{status}`, `{latency}`, `{method}`, `{path}`, `{source}`, `{ip}`, `{log_json}` placeholders

---

## Phase 2 — Provider implementations

### Task 2.1 — Create providers sub-package

- [ ] Create `armure_apim_sentinel/ai/providers/`
- [ ] Create `armure_apim_sentinel/ai/providers/__init__.py` (empty)

### Task 2.2 — Gemini provider

- [ ] Create `armure_apim_sentinel/ai/providers/gemini.py`
- [ ] Class `GeminiProvider(AIProvider)`:
  - `__init__(self, api_key: str, model: str = "gemini-2.0-flash")`
  - `audit_logs()` — inline `from google import genai`, construct client, send `AUDIT_PROMPT`, parse score via regex
  - `explain_error()` — same client, send `EXPLAIN_ERROR_PROMPT`, return raw text
  - Raise descriptive exception if API key is empty
- [ ] Port the score-parsing regex from current `api/ai.py:48-52`
- [ ] Port the fallback error DocType creation pattern (moved to `api/ai.py` layer)

### Task 2.3 — OpenAI-compatible provider

- [ ] Create `armure_apim_sentinel/ai/providers/openai_compatible.py`
- [ ] Class `OpenAICompatibleProvider(AIProvider)`:
  - `__init__(self, api_base: str, api_key: str, model: str)`
  - Store `self._client = openai.OpenAI(base_url=api_base, api_key=api_key)`
  - `audit_logs()` — `client.chat.completions.create()`, parse score via same regex
  - `explain_error()` — same pattern, return `choices[0].message.content`
- [ ] Use `armure_apim_sentinel.ai.prompts` for shared templates

---

## Phase 3 — Provider factory

### Task 3.1 — Factory function

- [ ] Create `armure_apim_sentinel/ai/provider_factory.py`
- [ ] `get_ai_provider() -> AIProvider`:
  - Read `settings = frappe.get_single("API Security App Settings")`
  - If `settings.ai_provider == "OpenAI Compatible"` → return `OpenAICompatibleProvider(api_base, api_key, model)`
  - Default → return `GeminiProvider(api_key=frappe.conf.get("gemini_api_key"), model=settings.ai_model)`

---

## Phase 4 — Refactor existing API module

### Task 4.1 — Rewrite `api/ai.py`

- [ ] Remove inline `from google import genai` import
- [ ] `run_ai_audit(logs_json)` — use `get_ai_provider().audit_logs()`, wrap in try/except
- [ ] Keep existing fallback: error → create `AI Audit Assessment` DocType with error summary
- [ ] Keep existing threshold logic: score > 40 → create `Alert Instance` + `publish_alert()`
- [ ] Keep `publish_scan_complete()` call at the end
- [ ] **New:** Implement `explain_error(logId)`:
  - `@frappe.whitelist(allow_guest=True, methods="POST")`
  - Fetch log from OpenSearch by ID via `opensearch_client.get_client().search()`
  - Call `get_ai_provider().explain_error(log)`
  - Return `{"explanation": str}`

---

## Phase 5 — DocType configuration

### Task 5.1 — Update API Security App Settings JSON

- [ ] Read `armure_apim_sentinel/armure_apim_sentinel/doctype/api_security_app_settings/api_security_app_settings.json`
- [ ] Add to `field_order`: `"ai_settings_section", "ai_provider", "ai_api_base", "ai_api_key", "ai_model"`
- [ ] Add 5 new field entries to `fields` array:
  - Section break: `ai_settings_section`
  - Select: `ai_provider` — options `Gemini\nOpenAI Compatible`, default `Gemini`
  - Data: `ai_api_base` — default `http://ollama:11434/v1`
  - Password: `ai_api_key` — default empty
  - Data: `ai_model` — default `gemini-2.0-flash`

### Task 5.2 — Update API Security App Settings Python

- [ ] Read `armure_apim_sentinel/armure_apim_sentinel/doctype/api_security_app_settings/api_security_app_settings.py`
- [ ] Ensure new fields are exposed (Frappe auto-generates from JSON, but verify)

---

## Phase 6 — Dependencies & build

### Task 6.1 — Add `openai` dependency

- [ ] Edit `pyproject.toml` — add `"openai"` to `[project] dependencies`

### Task 6.2 — Run migration

- [ ] `docker compose exec -w "/workspace/development/armure-apim" frappe bench --site apim.localhost migrate`

### Task 6.3 — Run build

- [ ] `docker compose exec -w "/workspace/development/armure-apim" frappe bench build`

---

## Phase 7 — Verification

### Task 7.1 — Gemini provider (default, backward compat)

- [ ] Without `gemini_api_key` in `frappe.conf` → `run_ai_audit` creates error DocType
- [ ] With valid `gemini_api_key` → `run_ai_audit` returns analysis, creates DocType
- [ ] `explain_error(logId)` returns markdown for a valid log
- [ ] `explain_error("nonexistent")` returns "Log not found" fallback

### Task 7.2 — OpenAI-compatible provider (Ollama)

- [ ] Set `AI Provider = "OpenAI Compatible"`, `AI API Base = http://ollama:11434/v1`, `AI Model = llama3.2` in App Settings
- [ ] `run_ai_audit` with sample logs returns `AuditResult` from Ollama
- [ ] `explain_error(logId)` returns markdown via Ollama
- [ ] Invalid API base returns graceful error DocType

### Task 7.3 — Regression

- [ ] Frontend anomaly scan trigger → queue → result → realtime works end-to-end
- [ ] Frontend "Explain Trace Cause" button on LogsPage works
- [ ] `AI Audit Assessment` DocType records created correctly in both provider modes
- [ ] Alert Instance created when score > 40 in both modes

---

## File change summary

| File | Action |
|---|---|
| `ai/__init__.py` | **Create** |
| `ai/base_provider.py` | **Create** |
| `ai/prompts.py` | **Create** |
| `ai/providers/__init__.py` | **Create** |
| `ai/providers/gemini.py` | **Create** |
| `ai/providers/openai_compatible.py` | **Create** |
| `ai/provider_factory.py` | **Create** |
| `api/ai.py` | **Modify** — use provider, add `explain_error()` |
| `doctype/api_security_app_settings/*.json` | **Modify** — add 5 AI config fields |
| `doctype/api_security_app_settings/*.py` | **Verify** — auto-generated |
| `pyproject.toml` | **Modify** — add `openai` dep |
