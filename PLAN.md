# AI Provider Abstraction — Implementation Tasks

> **Branch:** main
> **Status:** All phases implemented (Phases 1-5 code complete; Phase 6 deps done; Phase 7 needs manual verification)
> **Depends on:** Python 3.14+, Frappe v16, `openai` SDK, existing notification adapter pattern

---

## Phase 1 — Package scaffolding & abstract interface

### Task 1.1 — Create `ai/` package

- [x] Create directory `armure_apim_sentinel/ai/`
- [x] Create `armure_apim_sentinel/ai/__init__.py` (empty)

### Task 1.2 — Define abstract base and data types

- [x] Create `armure_apim_sentinel/ai/base_provider.py`
- [x] Define `AuditResult` dataclass (`anomaly_score: int`, `report: str`, `alerts_count: int`)
- [x] Define `AIProvider` ABC with two abstract methods:
  - `audit_logs(self, logs: list[dict]) -> AuditResult`
  - `explain_error(self, log: dict) -> str`

### Task 1.3 — Extract shared prompt templates

- [x] Create `armure_apim_sentinel/ai/prompts.py`
- [x] Port `AUDIT_PROMPT` from `server.ts:943-960` with `{log_count}`, `{logs_json}` placeholders
- [x] Port `EXPLAIN_ERROR_PROMPT` from `server.ts:894-905` with `{status}`, `{latency}`, `{method}`, `{path}`, `{source}`, `{ip}`, `{log_json}` placeholders

---

## Phase 2 — Provider implementations

### Task 2.1 — Create providers sub-package

- [x] Create `armure_apim_sentinel/ai/providers/`
- [x] Create `armure_apim_sentinel/ai/providers/__init__.py` (empty)

### Task 2.2 — Gemini provider

- [x] Create `armure_apim_sentinel/ai/providers/gemini.py`
- [x] Class `GeminiProvider(AIProvider)`:
  - `__init__(self, api_key: str, model: str = "gemini-2.0-flash")`
  - `audit_logs()` — inline `from google import genai`, construct client, send `AUDIT_PROMPT`, parse score via regex
  - `explain_error()` — same client, send `EXPLAIN_ERROR_PROMPT`, return raw text
  - Raise descriptive exception if API key is empty
- [x] Port the score-parsing regex from current `api/ai.py:48-52`
- [x] Port the fallback error DocType creation pattern (moved to `api/ai.py` layer)

### Task 2.3 — OpenAI-compatible provider

- [x] Create `armure_apim_sentinel/ai/providers/openai_compatible.py`
- [x] Class `OpenAICompatibleProvider(AIProvider)`:
  - `__init__(self, api_base: str, api_key: str, model: str)`
  - Store `self._client = openai.OpenAI(base_url=api_base, api_key=api_key)`
  - `audit_logs()` — `client.chat.completions.create()`, parse score via same regex
  - `explain_error()` — same pattern, return `choices[0].message.content`
- [x] Use `armure_apim_sentinel.ai.prompts` for shared templates

---

## Phase 3 — Provider factory

### Task 3.1 — Factory function

- [x] Create `armure_apim_sentinel/ai/provider_factory.py`
- [x] `get_ai_provider() -> AIProvider`:
  - Read `settings = frappe.get_single("API Security App Settings")`
  - If `settings.ai_provider == "OpenAI Compatible"` → return `OpenAICompatibleProvider(api_base, api_key, model)`
  - Default → return `GeminiProvider(api_key=frappe.conf.get("gemini_api_key"), model=settings.ai_model)`

---

## Phase 4 — Refactor existing API module

### Task 4.1 — Rewrite `api/ai.py`

- [x] Remove inline `from google import genai` import
- [x] `run_ai_audit(logs_json)` — use `get_ai_provider().audit_logs()`, wrap in try/except
- [x] Keep existing fallback: error → create `AI Audit Assessment` DocType with error summary
- [x] Keep existing threshold logic: score > 40 → create `Alert Instance` + `publish_alert()`
- [x] Keep `publish_scan_complete()` call at the end
- [x] **New:** Implement `explain_error(logId)`:
  - `@frappe.whitelist(allow_guest=True, methods="POST")`
  - Fetch log from OpenSearch by ID via `opensearch_client.get_client().search()`
  - Call `get_ai_provider().explain_error(log)`
  - Return `{"explanation": str}`

---

## Phase 5 — DocType configuration

### Task 5.1 — Update API Security App Settings JSON

- [x] Read `armure_apim_sentinel/armure_apim_sentinel/doctype/api_security_app_settings/api_security_app_settings.json`
- [x] Add to `field_order`: `"ai_settings_section", "ai_provider", "ai_api_base", "ai_api_key", "ai_model"`
- [x] Add 5 new field entries to `fields` array:
  - Section break: `ai_settings_section`
  - Select: `ai_provider` — options `Gemini\nOpenAI Compatible`, default `Gemini`
  - Data: `ai_api_base` — default `http://ollama:11434/v1`
  - Password: `ai_api_key` — default empty
  - Data: `ai_model` — default `gemini-2.0-flash`

### Task 5.2 — Update API Security App Settings Python

- [x] Read `armure_apim_sentinel/armure_apim_sentinel/doctype/api_security_app_settings/api_security_app_settings.py`
- [x] Ensure new fields are exposed (Frappe auto-generates from JSON, but verify) — confirmed, class just has `pass`

---

## Phase 6 — Dependencies & build

### Task 6.1 — Add `openai` dependency

- [x] Edit `pyproject.toml` — add `"openai"` to `[project] dependencies`

### Task 6.2 — Run migration

> **Blocked:** requires `pip install openai` inside the container first (see error: ModuleNotFoundError). After install, run:
> `docker compose exec frappe bench --site apim.localhost migrate`

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

| File | Action | Status |
|---|---|---|---|
| `ai/__init__.py` | **Create** | Done |
| `ai/base_provider.py` | **Create** | Done |
| `ai/prompts.py` | **Create** | Done |
| `ai/providers/__init__.py` | **Create** | Done |
| `ai/providers/gemini.py` | **Create** | Done |
| `ai/providers/openai_compatible.py` | **Create** | Done |
| `ai/provider_factory.py` | **Create** | Done |
| `api/ai.py` | **Modify** — use provider, add `explain_error()` | Done |
| `doctype/api_security_app_settings/*.json` | **Modify** — add 5 AI config fields | Done |
| `doctype/api_security_app_settings/*.py` | **Verify** — auto-generated | Done |
| `pyproject.toml` | **Modify** — add `openai` dep | Done |

---

# Chart Zoom → Time Range Filter — Implementation Tasks

> **Status:** Not started
> **Depends on:** Existing frontend (Vue 3, echarts, Pinia), backend (Frappe, OpenSearch)
> **Design doc:** `implementation-plan.md` Section 14

---

## Phase 1 — Backend: Add `from`/`to` support to dashboard API

### Task 1.1 — Modify `aggregate_dashboard()` in `opensearch_client.py`

- [ ] Read `armure_apim_sentinel/opensearch_client.py`
- [ ] Add `from_timestamp: str | None = None` parameter to `aggregate_dashboard()` signature
- [ ] Add `to_timestamp: str | None = None` parameter to `aggregate_dashboard()` signature
- [ ] When `from_timestamp` is provided, use `datetime.fromisoformat(from_timestamp.replace("Z", "+00:00"))` instead of `now - timedelta(hours=period)`
- [ ] When `to_timestamp` is provided, use `datetime.fromisoformat(to_timestamp.replace("Z", "+00:00"))` as the range `lte` bound
- [ ] Pass the computed `end_time` into the OpenSearch timestamp `range` query as `lte`
- [ ] Verify `from_timestamp` and `to_timestamp` default to `None` — existing callers with `period=24` alone continue to work identically
- [ ] Ensure `_daily_index()` uses `end_time` (or `now`) for index selection when `to_timestamp` is provided

### Task 1.2 — Modify dashboard endpoints in `api/dashboard.py`

- [ ] Read `armure_apim_sentinel/api/dashboard.py`
- [ ] Add `from_=None` parameter to `get_summary()` (Frappe receives `from` from URL; trailing underscore avoids Python keyword)
- [ ] Add `to=None` parameter to `get_summary()`
- [ ] Pass `from_timestamp=from_` and `to_timestamp=to` to `aggregate_dashboard()` call
- [ ] Repeat for `get_charts()` — same `from_=None`, `to=None` params
- [ ] Repeat for `get_breakdown()` — same `from_=None`, `to=None` params
- [ ] Ensure all 3 endpoints remain backward compatible: existing calls with `?period=24` still work

---

## Phase 2 — Frontend: Central time range state in Pinia store

### Task 2.1 — Add time range state and actions

- [ ] Read `frontend/src/stores/telemetry.js`
- [ ] Add `timeRange: ref(null)` to the store's state — holds `null` or `{ from: number, to: number }` (millisecond timestamps)
- [ ] Add action `setTimeRange(from, to)`:
  - Sets `timeRange.value = { from, to }`
  - Calls `fetchDashboard()` (which will pick up the range)
- [ ] Add action `clearTimeRange()`:
  - Sets `timeRange.value = null`
  - Calls `fetchDashboard()` with default period

### Task 2.2 — Modify `fetchDashboard()` to pass from/to

- [ ] Read `fetchDashboard(period = 24)` in telemetry.js
- [ ] Inside the action, check if `timeRange.value` is non-null
- [ ] If set: pass `from_` and `to` as query params to all 3 API calls (`get_summary`, `get_charts`, `get_breakdown`)
- [ ] If null: pass `period` as before
- [ ] Verify the `from_` param name matches the backend (Frappe receives `from` from URL, maps to `from_` on the Python side)
- [ ] Do NOT modify `pollAll()` — it continues passing `period` (the polling mechanism always uses the period preset, not the custom range)

---

## Phase 3 — Frontend: Dashboard chart interaction

### Task 3.1 — Wire echarts click and zoom events on Traffic Volume chart

- [ ] Read `frontend/src/pages/DashboardPage.vue`
- [ ] Add `@chart-click` event to the `<VChart>` for traffic volume chart (remove the click handler from the wrapping `<div>`)
- [ ] Add `@datazoom` event to the same `<VChart>`
- [ ] Write `handleChartClick(params)`:
  - If `params?.data?.timestamp` exists, get millisecond timestamp
  - Compute: `from = timestamp - 1800000` (30 min before), `to = timestamp + 1800000` (30 min after)
  - Call `telemetry.setTimeRange(from, to)`
- [ ] Write `handleDataZoom(params)`:
  - If `params.startValue` and `params.endValue` exist (both numbers = timestamps)
  - Call `telemetry.setTimeRange(params.startValue, params.endValue)`

### Task 3.2 — Wire echarts events on Latency Trend chart

- [ ] Same as Task 3.1 — add `@chart-click` and `@datazoom` to the latency chart's `<VChart>`
- [ ] Reuse the same `handleChartClick` and `handleDataZoom` handlers

### Task 3.3 — Remove local datetime-local state and update dependent UI

- [ ] Remove `localStartTime` and `localEndTime` refs and their watchers
- [ ] Update "Dashboard Historical Lens" section to read from `telemetry.timeRange` instead of local state:
  - Show `from` and `to` as formatted display text
  - Or keep the `<input type="datetime-local">` but sync bidirectionally with `telemetry.timeRange`
- [ ] Decision: remove datetime-local inputs entirely, replace with a compact "Filtered: [time range] — Clear" badge. The inputs are redundant now that clicking charts directly re-fetches data.

### Task 3.4 — Update "Clear Lens" and "Explore Logs" buttons

- [ ] `clearLens()` → call `telemetry.clearTimeRange()` instead of resetting local state
- [ ] `exploreLogs()` → read `from`/`to` from `telemetry.timeRange` instead of local state
- [ ] Navigate to logs page with query params: `router.push({ name: 'logs', query: { startMs: from, endMs: to } })`

---

## Phase 4 — Frontend: URL query param sync

### Task 4.1 — Watch `telemetry.timeRange` and sync to URL

- [ ] Read `frontend/src/App.vue`
- [ ] Add a `watch` on `() => telemetry.timeRange` (deep watch via getter function):
  - When timeRange is set: update current route query with `from` and `to` via `router.replace({ query: { ...route.query, from: String(range.from), to: String(range.to) } })`
  - When cleared: remove `from` and `to` from query via `router.replace({ query: { ...cleaned } })`
- [ ] Avoid infinite loops: check if the values actually changed before calling `router.replace`

### Task 4.2 — Restore time range from URL on mount

- [ ] In `App.vue`'s `onMounted`, add logic to parse `route.query.from` and `route.query.to`
- [ ] If both are valid numeric strings, parse them and call `telemetry.setTimeRange(from, to)`
- [ ] This enables bookmarkable/shared URLs

### Task 4.3 — Clear custom range when period preset is clicked

- [ ] In the existing `watch(periodHours, ...)` in App.vue, add `telemetry.clearTimeRange()` before `telemetry.fetchDashboard(val)`
- [ ] This ensures switching between period presets removes any custom zoom range

---

## Phase 5 — Frontend: LogsPage query param consumption

### Task 5.1 — Read dashboard's time range from route query

- [ ] Read `frontend/src/pages/LogsPage.vue`
- [ ] In `onMounted`, check for `route.query.startMs` and `route.query.endMs`
- [ ] If present, set the page's `startTime` and `endTime` local refs
- [ ] Trigger `refetchLogs()` to load logs filtered to that time window
- [ ] Ensure the "Reset Time" button on LogsPage clears both params from the URL as well

---

## Phase 6 — Verification

### Task 6.1 — Backend verification

- [ ] `curl "http://localhost:8000/api/method/armure_apim_sentinel.api.dashboard.get_summary?from=2025-05-25T00:00:00Z&to=2025-05-25T23:59:59Z"` returns filtered KPIs
- [ ] `curl "http://localhost:8000/api/method/armure_apim_sentinel.api.dashboard.get_summary?period=24"` returns same result as before (backward compat)
- [ ] Invalid timestamp format returns graceful error

### Task 6.2 — Frontend verification

- [ ] Dashboard loads with default 24h period (no custom range)
- [ ] Click a data point on Traffic Volume chart → dashboard re-fetches, charts show filtered window
- [ ] Drag-to-zoom on Traffic Volume chart → same behavior with exact boundaries
- [ ] Click/Latency chart click → same behavior
- [ ] URL query params `?from=...&to=...` appear in address bar
- [ ] Copy URL → open in new tab → dashboard restores the same time window
- [ ] Change period in header dropdown → custom range clears, dashboard reverts to preset
- [ ] "Explore Logs for Timeframe" navigates to LogsPage with correct start/end
- [ ] LogsPage shows logs filtered to that time window
- [ ] LogsPage "Reset Time" clears the filter
- [ ] Pie chart click does NOT affect time range (no zoom on pie)
- [ ] Anomaly chart click does NOT affect time range (no zoom on anomaly)

### Task 6.3 — Regression

- [ ] Polling still works (every 2.5s using period preset)
- [ ] MetricsCards still update on poll
- [ ] AlertsPage / SourcesPage / NotificationsPage unchanged
- [ ] All existing API calls without `from`/`to` params return correct results

---

## File change summary

| File | Action |
|---|---|
| `armure_apim_sentinel/opensearch_client.py` | **Modify** — add `from_timestamp`/`to_timestamp` to `aggregate_dashboard()` |
| `armure_apim_sentinel/api/dashboard.py` | **Modify** — add `from_`/`to` params to 3 endpoints |
| `frontend/src/stores/telemetry.js` | **Modify** — add `timeRange`, `setTimeRange()`, `clearTimeRange()`, update `fetchDashboard()` |
| `frontend/src/pages/DashboardPage.vue` | **Modify** — replace local datetime state, add echarts events |
| `frontend/src/App.vue` | **Modify** — URL sync watcher, period→clear range, init from URL |
| `frontend/src/pages/LogsPage.vue` | **Modify** — read `startMs`/`endMs` from route query |
