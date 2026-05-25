# Implementation Plan: API Security Monitor (Frappe Framework)

## Overview

Port the functional prototype from `api-monitoring-governance/` (React + Express TypeScript) to a Frappe Framework custom app named `api_security_monitor`. Target stack: **Frappe Framework** (backend), **Vue 3 + Pinia + frappe-ui + Tailwind** (frontend), **OpenSearch** (log storage/analytics), **Redis** (cache/pub-sub), **Frappe WebSockets** (realtime).

---

## Table of Contents

1. [Feature Inventory — Prototype vs. Frappe](#1-feature-inventory)
2. [Data Model — All DocTypes + OpenSearch Mapping](#2-data-model)
3. [Backend Architecture — Python/Frappe Modules](#3-backend-architecture)
4. [API Endpoint Mapping](#4-api-endpoint-mapping)
5. [Frontend Architecture — Vue 3 SPA (JavaScript Only)](#5-frontend-architecture)
6. [Realtime WebSocket Flow](#6-realtime-websocket-flow)
7. [Simulation Engine](#7-simulation-engine)
8. [Deployment Configuration](#8-deployment-configuration)
9. [Implementation Order (7 Phases)](#9-implementation-order)
10. [Verification Checklist](#10-verification-checklist)

---

## 1. Feature Inventory

### 1.1 Data Models (prototype → Frappe)

| Prototype Entity | Frappe Target |
|---|---|
| `APILog` | OpenSearch index `api-telemetry-logs-YYYY.MM.DD` |
| `Source` | DocType: **Log Ingest Adapter** |
| `AlertRule` | DocType: **Security Alert Rule** |
| `AlertInstance` | DocType: **Alert Instance** |
| `AnomalyReport` | DocType: **AI Audit Assessment** |
| *(nonexistent)* | Singleton DocType: **API Security App Settings** |
| *(nonexistent)* | Singleton DocType: **Simulation Config** (or merge into App Settings) |

### 1.2 Backend API Endpoints (20 routes)

| # | Prototype Route | Method | Purpose |
|---|---|---|---|
| 1 | `/api/dashboard/summary` | GET | Aggregate KPIs (totalRequests, avgLatency, successRate, errorCount, rateLimitCount, activeAlerts) |
| 2 | `/api/dashboard/charts` | GET | Time-bucketed traffic/error/latency histogram |
| 3 | `/api/dashboard/breakdown` | GET | Per-source, per-status-code, per-endpoint breakdown |
| 4 | `/api/logs` | GET | Filtered log query (search, source, status, method, latency, time) |
| 5 | `/api/logs/ingest` | POST | Custom batch ingestion (array or single) |
| 6 | `/api/sources` | GET | List sources |
| 7 | `/api/sources` | POST | Create source |
| 8 | `/api/sources/:id/status` | PUT | Toggle active/inactive |
| 9 | `/api/sources/:id` | DELETE | Delete source |
| 10 | `/api/rules` | GET | List alert rules |
| 11 | `/api/rules` | POST | Create rule |
| 12 | `/api/rules/:id` | PUT | Update rule (toggle enabled, change fields) |
| 13 | `/api/rules/:id` | DELETE | Delete rule |
| 14 | `/api/alerts` | GET | List alerts |
| 15 | `/api/alerts/resolve` | POST | Resolve all alerts |
| 16 | `/api/alerts/:id/resolve` | POST | Resolve specific alert |
| 17 | `/api/simulation/config` | POST | Set speed and active/paused state |
| 18 | `/api/explain-error` | POST | Gemini AI per-log trace explanation |
| 19 | `/api/anomaly-scan` | POST | Gemini AI batch anomaly detection |
| 20 | `/api/anomaly-scan/history` | GET | Past AnomalyReport entries |

### 1.3 Frontend Components (6)

| Component | Tab ID | Description |
|---|---|---|
| `Sidebar` | — | Navigation, live status indicator, UTC clock |
| `MetricsCards` | — | 4 KPI cards (always visible) |
| `Dashboard` | `dashboard` | Charts, breakdowns, time controls, anomaly trend |
| `LogViewer` | `logs` | Filters, log table, trace inspector, CSV export, Gemini explainer |
| `AlertsPanel` | `alerts` | 3 sub-tabs: triggered alerts, rules CRUD, AI scanner |
| `SourceConfig` | `sources` | Simulation controls, source CRUD, JSON/CSV ingest |

### 1.4 Conditional UI States (73+)

Every loading, empty, error, disabled, color-coded threshold, and animation state in the prototype must be preserved 1:1. Key categories:

- **Loading**: spinner placeholders on metrics, charts, log table
- **Empty**: "No logs match filters", "No scan history", "System Operations Normal"
- **Error**: Gemini API failure, CSV parse failure, ingest failure banners
- **Disabled**: Export button when no logs, Ingest button when empty textarea
- **Color thresholds**: latency (>1000ms red, >300ms amber), error rate (>5% red, >0% amber), anomaly score (>60 red, >30 amber)
- **Animations**: pulsing alert cards, spinning loaders, ping dots on live indicators
- **Conditional visibility**: Resolve All button only when unresolved exist, Clear Lens only when filter active

---

## 2. Data Model

### 2.1 DocType: Log Ingest Adapter

| Field | Type | Details |
|---|---|---|
| `channel_name` | Data (unique, mandatory) | Source display name |
| `protocol_type` | Select | `Gateway\nWebhook\nAgent\nCustom` |
| `secret_token` | Password | Auto-generated; read-only after creation |
| `status` | Select | `Active\nInactive`, default `Active` |
| `total_logs_received` | Int (read-only) | Auto-incremented on each ingest |

### 2.2 DocType: Security Alert Rule

| Field | Type | Details |
|---|---|---|
| `rule_name` | Data (mandatory) | Human-readable name |
| `metric` | Select | `latency\nstatus_code\nrate_limit` |
| `condition` | Select | `gt (Greater Than)\nlt (Less Than)\neq (Equals)` |
| `threshold` | Int (mandatory) | Numeric threshold value |
| `duration` | Int | Monitoring window in minutes, default `1` |
| `severity` | Select | `info\nwarning\ncritical`, default `warning` |
| `is_active` | Check | Default `1` (enabled) |

### 2.3 DocType: Alert Instance

| Field | Type | Details |
|---|---|---|
| `rule` | Link → Security Alert Rule | Optional |
| `alert_message` | Text (mandatory) | Human-readable description |
| `severity` | Select | `info\nwarning\ncritical` |
| `alert_type` | Select | `System\nAI`, default `System` |
| `resolved` | Check | Default `0` |
| `details` | Code | JSON string of triggering log context |
| `timestamp` | Datetime | Default: `Now` |

### 2.4 DocType: AI Audit Assessment

| Field | Type | Details |
|---|---|---|
| `scan_time` | Datetime | Default: `Now` |
| `anomaly_score` | Float (0–100) | Gemini-generated score |
| `generated_summary` | Text Editor | Full markdown report from Gemini |
| `triggered_alerts_count` | Int | Default `0` |

### 2.5 DocType: API Security App Settings (Singleton)

| Field | Type | Details |
|---|---|---|
| `opensearch_host` | Data | Default `"localhost"` |
| `opensearch_port` | Int | Default `9200` |
| `opensearch_user` | Data | Default `"admin"` |
| `opensearch_password` | Password | Stored encrypted |
| `enable_live_simulation` | Check | Default `1` |
| `simulation_interval_ms` | Int | Default `4000` |

### 2.6 OpenSearch Index Mapping

```
Index pattern: api-telemetry-logs-YYYY.MM.DD (daily rotation)

Field                  Type        Notes
──────────────────────────────────────────────────
id                     keyword     log_xxx-uuid
timestamp              date        ISO 8601
method                 keyword     GET/POST/PUT/DELETE/PATCH
path                   keyword     /api/v1/users/login
status                 integer     HTTP status code
latency                integer     milliseconds
source                 keyword     service name
ip                     ip          Client IP address
user_agent             text        User-Agent header
payload_size           integer     bytes
request_headers        flattened   JSON object
response_body          text        Response payload snippet
user_id                keyword     usr_xxx or null
rate_limit_limit       integer     Requests allowed per window
rate_limit_remaining   integer     Requests remaining in window
```

Index settings: 1 shard, 1 replica. Auto-created on first daily write if absent.

---

## 3. Backend Architecture

### 3.1 Directory Layout

```
api_security_monitor/
└── api_security_monitor/
    ├── __init__.py
    ├── hooks.py                   # App metadata + scheduler + websocket events + permission hooks
    ├── install.py                 # after_migrate → seed defaults
    ├── uninstall.py               # before_uninstall cleanup
    ├── decorators.py              # @whitelist(role), @validate_type — custom decorators
    ├── permissions.py             # get_permission_query_conditions, has_permission
    ├── opensearch_client.py       # get_client(), ensure_index(), index_log()
    ├── utils.py                   # Rule evaluation engine, Redis cache helpers
    ├── realtime.py                # publish_alert(), publish_scan_complete()
    ├── api/
    │   ├── __init__.py
    │   ├── dashboard.py           # get_summary(), get_charts(), get_breakdown()
    │   ├── logs.py                # query_logs(), ingest_logs()
    │   ├── sources.py             # list, create, toggle, delete
    │   ├── rules.py               # list, create, update, delete
    │   ├── alerts.py              # list, resolve_all, resolve_one
    │   ├── simulation.py          # get_config(), update_config()
    │   └── ai_gemini.py           # explain_error(), run_anomaly_scan(), get_scan_history()
    ├── fixtures/                  # Seed data JSON (default sources, rules)
    ├── tasks.py                   # generate_simulated_logs() (cron worker)
    └── doc_events.py              # Rule on_update → invalidate Redis cache
```

### 3.2 hooks.py Configuration

```python
app_name = "api_security_monitor"
app_title = "API Security Monitor"
app_publisher = "..."
app_description = "Real-time API threat auditing with OpenSearch & WebSockets"
app_email = "..."
app_license = "MIT"

# ── Permission hooks (delegates to permissions.py) ──
permission_query_conditions = {
    "Log Ingest Adapter": "api_security_monitor.permissions.get_permission_query_conditions",
    "Security Alert Rule": "api_security_monitor.permissions.get_permission_query_conditions",
    "Alert Instance": "api_security_monitor.permissions.get_permission_query_conditions",
    "AI Audit Assessment": "api_security_monitor.permissions.get_permission_query_conditions",
}
has_permission = {
    "Log Ingest Adapter": "api_security_monitor.permissions.has_permission",
    "Security Alert Rule": "api_security_monitor.permissions.has_permission",
    "Alert Instance": "api_security_monitor.permissions.has_permission",
    "AI Audit Assessment": "api_security_monitor.permissions.has_permission",
}

# ── SPA route — all frontend paths served by one page ──
website_route_rules = [
    {"from_route": "/api-security-monitor/<path:app_path>", "to_route": "api_security_monitor"},
]

# ── DocType JS (client-side scripts) ──
doctype_js = {
    "Security Alert Rule": "public/js/security_alert_rule.js"
}

# ── Scheduler ──
scheduler_events = {
    "cron": {
        "*/1 * * * *": [
            "api_security_monitor.tasks.generate_simulated_logs"
        ]
    }
}

# ── Lifecycle ──
after_migrate = ["api_security_monitor.install.after_migrate"]

# ── Visibility ──
add_to_apps_screen = ["api_security_monitor"]
```

The `website_route_rules` entry maps all frontend SPA paths (`/api-security-monitor/...`) to a single page route handler so Vue Router controls client-side navigation. The `add_to_apps_screen` entry makes the app visible in the Frappe App Switcher.

### 3.3 install.py — Seed Data

The `after_migrate` hook must be idempotent and seed:

- **4 Log Ingest Adapters**: Auth Service (gateway), Billing Gateway (webhook), Catalog Engine (gateway), Data Collector (agent)
- **3 Security Alert Rules**:
  1. "Critical Response Latency Spike" — metric: latency, condition: gt, threshold: 800, severity: critical
  2. "High HTTP Error Count" — metric: status_code, condition: gt, threshold: 499, severity: warning
  3. "Rate Limit Exhaustion Trigger" — metric: rate_limit, condition: lt, threshold: 5, severity: info
- **API Security App Settings** singleton with defaults

### 3.4 Rule Evaluation Engine (utils.py)

Logic ported directly from `server.ts` `evaluateRulesForLog()`:

```python
def evaluate_rules_for_log(log_payload):
    rules = frappe.get_all("Security Alert Rule", filters={"is_active": 1})
    for rule in rules:
        triggered = False
        message = ""
        if rule.metric == "latency" and rule.condition == "gt" and log_payload.latency > rule.threshold:
            triggered = True
            message = f"High latency on {log_payload.method} {log_payload.path}: {log_payload.latency}ms"
        elif rule.metric == "status_code" and rule.condition == "gt" and log_payload.status > rule.threshold:
            triggered = True
            message = f"HTTP {log_payload.status} Error on {log_payload.path}"
        elif rule.metric == "rate_limit" and rule.condition == "lt" and log_payload.rate_limit_remaining < rule.threshold:
            triggered = True
            message = f"Rate limit low: {log_payload.rate_limit_remaining} remaining"
        if triggered:
            create_alert_instance(rule, message, log_payload)
            publish_realtime_alert(rule, message)
```

### 3.5 Decorators & Permissions

#### 3.5.1 Custom `@whitelist()` Decorator (decorators.py)

Modeled after Insights' `@insights_whitelist`. Wraps `@frappe.whitelist()` with an explicit role check and consistent error response:

```python
# decorators.py
import frappe
from functools import wraps

def whitelist(role="System Manager", allow_guest=False, methods=("GET", "POST")):
    """Combined @frappe.whitelist + role guard."""
    def decorator(fn):
        @wraps(fn)
        @frappe.whitelist(allow_guest=allow_guest, methods=methods)
        def wrapper(*args, **kwargs):
            if not allow_guest and not frappe.session.user == "Guest":
                if not frappe.has_permission(doctype=None, ptype="read"):
                    frappe.throw("Not permitted", frappe.PermissionError)
            if role and not frappe.has_role(role):
                frappe.response["http_status_code"] = 403
                return {"message": f"Role {role} required", "http_status_code": 403}
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def validate_type(*expected_types):
    """Ensure first positional arg is one of the expected Python types."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if args and not isinstance(args[0], expected_types):
                frappe.throw(f"Expected {expected_types}, got {type(args[0])}")
            return fn(*args, **kwargs)
        return wrapper
    return decorator
```

Usage in API modules:

```python
# api/dashboard.py
from api_security_monitor.decorators import whitelist

@whitelist(role="System Manager")
def get_summary(period=24):
    ...
```

#### 3.5.2 Permission Hooks (permissions.py)

Modeled after Insights' `InsightsPermissions` class. Provides row-level permission filtering for DocTypes:

```python
# permissions.py
import frappe

DOCTYPES = {
    "Log Ingest Adapter",
    "Security Alert Rule",
    "Alert Instance",
    "AI Audit Assessment",
}

def get_permission_query_conditions(user):
    """Return conditions so non-System-Managers only see their own data."""
    if not user:
        user = frappe.session.user
    if "System Manager" in frappe.get_roles(user):
        return ""
    return f"""(`tabLog Ingest Adapter`.owner = {frappe.db.escape(user)}
        OR `tabSecurity Alert Rule`.owner = {frappe.db.escape(user)}
        OR `tabAlert Instance`.owner = {frappe.db.escape(user)}
        OR `tabAI Audit Assessment`.owner = {frappe.db.escape(user)})"""

def has_permission(doctype, ptype="read", user=None):
    """System Managers have full access; others have owner-scoped access."""
    if not user:
        user = frappe.session.user
    if "System Manager" in frappe.get_roles(user):
        return True
    return False  # Owner-scoped via query conditions
```

The `get_permission_query_conditions` function is registered in `hooks.py` for each DocType. This approach keeps permission logic centralized rather than scattered across hooks.py.

---

## 4. API Endpoint Mapping

| Prototype Route | Frappe Module and Method | Auth | Notes |
|---|---|---|---|
| `GET /api/dashboard/summary` | `api.dashboard.get_summary(period=24)` | System Manager | OpenSearch aggregation + Redis cache (5s TTL) |
| `GET /api/dashboard/charts` | `api.dashboard.get_charts(period=24)` | System Manager | OpenSearch date_histogram with dynamic bucket sizing |
| `GET /api/dashboard/breakdown` | `api.dashboard.get_breakdown(period=24)` | System Manager | Multi-aggregation query |
| `GET /api/logs` | `api.logs.query_logs(...)` | System Manager | 8 query params → OpenSearch bool query |
| `POST /api/logs/ingest` | `api.logs.ingest_logs()` | allow_guest=True | Validates X-Ingest-Token header; enqueues to worker |
| `GET /api/sources` | Frappe standard API on Log Ingest Adapter | System Manager | `frappe.get_list` |
| `POST /api/sources` | `api.sources.create_source()` | System Manager | Auto-generates secret_token |
| `PUT /api/sources/:id/status` | `api.sources.toggle_source()` | System Manager | Sets active/inactive |
| `DELETE /api/sources/:id` | `api.sources.delete_source()` | System Manager | |
| `GET /api/rules` | Frappe standard API on Security Alert Rule | System Manager | |
| `POST /api/rules` | Frappe standard API on Security Alert Rule | System Manager | |
| `PUT /api/rules/:id` | `api.rules.update_rule()` | System Manager | Toggle enabled or update fields |
| `DELETE /api/rules/:id` | Frappe standard API on Security Alert Rule | System Manager | |
| `GET /api/alerts` | Frappe standard API on Alert Instance | System Manager | |
| `POST /api/alerts/resolve` | `api.alerts.resolve_all()` | System Manager | |
| `POST /api/alerts/:id/resolve` | `api.alerts.resolve_one()` | System Manager | |
| `POST /api/simulation/config` | `api.simulation.update_config()` | System Manager | Updates App Settings Singleton |
| `POST /api/explain-error` | `api.ai_gemini.explain_error(log_id)` | System Manager | Reads log from OpenSearch by id |
| `POST /api/anomaly-scan` | `api.ai_gemini.run_anomaly_scan()` | System Manager | Fetches last 85 from OpenSearch; creates AI Audit Assessment + Alert Instance |
| `GET /api/anomaly-scan/history` | Frappe standard API on AI Audit Assessment | System Manager | |

---

## 5. Frontend Architecture

### 5.1 Directory Layout

```
api_security_monitor/frontend/
├── src/
│   ├── main.js                    # createApp + mount, provide shared services
│   ├── App.vue                    # Root layout: FrappeUIProvider + Suspense + router-view
│   ├── router.js                  # Vue Router + beforeEach auth guard
│   ├── style.css                  # frappe-ui CSS + Tailwind directives
│   ├── api/
│   │   └── index.js               # Frappe call() wrappers, shared fetch helpers
│   ├── pages/
│   │   ├── DashboardPage.vue      # Charts, breakdowns, anomaly trend
│   │   ├── LogsPage.vue           # Filters, log table, trace inspector
│   │   ├── AlertsPage.vue         # 3 tabs: triggered, rules, AI scanner
│   │   └── SourcesPage.vue        # Sim controls, source CRUD, ingest
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppSidebar.vue     # Nav + UTC clock + live status
│   │   │   └── SuspenseFallback.vue  # Full-page spinner for async route fallback
│   │   ├── dashboard/
│   │   │   └── MetricsCards.vue   # 4 KPI cards
│   │   ├── shared/
│   │   │   └── ...                # Reusable: EmptyState, ErrorBanner, etc.
│   ├── composables/
│   │   ├── useDashboard.js        # useCall wrappers for summary/charts/breakdown
│   │   ├── useLogs.js             # useCall wrappers for log queries + ingest
│   │   ├── useAlerts.js           # useCall wrappers for alerts + rules CRUD
│   │   └── useSources.js          # useCall wrappers for sources + simulation
│   └── stores/
│       ├── telemetry.js           # Pinia store (logs, alerts, realtime state)
│       └── sessionStore.js        # Pinia store (user session, auth, init)
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

The `api/index.js` module provides a thin wrapper over `useCall` with shared defaults (base URL, error handling). The `sessionStore.js` handles Frappe session initialization, login state, and is used by the router auth guard.

### 5.2 Technology Substitutions

| Prototype (React/TypeScript) | Frappe Target (Vue/JavaScript) |
|---|---|
| `lucide-react` | lucide CSS classes (`<span class="lucide-edit size-4" />`) |
| `recharts` (Area, Bar, Pie, Line) | `echarts` + `vue-echarts` |
| `@vitejs/plugin-react` | `@vitejs/plugin-vue` |
| `react` + `react-dom` | `vue` |
| `useState` + lift pattern | Pinia store |
| `useEffect`, `useRef` | `onMounted`, `watch`, `computed`, `ref` |
| `fetch('/api/...')` | `useCall({ url: '/api/method/...' })` |
| Direct socket.io | Frappe realtime (`frappe.realtime.on()`) |
| TypeScript (.tsx / .ts) | JavaScript (.vue / .js) |

### 5.3 frappe-ui Integration Rules

Use `frappe-ui` as the UI contract for the Frappe frontend. The app must follow these rules exactly:

1. **Pin the expected toolchain**
   - frappe-ui 0.1.x requires **Tailwind v3.4** (not v4) and **Vite 5** (not 6+).
   - Use `@vitejs/plugin-vue@^5` and `frappe-ui/vite` — never `@tailwindcss/vite`.
   - `vue-router` is required — `<Button>` injects `Symbol(router)` and warns without it.

2. **Bootstrap with both `FrappeUI` plugin and `FrappeUIProvider`**
   - `app.use(FrappeUI)` — registers the plugin (resource provider, etc.)
   - `<FrappeUIProvider>` at app root — mounts imperative dialog/toast portals.

3. **Icons are CSS classes, not Vue components**
   - Never install or import `lucide-vue-next`.
   - Render: `<span class="lucide-plus size-4" aria-hidden="true" />`.
   - For component `icon` props: `icon="lucide-edit"`.

4. **Prefer `useCall` for all Frappe backend calls**
   - Use `useCall({ url: '/api/method/...', params, method, immediate, onSuccess, onError })`.
   - Use `useCall` for mutations as well as reads.
   - For non-Frappe prototypes (e.g. Express backend), use `useFetch` from `@vueuse/core`.

5. **Use semantic tokens, not raw Tailwind palette**
   - `text-ink-gray-9` (primary), `text-ink-gray-5` (muted), `text-ink-red-3` (error).
   - `bg-surface-white` (page), `bg-surface-gray-1` (cards), `bg-surface-gray-2` (hover).
   - `border-outline-gray-1` (default borders).
   - Never use `text-gray-900`, `bg-white`, `border-gray-200`.

6. **Use the frappe-ui component vocabulary**
   - `Button`, `Dialog`, `Dropdown`, `FormControl`, `TextInput`, `Select`, `Badge`, `Alert`, `Tabs`, `TabButtons`, `ListView`, `Switch`, `Checkbox`, `DatePicker`, `DateRangePicker`, `FileUploader`, `Spinner`, `LoadingText`.
   - Imperative: `dialog.confirm()`, `dialog.prompt()`, `toast.success()`, `toast.error()`.
   - Do **not** hand-roll buttons, dialogs, selects, or modals.

7. **Keep data flow store-backed, but UI state local**
   - Pinia for cross-component state: logs, alerts, dashboard summaries, scan history, realtime.
   - `ref`/`computed` for form-local and transient UI state.
   - Avoid giant `v-if` trees; prefer small composable components.

### 5.4 Pinia Store Design

Two stores: `telemetry.js` (app data) and `sessionStore.js` (auth).

```javascript
// stores/sessionStore.js
import { defineStore } from 'pinia'
import { useCall } from 'frappe-ui'

export const useSessionStore = defineStore('session', {
  state: () => ({
    user: null,
    isLoggedIn: false,
    initialized: false,
  }),
  actions: {
    async init() {
      const { data, error } = await useCall({
        url: '/api/method/frappe.auth.get_logged_user',
        immediate: true,
      })
      if (error.value) {
        this.initialized = true
        return
      }
      this.user = data.value.message
      this.isLoggedIn = true
      this.initialized = true
    },
    async logout() {
      await useCall({ url: '/api/method/logout', method: 'POST' })
      this.user = null
      this.isLoggedIn = false
    },
  },
})
```

```javascript
// stores/telemetry.js
import { defineStore } from 'pinia'

export const useTelemetryStore = defineStore('telemetry', {
  state: () => ({
    logs: [],
    alerts: [],
    scanHistory: [],
    dashboardMetrics: {},
    dashboardCharts: {},
    dashboardBreakdown: {},
    sources: [],
    rules: [],
    isScanning: false,
    theme: localStorage.getItem('theme') || 'dark',
    realtimeReady: false
  }),
  actions: {
    async fetchDashboard() { /* useCall wrappers or fetch helper */ },
    async fetchLogs(filters) { /* query logs */ },
    async fetchSources() { /* load adapter list */ },
    async fetchRules() { /* load alert rules */ },
    async fetchAlerts() { /* load alert instances */ },
    async fetchScanHistory() { /* load AI audit assessments */ },
    toggleTheme() { /* swap dark/light + persist */ },
    initRealtime() { /* subscribe via frappe.realtime.on */ }
  }
})
```

### 5.5 Frontend Build Setup

Scaffold manually (do not use `npm create vite@latest` — its defaults are incompatible):

```bash
cd api_security_monitor
mkdir frontend && cd frontend
npm init -y
npm install vue vue-router pinia frappe-ui echarts vue-echarts
npm install -D \
  vite@^5 \
  @vitejs/plugin-vue@^5 \
  tailwindcss@^3.4 \
  postcss \
  autoprefixer \
  unplugin-icons \
  unplugin-auto-import \
  unplugin-vue-components \
  lucide-static \
  @iconify/json
```

### 5.6 Vite Config

```javascript
// frontend/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'

export default defineConfig({
  plugins: [
    frappeui({
      frappeProxy: false,
      jinjaBootData: false,
      buildConfig: false,
    }),
    vue(),
  ],
  optimizeDeps: {
    exclude: ['frappe-ui'],
    include: [
      'feather-icons',
      'tippy.js',
      'showdown',
      'engine.io-client',
      'socket.io-client',
      'debug',
    ],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/socket.io': { target: 'http://localhost:8000', ws: true }
    }
  }
})
```

### 5.7 PostCSS Config

```javascript
// frontend/postcss.config.js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

### 5.8 Tailwind Config

```javascript
// frontend/tailwind.config.js
import frappeUIPreset from 'frappe-ui/tailwind'

/** @type {import('tailwindcss').Config} */
export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
  ],
}
```

### 5.9 CSS Entry

```css
/* frontend/src/style.css */
@import 'frappe-ui/style.css';
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 5.10 App Bootstrap Pattern

```javascript
// frontend/src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { FrappeUI } from 'frappe-ui'
import { router } from './router'
import './style.css'
import App from './App.vue'

const app = createApp(App)
app.use(router)
app.use(createPinia())
app.use(FrappeUI)
app.mount('#app')
```

```vue
<!-- frontend/src/App.vue -->
<script setup>
import { FrappeUIProvider } from 'frappe-ui'
</script>

<template>
  <FrappeUIProvider>
    <router-view />
  </FrappeUIProvider>
</template>
```

```javascript
// frontend/src/router.js
import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Dashboard', component: () => import('./pages/DashboardPage.vue') },
    { path: '/logs', name: 'Logs', component: () => import('./pages/LogsPage.vue') },
    { path: '/alerts', name: 'Alerts', component: () => import('./pages/AlertsPage.vue') },
    { path: '/sources', name: 'Sources', component: () => import('./pages/SourcesPage.vue') },
  ],
})
```

### 5.11 Router Auth Guards

Add a `beforeEach` navigation guard to check session state before rendering any page. Modeled after Insights' guard pattern — redirects to Frappe login when unauthenticated:

```javascript
// frontend/src/router.js (extended)
import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from './stores/sessionStore'

const loginPage = `/login?redirect-to=${encodeURIComponent(window.location.pathname)}`

router.beforeEach(async (to, from, next) => {
  const session = useSessionStore()

  if (!session.initialized) {
    await session.init()
  }

  if (!session.isLoggedIn) {
    window.location.href = loginPage
    return
  }

  next()
})
```

The guard calls `session.init()` on first navigation, which fetches the logged-in user via `frappe.auth.get_logged_user`. If the user is not authenticated, the browser redirects to the standard Frappe login page with a `redirect-to` parameter so the user returns to the SPA after login.

### 5.12 Provide/Inject Shared Services

Register shared services at the app root so all components can access them without imports. Modeled after Insights' `provideDashboardProvider()` pattern:

```javascript
// frontend/src/main.js (extended)
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { FrappeUI } from 'frappe-ui'
import { router } from './router'
import './style.css'
import App from './App.vue'

const app = createApp(App)

// Provide shared services
app.provide('$dayjs', dayjs)
app.provide('$notify', {
  success: (msg) => toast.success(msg),
  error: (msg) => toast.error(msg),
  info: (msg) => toast.info(msg),
})

app.use(router)
app.use(createPinia())
app.use(FrappeUI)
app.mount('#app')
```

```vue
<!-- frontend/src/App.vue (extended with Suspense) -->
<script setup>
import { FrappeUIProvider } from 'frappe-ui'

const modules = import.meta.glob('./pages/*.vue')
</script>

<template>
  <FrappeUIProvider>
    <router-view v-slot="{ Component }">
      <Suspense>
        <component :is="Component" />
        <template #fallback>
          <div class="flex h-screen items-center justify-center">
            <Spinner class="size-8 text-ink-gray-5" />
          </div>
        </template>
      </Suspense>
    </router-view>
  </FrappeUIProvider>
</template>
```

Key services to provide:
- **`$dayjs`** — date formatting across dashboard time controls, log timestamps
- **`$notify`** — consistent toast notifications (success/error/info) via frappe-ui's imperative toast
- **`$utils`** — shared helpers (formatBytes, formatDuration, pluralize, etc.)

Components consume via `inject`:

```javascript
const $notify = inject('$notify')
const $dayjs = inject('$dayjs')
```

The `<Suspense>` wrapper allows async page components to show a centered spinner fallback while their `useCall` resources resolve. Each page component should export a `setup()` that returns a promise or use `<script setup>` with top-level `await`.

### 5.13 Data Access Pattern

Use object-style config with `useCall` for all Frappe backend calls. Never use raw `fetch` or `axios`.

#### Basic Pattern (useCall wrappers)

```javascript
// composables/useDashboard.js
import { useCall } from 'frappe-ui'

// Read (auto-fetches on mount)
export function useDashboardSummary(period = 24) {
  return useCall({
    url: '/api/method/api_security_monitor.api.dashboard.get_summary',
    params: { period },
    refetch: true,
    cacheKey: ['dashboard-summary', period],
  })
}

// Write (trigger on action)
export function useIngestLogs() {
  return useCall({
    url: '/api/method/api_security_monitor.api.logs.ingest_logs',
    method: 'POST',
    immediate: false,
    onSuccess: () => toast.success('Logs ingested'),
    onError: (err) => toast.error(err.message),
  })
}
```

#### Composable with Object.assign (modeled after Insights)

For composables that expose multiple reactive refs and methods, use the `Object.assign(state, { methods })` pattern. This keeps the return value flat (no nesting) and ensures refs are auto-unwrapped in templates:

```javascript
// composables/useAlerts.js
import { reactive, computed } from 'vue'
import { useCall } from 'frappe-ui'
import { useTelemetryStore } from '../stores/telemetry'

export function useAlerts() {
  const state = reactive({
    unresolvedCount: computed(() => useTelemetryStore().alerts.filter(a => !a.resolved).length),
    severityTheme: (sev) => ({ critical: 'red', warning: 'orange', info: 'blue' }[sev] || 'gray'),
  })

  async function resolveAll() {
    const { error } = await useCall({
      url: '/api/method/api_security_monitor.api.alerts.resolve_all',
      method: 'POST',
      immediate: false,
    })
    if (!error.value) {
      useTelemetryStore().fetchAlerts()
    }
  }

  return Object.assign(state, { resolveAll })
}
```

This pattern is preferred over returning `{ state, methods }` because:
- Template access is `unresolvedCount` not `state.unresolvedCount` (flatter)
- `Object.assign` merges reactive refs and functions at the top level
- Each composable remains focused on one domain (dashboard, logs, alerts, sources)

### 5.14 UI/UX Pattern Notes

- Keep the existing 6-component split and preserve the prototype's loading, empty, disabled, and error states.
- Use `frappe-ui` badges, alerts, buttons, dialogs, and form controls to replace custom React-style primitives.
- For the dashboard, keep the chart interactions and navigation behavior from the prototype: time window selector, date range picker, drill-down to LogViewer, and analyze actions on endpoints.
- For alerts, keep the 3-tab structure and the create/edit/toggle/delete flows.
- For source configuration, keep the simulation toggle, speed buttons, JSON/CSV ingest, and feedback banners.
- Form fields: one column, `FormControl` with `label`/`description`/`error`/`required`, submit buttons right-aligned.
- Empty states: centered layout with icon, message, and CTA button (never an empty table).
- Confirmations: use `dialog.confirm({ title, theme, onConfirm })` — never hand-roll confirm modals.
- Status badges: use `<Badge :label :theme variant="subtle" />` with a theme map.
- Loading: `<Button :loading>` for buttons, `<Spinner />` / `<LoadingText />` for inline placeholders.
- Dark mode: set `[data-theme="dark"]` on `<html>` — semantic tokens flip automatically. Test every screen.
- `<Suspense>`: wrap `<router-view>` in `<Suspense>` with a centered `<Spinner>` fallback. Page components with top-level `await` in `<script setup>` suspend automatically while `useCall` resources resolve.

---

## 6. Realtime WebSocket Flow

### Live Simulation → Alert Pipeline

```
Log ingested → index to OpenSearch → evaluate_rules_for_log()
    ↓ rule matches
create Alert Instance DocType
    ↓
frappe.publish_realtime("security_anomaly_triggered", alert_data)
    ↓
Frappe Node.js Socket.io server → Redis pub/sub → connected browsers
    ↓
Vue Pinia store receives event → unshift to alerts array + refresh metrics
```

### Anomaly Scan Pipeline

```
User clicks "Execute Gemini Security Scan"
    ↓
run_anomaly_scan() fetches last 85 logs from OpenSearch
    ↓
Sends aggregated log summary to Gemini API
    ↓
Parses response → creates AI Audit Assessment DocType
    ↓
If score > 40: creates AI Alert Instance DocType
    ↓
frappe.publish_realtime("security_scan_complete", report_data)
    ↓
Vue store receives event → updates scanHistory + alerts
```

---

## 7. Simulation Engine

### 7.1 Background Task

Registered in `hooks.py` scheduler_events as a cron job (default: every 1 minute).

```python
# tasks.py
def generate_simulated_logs():
    """Port of feedSingleLiveLog() from server.ts"""
    settings = frappe.get_single("API Security App Settings")
    if not settings.enable_live_simulation:
        return

    # Generate 1 log per task execution using same path/method templates
    # Inject same anomaly patterns:
    #   - ~12% error rate: 5% 500/429, 5% 401, 2% 404
    #   - Auth outage at hour 14 UTC (elevated 500s + latency)
    #   - Rate-limit spike every 25th log
    #   - Random 4% 503/404 noise, 8% 401 noise

    log = generate_log()  # uses same seeded sources + paths
    index_api_log(log)    # → OpenSearch
    evaluate_rules_for_log(log)
```

### 7.2 Seed Data (server.ts reference)

- **4 sources**: Auth Service (gateway), Billing Gateway (webhook), Catalog Engine (gateway), Data Collector (agent)
- **8 API paths**: `/api/v1/users/login` (POST), `/api/v1/users/profile` (GET), `/api/v1/billing/checkout` (POST), `/api/v1/billing/invoices` (GET), `/api/v1/products/list` (GET), `/api/v1/products/detail` (GET), `/api/v1/analytics/stream` (POST), `/api/v1/webhooks/stripe` (POST)
- **9 IPs**: `192.168.1.50`, `203.0.113.88`, `198.51.100.12`, `185.228.168.10`, `34.120.45.99`, `8.8.8.8`, `172.56.21.90`, `192.168.1.112`, `45.12.33.20`
- **6 User-Agents**: Chrome, Safari, Postman, curl, Android, Go-http-client
- **350 seed logs** distributed over 24h with injected anomaly patterns

---

## 8. Deployment Configuration

### 8.1 Site Config

```json
// sites/site1/common_site_config.json
{
  "opensearch_host": "localhost",
  "opensearch_port": 9200,
  "opensearch_user": "admin",
  "opensearch_password": "..."
}
```

### 8.2 Dependencies

Add to `api_security_monitor/requirements.txt`:
```
opensearch-py
```

### 8.3 Services Required

- MariaDB/PostgreSQL (Frappe's standard database)
- Redis (Frappe's cache + queue broker)
- OpenSearch (log storage + aggregation)
- RQ Worker (bench worker — for background ingestion tasks)
- Frappe Node.js Socket.io server (built-in, port 8000)

---

## 9. Implementation Order

### Phase 1: Frappe App Scaffolding

1. `bench new-app api_security_monitor`
2. Add `opensearch-py` to `requirements.txt`
3. Register app in site
4. `bench build && bench migrate`

### Phase 2: DocType Definitions

1. Create **API Security App Settings** (Singleton)
2. Create **Log Ingest Adapter**
3. Create **Security Alert Rule**
4. Create **Alert Instance**
5. Create **AI Audit Assessment**
6. Run `bench migrate`

### Phase 3: Backend Python Modules

1. `decorators.py` — `@whitelist(role)`, `@validate_type` custom decorators
2. `permissions.py` — `get_permission_query_conditions`, `has_permission` hooks
3. `opensearch_client.py` — `get_client()`, `ensure_index()`, `index_log()`
4. `utils.py` — `evaluate_rules_for_log()`, Redis caching helpers
5. `realtime.py` — `publish_alert()`, `publish_scan_complete()`
6. `api/dashboard.py` — `get_summary()`, `get_charts()`, `get_breakdown()`
7. `api/logs.py` — `query_logs()`, `ingest_logs()`
8. `api/sources.py` — CRUD + status toggle
9. `api/rules.py` — CRUD + toggle
10. `api/alerts.py` — list + resolve
11. `api/simulation.py` — config management
12. `api/ai_gemini.py` — `explain_error()`, `run_anomaly_scan()`
13. `tasks.py` — `generate_simulated_logs()`
14. `create fixtures/ directory` — seed data JSON (default sources, rules)
15. `install.py` — `after_migrate` seed function
16. `hooks.py` — scheduler + permission hooks + websocket registration + website route rules

### Phase 4: Rule Evaluation + Redis Caching

1. Implement evaluate_rules_for_log() in utils.py
2. Redis caching for active rules (30min TTL)
3. Redis caching for dashboard aggregates (5s TTL)
4. Invalidate cache on rule update/create/delete

### Phase 5: Simulation Engine

1. Port feedSingleLiveLog() to tasks.generate_simulated_logs()
2. Register cron schedule in hooks.py
3. Ensure idempotent log generation with anomaly injection

### Phase 6: Vue 3 Frontend

**6a. Bootstrap**

1. Scaffold: `package.json`, `vite.config.js`, `tailwind.config.js`, `postcss.config.js`, `src/style.css`, `index.html`
2. App bootstrap: `src/main.js` (FrappeUI plugin + provide `$dayjs`, `$notify`), `src/App.vue` (FrappeUIProvider + `<Suspense>` fallback), `src/router.js` (4 routes + `beforeEach` auth guard)
3. `src/api/index.js` — shared `useCall` wrapper with base URL and error handling defaults
4. `src/stores/sessionStore.js` — user session, `init()`, `logout()`

**6b. App Shell & Shared Components**

5. `src/components/layout/AppSidebar.vue` — nav tabs, UTC clock, live status, alert badge
6. `src/components/layout/SuspenseFallback.vue` — centered Spinner for async route loading
7. `src/components/dashboard/MetricsCards.vue` — 4 KPI cards
8. `src/components/shared/` — EmptyState, ErrorBanner, StatusBadge, etc.

**6c. Pinia Store**

9. `src/stores/telemetry.js` — logs, alerts, scan history, dashboard data, sources, rules, realtime scaffolding

**6d. Composables**

10. `src/composables/useDashboard.js` — `useCall` wrappers for summary/charts/breakdown (Object.assign pattern)
11. `src/composables/useLogs.js` — `useCall` wrappers for log queries + ingest + CSV
12. `src/composables/useAlerts.js` — `useCall` wrappers for alerts + rules CRUD
13. `src/composables/useSources.js` — `useCall` wrappers for sources + simulation config

**6e. Pages**

14. `src/pages/DashboardPage.vue` — charts (vue-echarts), breakdown tables, anomaly trend, time controls
15. `src/pages/LogsPage.vue` — filters, log table (ListView), trace inspector (Dialog), CSV export, Gemini explain
16. `src/pages/AlertsPage.vue` — 3-tab layout: triggered alerts, rules CRUD, AI scanner
17. `src/pages/SourcesPage.vue` — simulation controls, source CRUD, JSON/CSV ingest (FileUploader)

### Phase 7: Realtime WebSocket Integration

1. Wire frappe.publish_realtime() into alert creation flow
2. Wire frappe.publish_realtime() into anomaly scan completion
3. Pinia store event listeners (security_anomaly_triggered, security_scan_complete)

---

## 10. Verification Checklist

### 10.1 Backend Verification

- [ ] `bench new-app api_security_monitor` completes without errors
- [ ] `bench migrate` creates all 6 DocType tables
- [ ] `bench console` → `frappe.get_single("API Security App Settings")` returns singleton
- [ ] OpenSearch daily indices created on first write
- [ ] GET `/api/method/api_security_monitor.api.dashboard.get_summary` returns correct KPIs
- [ ] GET `/api/method/api_security_monitor.api.dashboard.get_charts` returns bucketed data
- [ ] GET `/api/method/api_security_monitor.api.dashboard.get_breakdown` returns source/status/endpoint breakdown
- [ ] Log query with search/source/status/method/latency/time filters returns filtered results
- [ ] POST log ingestion creates document in OpenSearch
- [ ] Rule evaluation triggers Alert Instance creation
- [ ] Rule evaluation with all 3 metric types (latency, status_code, rate_limit)
- [ ] Gemini explanation endpoint returns markdown (when API key set)
- [ ] Gemini anomaly scan creates AI Audit Assessment + Alert Instance (when score > 40)
- [ ] Simulation cron task runs and generates logs with anomaly patterns
- [ ] Simulation on/off + speed settings respected
- [ ] Source CRUD (create, read, update status, delete) on Log Ingest Adapter DocType
- [ ] Alert rule CRUD (create, read, update enabled, delete) on Security Alert Rule DocType
- [ ] Alert resolve (single + bulk) on Alert Instance DocType
- [ ] `@whitelist(role="System Manager")` returns 403 for non-System-Manager users
- [ ] `@whitelist(allow_guest=True)` on ingest endpoint accepts unauthenticated requests
- [ ] `get_permission_query_conditions` returns correct owner-scoped conditions for non-admin users
- [ ] `has_permission` returns True for System Manager, False for standard users
- [ ] Fixture seed data (default sources, rules) loads correctly on `bench migrate`
- [ ] `website_route_rules` serves SPA at `/api-security-monitor/` path
- [ ] `add_to_apps_screen` shows app in Frappe App Switcher

### 10.2 Frontend Verification

- [ ] Sidebar displays all 4 nav tabs with correct icons
- [ ] Sidebar shows live UTC clock updating every second
- [ ] Sidebar shows "Gateway Stream Live" indicator with pulsing dot
- [ ] Sidebar shows active alert badge count on Alerts tab
- [ ] MetricsCards show 4 cards with correct data and loading states
- [ ] MetricsCards color-code latency (green < 150ms, otherwise warning)
- [ ] MetricsCards color-code success rate (green ≥ 98%, amber < 98%)
- [ ] MetricsCards animate alert card when activeAlerts > 0
- [ ] Dashboard time window selector (2h / 24h / 3d) works
- [ ] Dashboard date range picker (From/To/Clear Lens) works
- [ ] Dashboard "Explore Logs for Timeframe" navigates to LogViewer with filters
- [ ] Dashboard Traffic Volume chart renders with success (green) and errors (red) areas
- [ ] Dashboard Latency chart renders as bars with click-to-filter
- [ ] Dashboard Status Code donut chart renders with correct colors
- [ ] Dashboard Endpoint table shows method badge, path, latency color-coded, error rate badge
- [ ] Dashboard "Analyze" button navigates to LogViewer with endpoint filter
- [ ] Dashboard AI Anomaly Score trend line chart renders
- [ ] Dashboard empty state for no scan history
- [ ] LogViewer search input filters by path/IP/id/userId
- [ ] LogViewer source dropdown populated from Log Ingest Adapter list
- [ ] LogViewer status dropdown with groups (2xx, 4xx, 5xx, 429)
- [ ] LogViewer method dropdown (All, GET, POST, PUT, DELETE)
- [ ] LogViewer min/max latency inputs
- [ ] LogViewer datetime-local start/end pickers with Reset button
- [ ] LogViewer log table shows status badge (color-coded), method badge, path, source, IP, latency (color-coded), timestamp
- [ ] LogViewer empty state when no logs match
- [ ] LogViewer Trace Inspector modal: shows all log metadata, headers, response body
- [ ] LogViewer Gemini "Explain Trace Cause" button works with loading spinner + error handling
- [ ] LogViewer CSV export with preview modal + download
- [ ] AlertsPanel tab switching works (Triggered / Rules & Policies / AI Scanner)
- [ ] AlertsPanel Triggered tab: alert cards with severity styling, resolve buttons, empty state
- [ ] AlertsPanel Rules tab: card layout, enable/disable toggle, delete, create form
- [ ] AlertsPanel AI Scanner: scan trigger button, loading state, score gauge (color-coded), markdown report, history list
- [ ] SourceConfig simulation Active/Paused toggle
- [ ] SourceConfig simulation speed buttons (Slow/Medium/Extreme)
- [ ] SourceConfig simulation state/info boxes
- [ ] SourceConfig source CRUD with add form, enable/disable, delete
- [ ] SourceConfig JSON paste area with DDoS/SlowDB/DataLoad presets
- [ ] SourceConfig CSV file upload with parsing
- [ ] SourceConfig success/error feedback banners
- [ ] Theme toggle works (dark/light) and persists to localStorage
- [ ] All loading spinners, empty states, error banners render correctly
- [ ] All color-coded thresholds match prototype exactly
- [ ] Router `beforeEach` guard calls `session.init()` on first navigation
- [ ] Router redirects to Frappe login page when `session.isLoggedIn` is false
- [ ] `<Suspense>` fallback spinner renders during async page component load
- [ ] `provide('$dayjs', ...)` and `provide('$notify', ...)` accessible via `inject` in child components
- [ ] `sessionStore` initializes, populates `user`, and sets `isLoggedIn=true` on app load
- [ ] Composable using `Object.assign(state, { methods })` returns flat reactive properties at top level

### 10.3 Realtime Verification

- [ ] Alert creation triggers `frappe.publish_realtime("security_anomaly_triggered")`
- [ ] Frontend receives `security_anomaly_triggered` event and updates alerts array
- [ ] Anomaly scan completion triggers `frappe.publish_realtime("security_scan_complete")`
- [ ] Frontend receives `security_scan_complete` event and updates scanHistory
- [ ] Socket.io connection established on page load (Frappe default `/socket.io/`)
- [ ] `frappe.realtime.on('security_anomaly_triggered')` listener registered and receives events

### 10.4 Integration Verification

- [ ] Complete flow: simulation → log generated → OpenSearch indexed → rules evaluated → alert created → realtime pushed → frontend updated
- [ ] Complete flow: user triggers anomaly scan → OpenSearch queried → Gemini called → DocType created → realtime pushed → frontend updated
- [ ] Complete flow: user ingests CSV → parsed → OpenSearch indexed → rules evaluated → alerts created
- [ ] Complete flow: dashboard filters → OpenSearch queried → results displayed
- [ ] Complete flow: trace inspection → Gemini explanation → markdown displayed

### 10.5 Edge Cases

- [ ] Empty OpenSearch cluster (no indices yet) — dashboard returns graceful zero-state
- [ ] Gemini API key not configured — endpoints return user-friendly message
- [ ] Invalid CSV format — clear error message shown
- [ ] Empty JSON payload — clear error message shown
- [ ] Very large time range (>72h) — chart auto-buckets to daily intervals
- [ ] Very small time range (<6min) — chart auto-buckets to 10-second intervals
- [ ] All sources disabled — simulation skips inactive sources
- [ ] All rules disabled — no alerts generated
- [ ] 2000+ logs in OpenSearch — query limit/pagination works
- [ ] Concurrent dashboard requests — Redis caching prevents OpenSearch overload
