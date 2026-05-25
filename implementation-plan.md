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

### 8.1 Docker Environment

The development environment uses `docker.io/frappe/bench:latest` (Frappe v16) with the following services:

| Service | Image | Notes |
|---|---|---|
| frappe | `frappe/bench:latest` | Bench CLI + Python 3.14 pre-installed |
| mariadb | `mariadb:11.8` | Database server |
| redis-cache | `redis:alpine` | Cache |
| redis-queue | `redis:alpine` | Queue + Socket.io broker |
| opensearch | `opensearchproject/opensearch:3` | Log storage + analytics |

**OpenSeach 3.x requires:**
- `DISABLE_SECURITY_PLUGIN=true` for dev (HTTP, no TLS)
- `OPENSEARCH_INITIAL_ADMIN_PASSWORD=admin` (required since v2.12)
- `discovery.type=single-node` for single-node dev cluster

Access the Frappe site via the `Host` header since the site is named `apim.localhost`:
```bash
curl -s -H "Host: apim.localhost" http://localhost:8000/login
```

### 8.2 Dependencies

Frappe v16 apps use `pyproject.toml` (not `requirements.txt`). Add Python packages to `[project] dependencies`:

```toml
# pyproject.toml
[project]
dependencies = [
    "opensearch-py",
]
```

Frontend dependencies go in `frontend/package.json`.

### 8.3 Services Required

- MariaDB (Frappe's standard database, containerized)
- Redis × 2 (cache + queue broker, containerized)
- OpenSearch 3.x (log storage + aggregation, containerized)
- Frappe Node.js Socket.io server (built-in, port 9000 inside container)

---

## 9. Implementation Order

### Phase 0: Docker Environment Setup

1. Create `.env` file with MariaDB/Redis/OpenSearch connection settings
2. Add OpenSearch 3.x service to `docker-compose.yml` (with `DISABLE_SECURITY_PLUGIN=true`, `OPENSEARCH_INITIAL_ADMIN_PASSWORD`)
3. `docker compose up -d`
4. Verify all 5 containers healthy: `docker compose ps`
5. Inside the frappe container, the bench is pre-configured at `/workspace/development/armure-apim/`
6. `bench build` to compile existing assets
7. `bench new-app armure_apim_sentinel` (interactive — pipe defaults via `echo -e`)
8. `bench --site apim.localhost install-app armure_apim_sentinel`
9. Start dev server: `bench serve --port 8000`
10. Add `opensearch-py` to `pyproject.toml` `[project] dependencies`

> **Note:** Bench 5.x (shipped with `frappe/bench:latest`) does NOT support `--title`/`--description` flags. Use `echo -e` to pipe responses:
> ```bash
> echo -e 'Armure APIM Sentinel\nDescription...\nArmure Suite\ndevelopment@armure.in\nmit\nn' | bench new-app armure_apim_sentinel
> ```
> Bench 6+ supports silent mode flags: `bench new-app app_name --title "..." --description "..." --publisher "..." --email "..." --license "mit"`

### Phase 1: Frappe App Scaffolding

1. Create directory structure (`api/`, `fixtures/`, `public/js/`)
2. Write `hooks.py` with all configuration entries
3. Write `__init__.py`, `install.py`, `uninstall.py`, `doc_events.py`
4. Run `bench migrate` to validate hooks

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

---

## 11. Enhancements — Richer Rule Criteria

### 11.1 Motivation

The current `Security Alert Rule` DocType supports only a single numeric threshold check (`latency > 800`, `status_code > 499`, `rate_limit < 5`) evaluated against **every** ingested log. Users cannot restrict rules by HTTP method, path pattern, IP range, user-agent, payload size, or status code range. There is also no windowed / count-based evaluation (e.g., "trigger if more than 10 POST errors happen in 5 minutes").

### 11.2 New Security Alert Rule Fields

#### API Selection / Filtering (decide *which* logs to evaluate)

| Field | Type | Default | Purpose |
|---|---|---|---|
| `filter_method` | Select | `Any` | Restrict to one HTTP method: `Any`, `GET`, `POST`, `PUT`, `DELETE`, `PATCH` |
| `filter_path_pattern` | Data | `""` | Glob or regex pattern. Empty = any path. Glob uses `fnmatch` (`/api/v1/billing/*`). If starts with `re:` prefix, treated as regex (`re:^/api/v1/users/\d+$`). |
| `filter_path_search_type` | Select | `glob` | `glob` or `regex` — determines how `filter_path_pattern` is matched |
| `filter_source` | Link → Log Ingest Adapter | `""` | Restrict to one source channel. Empty = any source |
| `filter_ip_range` | Data | `""` | Comma-separated list of CIDR notations or single IPs (`10.0.0.0/8,192.168.1.50`) |
| `filter_user_agent_pattern` | Data | `""` | Glob or regex on User-Agent. Empty = any UA. Same `re:` prefix convention |
| `filter_user_agent_search_type` | Select | `glob` | `glob` or `regex` |
| `filter_min_payload` | Int | `0` | Minimum payload size in bytes. `0` = no minimum |
| `filter_max_payload` | Int | `0` | Maximum payload size in bytes. `0` = no maximum |
| `filter_status_min` | Int | `0` | Min HTTP status to consider (e.g., `400` for client errors+). `0` = no minimum |
| `filter_status_max` | Int | `0` | Max HTTP status. `0` = no maximum |

#### Enhanced Evaluation (decide *how* to trigger)

| Field | Type | Default | Purpose |
|---|---|---|---|
| `count_based` | Check | `0` (off) | If enabled, use a rolling count over `evaluation_window` instead of per-log check |
| `evaluation_window` | Int (minutes) | `5` | Sliding window size for count-based rules |
| `min_trigger_count` | Int | `1` | Minimum number of matching logs in the window to trigger an alert |
| `group_by` | Select | `none` | Aggregation dimension for count rules: `none`, `source`, `ip`, `path`, `method` |

### 11.3 Updated Rule Engine

The `evaluate_rules_for_log()` function gains a filter pipeline before the existing metric check:

```
for each rule:
  1. FILTER PIPELINE (all filters are AND-ed)
     - filter_method: skip if log.method doesn't match (when not "Any")
     - filter_path_pattern: fnmatch or re.match against log.path
     - filter_source: skip if log.source != filter_source
     - filter_ip_range: ipaddress.ip_address(log.ip) in any CIDR
     - filter_user_agent_pattern: fnmatch or re.match against log.userAgent
     - filter_min_payload: skip if log.payloadSize < filter_min_payload
     - filter_max_payload: skip if log.payloadSize > filter_max_payload
     - filter_status_min: skip if log.status < filter_status_min
     - filter_status_max: skip if log.status > filter_status_max

  2. If any filter fails → skip to next rule

  3. EVALUATION
     a) If count_based is OFF:
        - Apply metric+condition+threshold check (existing logic)
     b) If count_based is ON:
        - Build Redis key: "rule_count:{rule_name}:{group_by_value}"
        - INCR the key, set EXPIRE to evaluation_window seconds
        - If current count >= min_trigger_count → trigger alert
        - Deduplicate: set a separate Redis flag "rule_alerted:{rule_name}:{group_by_value}"
          with TTL = evaluation_window to prevent repeated alerts
```

### 11.4 Backward Compatibility

All new fields have empty/zero/default values. Existing rules with no filters set match all logs (same behavior as today). The `count_based` field defaults to `0` (off), so existing rules evaluate per-log as before.

### 11.5 Frontend — Updated Rule Form

Add collapsible "Advanced API Selection" section between the Condition Target Metric and Trigger Criteria fields in the rule creation form with inputs for all filter fields. The rule display card shows active filter criteria as small badges below the metric threshold.

---

## 12. Notification Engine

### 12.1 Motivation

Currently, alerts are only delivered in-app via Frappe WebSockets (`publish_alert` → `security_anomaly_triggered` event). There is no mechanism to route alerts to external notification channels (Email, Slack, Discord, SMS, Teams, Whatsapp, Telegram). Operators must be logged into the Frappe dashboard to see alerts, which limits the app's utility as a real-time monitoring tool.

A notification engine is required to:
- Route triggered alerts to one or more external channels based on rule-channel mappings
- Support configurable channels with channel-specific parameters (webhook URLs, API keys, SMTP config, etc.)
- Queue notifications asynchronously with retry on failure
- Maintain an audit log of all notifications sent

### 12.2 New DocTypes

#### 12.2.1 Notification Channel

| Field | Type | Notes |
|---|---|---|
| `channel_name` | Data | Unique, required, autoname |
| `channel_type` | Select | `discord\nemail\nslack\nsms\nteams\nwhatsapp\ntelegram\nhttp` |
| `is_active` | Check | Default 1 |
| `rate_limit_per_minute` | Int | Default 60 — max messages per minute through this channel |
| `config_json` | Code (JSON) | Channel-specific configuration payload |

**Channel-type-specific config fields** stored in `config_json`:

| Channel Type | Config Fields |
|---|---|
| `discord` | `{"webhook_url": "..."}` |
| `email` | `{"smtp_host": "...", "smtp_port": 587, "smtp_user": "...", "smtp_password": "...", "from_email": "...", "to_emails": ["..."], "use_tls": true}` |
| `slack` | `{"webhook_url": "..."}` or `{"bot_token": "...", "channel_id": "..."}` |
| `teams` | `{"webhook_url": "..."}` |
| `telegram` | `{"bot_token": "...", "chat_id": "..."}` |
| `whatsapp` | `{"api_endpoint": "...", "api_key": "...", "phone_number_id": "...", "to_number": "..."}` |
| `sms` | `{"provider": "twilio", "account_sid": "...", "auth_token": "...", "from_number": "...", "to_number": "..."}` |
| `http` | `{"url": "...", "method": "POST", "headers": {...}, "template": "..."}` |

#### 12.2.2 Security Alert Rule Notification (Child Table)

A child table DocType added to `Security Alert Rule` via a Table field `notifications`:

| Field | Type | Notes |
|---|---|---|
| `channel` | Link → Notification Channel | Required |
| `enabled` | Check | Default 1 |

This creates a many-to-many relationship between rules and channels.

#### 12.2.3 Notification Queue Item

| Field | Type | Notes |
|---|---|---|
| `title` | Data | Notification title |
| `severity` | Select | `info\nwarning\ncritical` |
| `payload` | Code (JSON) | Full notification payload |
| `channel` | Link → Notification Channel | Target channel |
| `alert_instance` | Link → Alert Instance | The alert that triggered this |
| `rule` | Link → Security Alert Rule | Rule that triggered it |
| `status` | Select | `pending\nsending\nsent\nfailed\nretrying` |
| `retry_count` | Int | Default 0, max 3 |
| `last_error` | Small Text | Error message from last attempt |
| `next_retry_at` | Datetime | When to retry |
| `sent_at` | Datetime | When successfully sent |
| `created_at` | Datetime | Default Now |

#### 12.2.4 Notification Log

| Field | Type | Notes |
|---|---|---|
| `title` | Data | Notification title |
| `channel` | Link → Notification Channel | |
| `channel_type` | Read-only Data | Copied from channel at send time |
| `severity` | Select | |
| `rule` | Link → Security Alert Rule | |
| `alert_instance` | Link → Alert Instance | |
| `status` | Select | `sent\nfailed\nretried` |
| `response` | Code (JSON) | API response from channel |
| `error_message` | Small Text | |
| `attempts` | Int | Total attempts made |
| `sent_at` | Datetime | |
| `created_at` | Datetime | Default Now |

### 12.3 New Python Modules

#### 12.3.1 `notification/adapter_base.py` — Abstract Adapter Interface

```python
from abc import ABC, abstractmethod

class NotificationAdapter(ABC):
    @abstractmethod
    def send(self, payload: dict, config: dict) -> dict:
        """
        Send notification through the channel.
        Returns: {'success': bool, 'response': ..., 'error': ...}
        """
        pass

    @classmethod
    @abstractmethod
    def validate_config(cls, config: dict) -> list[str]:
        """
        Validate channel-specific config.
        Returns list of error messages (empty = valid).
        """
        pass
```

#### 12.3.2 `notification/adapters/` — Concrete Adapters

| File | Adapter Class | Channel | Key Config |
|---|---|---|---|
| `adapters/discord.py` | `DiscordAdapter` | Discord | `webhook_url` |
| `adapters/email.py` | `EmailAdapter` | Email | `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`, `from_email`, `to_emails`, `use_tls` |
| `adapters/slack.py` | `SlackAdapter` | Slack | `webhook_url` |
| `adapters/teams.py` | `TeamsAdapter` | Microsoft Teams | `webhook_url` |
| `adapters/telegram.py` | `TelegramAdapter` | Telegram | `bot_token`, `chat_id` |
| `adapters/whatsapp.py` | `WhatsAppAdapter` | WhatsApp (Meta Cloud API) | `api_endpoint`, `api_key`, `phone_number_id`, `to_number` |
| `adapters/sms.py` | `SMSAdapter` | SMS | `provider`, `account_sid`, `auth_token`, `from_number`, `to_number` |
| `adapters/http.py` | `HTTPAdapter` | Generic HTTP | `url`, `method`, `headers`, `template` |

Each adapter implements `send(payload, config)` and `validate_config(config)`. The `send()` method returns `{'success': True/False, 'response': ..., 'error': ...}`.

Email adapter uses Frappe's built-in `frappe.sendmail` if SMTP is not configured, otherwise uses its own SMTP connection from the channel config.

SMS/Telegram/WhatsApp adapters can be stubs that log to `frappe.logger()` with a "not implemented" warning.

#### 12.3.3 `notification/__init__.py` — Factory + Dispatcher

```python
def get_adapter(channel_type: str) -> NotificationAdapter:
    """Factory: returns the correct adapter for channel_type"""

def dispatch_notification(alert_doc, rule_name: str):
    """
    Called when an Alert Instance is created.
    1. Query rule's child table `notifications` for enabled channels
    2. For each mapped channel, create a Notification Queue Item
    3. Enqueue `send_queued_notification` for each item via frappe.enqueue
    """
```

#### 12.3.4 `notification/queue.py` — Queue Processing + Retry

```python
def send_queued_notification(queue_item_name: str):
    """
    - Fetch Notification Queue Item
    - Set status = 'sending'
    - Fetch channel config
    - Resolve adapter via get_adapter(channel_type)
    - Build payload from template / alert data
    - Call adapter.send(payload, config)
    - On success: status = 'sent', create Notification Log, record response
    - On failure: increment retry_count, set status = 'retrying'/'failed',
      set next_retry_at, log error in Notification Log
    """

def retry_failed_notifications():
    """
    Scheduled cron task (every 5 minutes):
    - Find items with status='retrying', retry_count < 3, next_retry_at <= now
    - Enqueue send_queued_notification for each
    """

def _enforce_rate_limit(channel_name: str, max_per_minute: int) -> bool:
    """
    Redis-based rate limiter using sliding window counter.
    Returns True if message is allowed, False if rate-limited.
    """
```

### 12.4 Integration Points

#### 12.4.1 doc_events.py

Add `doc_events` entry for `Alert Instance`:

```python
"Alert Instance": {
    "after_insert": "armure_apim_sentinel.notification.dispatch_notification"
}
```

Alternatively, call `dispatch_notification()` directly from `tasks.py` right after `frappe.new_doc("Alert Instance").insert()` to avoid the document event overhead. The plan is to wire it in `tasks.py` for reliability.

#### 12.4.2 hooks.py

1. Add scheduler cron for retry:
```python
scheduler_events = {
    "cron": {
        "*/1 * * * *": ["armure_apim_sentinel.tasks.generate_simulated_logs"],
        "*/5 * * * *": ["armure_apim_sentinel.notification.queue.retry_failed_notifications"],
    }
}
```

2. Add permission hooks for the 4 new DocTypes:
```python
permission_query_conditions = {
    ...
    "Notification Channel": "armure_apim_sentinel.permissions.get_permission_query_conditions",
    "Notification Queue Item": "armure_apim_sentinel.permissions.get_permission_query_conditions",
    "Notification Log": "armure_apim_sentinel.permissions.get_permission_query_conditions",
}

has_permission = {
    ...
    "Notification Channel": "armure_apim_sentinel.permissions.has_permission",
    "Notification Queue Item": "armure_apim_sentinel.permissions.has_permission",
    "Notification Log": "armure_apim_sentinel.permissions.has_permission",
}
```

3. Add the new `Notification` module to `modules.txt` (or include as a sub-module).

#### 12.4.3 install.py — Seed Data

Seed two notification channels:
- "Email Alert" — type=email, enabled, default SMTP config
- "Slack Alert" — type=slack, enabled, placeholder webhook URL

#### 12.4.4 Security Alert Rule JSON

Add child table field `notifications` to the Security Alert Rule DocType:
```json
{
    "fieldname": "notifications",
    "fieldtype": "Table",
    "label": "Notification Channels",
    "options": "Security Alert Rule Notification"
}
```

Update `field_order` to place it after `section_evaluation` / `group_by`.

### 12.5 API Endpoints (`api/notifications.py`)

| Endpoint | Method | Purpose |
|---|---|---|
| `list_channels` | GET | List all Notification Channels |
| `create_channel` | POST | Create channel (validates config via adapter) |
| `toggle_channel` | POST | Activate/deactivate channel |
| `delete_channel` | POST | Delete channel |
| `test_channel` | POST | Send test notification through a channel |
| `list_queue` | GET | View pending/failed notification queue items |
| `retry_queue_item` | POST | Manually retry a single queued item |
| `list_notification_logs` | GET | Paginated notification audit log |

### 12.6 Notification Flow

```
Log ingested → rule evaluation → Alert Instance created
    ↓
dispatch_notification()
    ↓ query rule → Security Alert Rule Notification (child table)
    ↓ for each enabled channel:
    ↓
Create Notification Queue Item (status=pending)
    ↓ frappe.enqueue("send_queued_notification", queue_item_name)
    ↓
send_queued_notification()
    ↓
1. Rate limit check (Redis sliding window)
2. Resolve adapter from channel type
3. Build payload from alert data + channel template
4. adapter.send(payload, config)
    ├── Success → Notification Log (status=sent), Queue Item (status=sent)
    └── Failure → Queue Item (status=retrying/failed, retry_count++),
                   Notification Log (status=failed/retried)
    ↓ retry cron (every 5 min)
retry_failed_notifications() → re-enqueue items with retry_count < 3
```

### 12.7 Frontend — Notification Management Page

A new Vue page at route `/api-security-monitor/notifications` with three tabs:

**Tab 1: Channels** — Card list of configured notification channels.
- Each card shows: channel name, type badge, active status toggle, last test result
- "Add Channel" button opens a form dialog
- Form: channel name + type selector → config fields rendered dynamically per type
- Config validation hint from adapter (shown inline)
- "Test" button on each channel sends a test notification

**Tab 2: Queue** — Table of pending/failed queue items.
- Columns: title, channel, status badge, retry count, next retry, created at
- "Retry" button on failed items
- Filter by status (pending/sending/sent/failed/retrying)

**Tab 3: Logs** — Filterable audit log of sent notifications.
- Columns: title, channel, channel type, severity, status, attempts, sent at, response preview
- Expandable row showing full response JSON

**Navigation**: Add a "Notifications" link to the sidebar (AppSidebar.vue).

### 12.8 Implementation Order

| Step | Description |
|---|---|
| 12.8.1 | Create `notification/adapter_base.py` — abstract base class |
| 12.8.2 | Implement `DiscordAdapter`, `SlackAdapter`, `EmailAdapter`, `HTTPAdapter` |
| 12.8.3 | Create stub adapters: TeamsAdapter, TelegramAdapter, WhatsAppAdapter, SMSAdapter |
| 12.8.4 | Create `Notification Channel` DocType JSON + Python stub |
| 12.8.5 | Create `Security Alert Rule Notification` child DocType |
| 12.8.6 | Add child table `notifications` to `Security Alert Rule` JSON |
| 12.8.7 | Create `Notification Queue Item` DocType |
| 12.8.8 | Create `Notification Log` DocType |
| 12.8.9 | Run `bench migrate` |
| 12.8.10 | Implement `notification/__init__.py` — factory + `dispatch_notification()` |
| 12.8.11 | Implement `notification/queue.py` — `send_queued_notification()`, `retry_failed_notifications()`, rate limiter |
| 12.8.12 | Wire dispatch into `tasks.py` after Alert Instance creation |
| 12.8.13 | Add retry cron + permission hooks to `hooks.py` |
| 12.8.14 | Create `api/notifications.py` — all 8 endpoints |
| 12.8.15 | Update `install.py` — seed 2 channels (Email + Slack) |
| 12.8.16 | Build frontend: NotificationsPage.vue (3 tabs + sidebar link) |
| 12.8.17 | Add Notifications route to `router.js` |
| 12.8.18 | Run `bench migrate` + `bench build --app armure_apim_sentinel` + integration test |

### 12.9 Rate Limiting Strategy

Per-channel rate limiting is enforced using a Redis sorted set sliding window:

```python
def _enforce_rate_limit(channel: str, max_per_minute: int) -> bool:
    now = time.time()
    key = f"rate_limit:{channel}"
    pipe = frappe.cache().redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - 60)  # remove entries older than 60s
    pipe.zcard(key)                           # count in window
    pipe.zadd(key, {str(now): now})           # add current request
    pipe.expire(key, 60)                      # ensure TTL
    _, count, _, _ = pipe.execute()
    return count <= max_per_minute
```

### 12.10 Adapter Template System

Each channel adapter can define a default notification template. The `HTTPAdapter` allows a user-defined `template` field in `config_json` using a simple `{key}` substitution syntax:

```
Template: "Alert {severity}: {title}\nRule: {rule}\nMessage: {message}"
Variables available: severity, title, rule, message, timestamp, channel, rule_url, alert_details
```

This template is rendered with the alert data before being sent.

For Discord/Slack, the template renders into the message content field. For Email, it renders the email body. For HTTP, it renders the request body (or can be JSON with template substitution).

### 12.11 Verification Checklist

- [ ] Notification Channel CRUD works (create, read, update, delete)
- [ ] Validate config via adapter returns errors for missing required fields
- [ ] Test notification sends correctly for each adapter
- [ ] New Alert Instance triggers dispatch to mapped channels
- [ ] Queue item created with status=pending
- [ ] `send_queued_notification` processes queue items correctly
- [ ] Failed sends increment retry_count, set next_retry_at
- [ ] Retry cron picks up failed items and re-enqueues
- [ ] After 3 failures, status set to "failed" with final error
- [ ] Rate limiter prevents exceeding per-minute threshold
- [ ] Notification Log captures all sends (success + failure)
- [ ] Notification Log can be filtered and searched
- [ ] Frontend: channels tab lists/add/delete/test works
- [ ] Frontend: queue tab shows pending/failed items with retry
- [ ] Frontend: logs tab shows audit trail with expandable rows
- [ ] Frontend: sidebar shows "Notifications" link
- [ ] Existing alerts flow unchanged when no channels configured
- [ ] Rule-card shows linked channels count/badges
- [ ] Many-to-many mapping: one rule → multiple channels, one channel → multiple rules
