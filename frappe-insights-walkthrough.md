# Frappe Insights — Reference App Walkthrough

## Purpose

This document extracts architectural patterns, coding conventions, and Frappe ecosystem practices from the real-world `frappe/insights` app (an open-source BI tool). Use it as a reference when building the `api_security_monitor` frontend.

The Insights app uses the older `createDocumentResource` / `createResource` API from frappe-ui. This walkthrough describes those patterns for reference, but **recommends the newer `useCall` / `useList` / `useDoc` composables** for new code. See the [frappe-ui-walkthrough.md](./frappe-ui-walkthrough.md) for the recommended API and [COMPONENTS.md → Data & resources](./frappe-reference/frappe-ui/skills/frappe-ui/COMPONENTS.md) for the full `useCall` reference.

## Source of truth

This walkthrough is based on the Insights app at `frappe-reference/insights/`.

---

## 1. Backend Architecture (Python / Frappe Framework)

### 1.1 Module Organization

Backend code lives under `insights/insights/` with a parallel `api/` module for whitelisted endpoints:

```
insights/
└── insights/
    ├── __init__.py
    ├── hooks.py              # App metadata, permissions, scheduler, routes
    ├── api/                  # Whitelisted endpoint modules
    │   ├── __init__.py       # get_user_info, get_app_version, file import
    │   ├── dashboards.py
    │   ├── queries.py
    │   ├── data_sources.py
    │   ├── alerts.py
    │   ├── data_store.py
    │   ├── home.py
    │   └── ...
    ├── permissions.py        # Custom permission query conditions
    ├── decorators.py         # @insights_whitelist, @validate_type, @check_role
    ├── utils.py
    ├── config/
    └── fixtures/
```

**Rule:** One API module per domain. Each file groups related endpoints (dashboard CRUD, query execution, source management, etc.).

### 1.2 Custom Decorator: `@insights_whitelist`

A convenience decorator that chains `@frappe.whitelist()` with role checking:

```python
# insights/decorators.py
def insights_whitelist(*args, role="Insights User", **kwargs):
    def decorator(function):
        @wraps(function)
        @frappe.whitelist(*args, **kwargs)
        @check_role(role)
        def wrapper(*args, **kwargs):
            return function(*args, **kwargs)
        return wrapper
    return decorator
```

Usage:

```python
from insights.decorators import insights_whitelist, validate_type

@insights_whitelist()
def get_dashboard_list():
    return frappe.get_list("Insights Dashboard", fields=["name", "title", ...])

@insights_whitelist()
@validate_type
def create_dashboard(title: str):
    dashboard = frappe.get_doc({"doctype": "Insights Dashboard", "title": title})
    dashboard.insert()
    return {"name": dashboard.name, "title": dashboard.title}
```

**Pattern:** Default role is `"Insights User"`, override with `@insights_whitelist(role="Insights Admin")` for admin-only endpoints.

### 1.3 `@validate_type` Decorator

Runtime type enforcement using `inspect` signatures:

```python
def validate_type(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        annotated_types = {
            k: v.annotation for k, v in sig.parameters.items()
            if v.annotation != inspect._empty
        }
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        for arg_name, arg_value in bound_args.arguments.items():
            if (
                arg_name in annotated_types
                and arg_value is not None
                and not isinstance(arg_value, annotated_types[arg_name])
            ):
                raise TypeError(...)
        return func(*args, **kwargs)
    return wrapper
```

### 1.4 Endpoint Patterns

**Simple list:**

```python
@insights_whitelist()
def get_dashboard_list():
    return frappe.get_list(
        "Insights Dashboard",
        fields=["name", "title", "modified", "_liked_by"],
        order_by="creation desc",
    )
```

**Frappe Query Builder (QB) for complex queries (joins, aggregations):**

```python
@insights_whitelist()
def get_dashboard_options(chart: str):
    Dashboard = frappe.qb.DocType("Insights Dashboard")
    DashboardItem = frappe.qb.DocType("Insights Dashboard Item")

    return (
        frappe.qb.from_(Dashboard)
        .left_join(DashboardItem)
        .on(Dashboard.name == DashboardItem.parent)
        .select(Dashboard.name.as_("value"), Dashboard.title.as_("label"))
        .where(DashboardItem.chart != chart)
        .groupby(Dashboard.name)
        .run(as_dict=True)
    )
```

**Create a new DocType record:**

```python
@insights_whitelist()
def create_dashboard(title: str):
    dashboard = frappe.get_doc({"doctype": "Insights Dashboard", "title": title})
    dashboard.insert()
    return {"name": dashboard.name, "title": dashboard.title}
```

**Public (unauthenticated) endpoints:**

```python
@frappe.whitelist(allow_guest=True)
@validate_type
def pivot(data: list[dict], public_key: str | None = None):
    # validate public_key, then execute
```

### 1.5 hooks.py Configuration

Key registrations in `hooks.py`:

```python
# Permissions — per-DocType query conditions and doc-level checks
permission_query_conditions = {
    "Insights Data Source v3": "insights.permissions.get_permission_query_conditions",
    "Insights Dashboard v3": "insights.permissions.get_permission_query_conditions",
    ...
}
has_permission = {
    "Insights Data Source v3": "insights.permissions.has_doc_permission",
    ...
}

# Scheduler events
scheduler_events = {
    "all": ["insights.insights.doctype.insights_alert.insights_alert.send_alerts"],
    "daily": ["insights.api.data_store.sync_tables"],
    "hourly": ["..."],
}

# Document events
doc_events = {
    "User": {
        "on_change": "insights.insights.doctype.insights_team.insights_team.update_admin_team",
    }
}

# Seed data on migrate
after_migrate = "insights.migrate.after_migrate"

# Page rendering
page_renderer = "insights.utils.InsightsPageRenderer"

# URL routes for SPA
website_route_rules = [
    {"from_route": "/insights/<path:app_path>", "to_route": "insights"},
    {"from_route": "/insights_v2/<path:app_path>", "to_route": "insights_v2"},
]
```

### 1.6 Custom Permission Architecture

Insights implements team-based permissions via an `InsightsPermissions` class:

```python
class InsightsPermissions:
    def __init__(self, user=None):
        self.user = user or frappe.session.user
        self.user_teams = get_teams(self.user) if self.team_permissions_enabled else []

    def get_permission_query_conditions(self, doctype):
        # Returns a SQL condition string to filter queries
        ...

    def has_doc_permission(self, doc, ptype):
        # Permission check per document
        ...

# Registered in hooks.py:
permission_query_conditions = {"<Doctype>": "insights.permissions.get_permission_query_conditions"}
has_permission = {"<Doctype>": "insights.permissions.has_doc_permission"}
```

**Key insight:** For our `api_security_monitor`, we can use simpler Frappe role-based permissions (via `@insights_whitelist` equivalent) or implement custom permission conditions for team-based access.

---

## 2. Frontend Architecture (Vue 3 + frappe-ui)

### 2.1 Directory Layout

```
frontend/src/
├── main.js              # App bootstrap
├── App.vue              # Root: Suspense + AppShell + Toaster
├── router.ts            # Vue Router with auth guards
├── index.css            # frappe-ui CSS + Tailwind + custom styles
├── globals.js           # Global component + provider registration
├── socket.js            # socket.io-client init
├── api/
│   ├── index.ts         # API call wrappers (call, createResource, etc.)
│   └── whitelistedMethods.ts  # DocType → method name map
├── stores/
│   ├── sessionStore.ts  # User session, login/logout
│   ├── settingsStore.ts # App settings
│   ├── cacheStore.ts    # Data source + table cache
│   └── ...
├── components/
│   ├── AppShell.vue     # Sidebar + RouterView + Suspense
│   ├── Sidebar.vue      # Navigation
│   ├── BasePage.vue     # Reusable page shell with breadcrumbs
│   ├── Breadcrumbs.vue  # Home → current page
│   ├── Tabs.vue         # Tab component
│   └── ...
├── dashboard/           # Feature: dashboards
├── query/               # Feature: query builder
├── datasource/          # Feature: data source management
├── notebook/            # Feature: notebooks
├── home/                # Feature: landing page
├── pages/               # Misc standalone pages (Login, Settings, Users, etc.)
├── widgets/             # Chart/table widget renderers
├── composables/         # Shared composables (inline, not a folder — files are in feature dirs)
└── utils/               # Utilities (toasts, dayjs, filters, etc.)
```

**Rule:** Feature-first folders (`dashboard/`, `query/`, `datasource/`, etc.) each contain their own composables, components, and sub-components.

### 2.2 Bootstrap Pattern

```javascript
// src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { frappeRequest, setConfig } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import { initSocket } from './socket'
import { registerGlobalComponents, registerControllers } from './globals'
import './index.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)

// Global resource fetcher that auto-shows error toasts
setConfig('resourceFetcher', (options) => {
  return frappeRequest({
    ...options,
    onError(err) {
      if (err.messages && err.messages[0]) {
        createToast({ title: 'Error', variant: 'error', message: err.messages[0] })
      }
    },
  })
})

app.provide('$socket', initSocket())
registerGlobalComponents(app)
registerControllers(app)
app.mount('#app')
```

Note: Insights does **not** use `FrappeUI` plugin or `<FrappeUIProvider>` — it uses a different approach with global component registration + `setConfig` for the resource fetcher. For new apps, prefer the standard approach from SETUP.md (`app.use(FrappeUI)` + `<FrappeUIProvider>`).

### 2.3 Global Component Registration

```javascript
// src/globals.js
import { Button, Input, Dialog, Badge, Avatar, Tooltip, Dropdown,
         LoadingIndicator, FormControl, Popover, Autocomplete, ErrorMessage,
         FeatherIcon, onOutsideClickDirective } from 'frappe-ui'
import Checkbox from '@/components/Controls/Checkbox.vue'

export function registerGlobalComponents(app) {
  app.component('Button', Button)
  app.component('Input', Input)
  app.component('Dialog', Dialog)
  app.component('Badge', Badge)
  // ... register all commonly-used components globally
  app.directive('on-outside-click', onOutsideClickDirective)
}

export function registerControllers(app) {
  app.provide('$utils', utils)
  app.provide('$dayjs', dayjs)
  app.provide('$notify', createToast)
}
```

**Rule:** Register components used in 3+ places globally. Use `provide`/`inject` for shared utilities.

### 2.4 Router with Auth Guards

```typescript
const routes = [
  { path: '/login', name: 'Login', component: () => import('@/pages/Login.vue'),
    meta: { hideSidebar: true, isGuestView: true } },
  { path: '/', name: 'Home', component: () => import('@/home/Home.vue') },
  { path: '/dashboard', name: 'Dashboards', component: () => import('@/dashboard/DashboardList.vue') },
  { path: '/dashboard/:name', props: true, name: 'Dashboard',
    component: () => import('@/dashboard/Dashboard.vue') },
  // ...
]

const router = createRouter({ history: createWebHistory('/insights_v2'), routes })

router.beforeEach(async (to, _, next) => {
  const session = sessionStore()
  !session.initialized && (await session.initialize())

  if (to.meta.isGuestView && !session.isLoggedIn && to.name !== 'Login') return next()
  if (!session.isLoggedIn) return next('/login')
  if (!session.isAuthorized) return next('/no-permission')

  const settings = settingsStore()
  !settings.initialized && (await settings.initialize())
  if (!settings.settings.setup_complete && to.name !== 'Setup') return next('/setup')

  next()
})

window.fetch = async function () {
  const res = await _fetch(...arguments)
  if (res.status === 403 && (!document.cookie || document.cookie.includes('user_id=Guest'))) {
    sessionStore().resetSession()
    router.push('/login')
  }
  return res
}
```

**Pattern:** `beforeEach` guard handles: session initialization, login redirect, authorization, setup completeness. Override `window.fetch` to detect 403 session expiry.

### 2.5 App Shell

```vue
<template>
  <div class="flex h-screen w-screen bg-white antialiased">
    <RouterView v-if="isGuestView" />
    <Suspense v-else>
      <AppShell />
    </Suspense>
    <Toaster :visible-toasts="2" position="bottom-right" />
  </div>
</template>
```

```vue
<!-- AppShell.vue -->
<template>
  <div class="flex flex-1 overflow-hidden text-base">
    <Sidebar v-if="!hideSidebar" />
    <RouterView v-slot="{ Component }">
      <Suspense>
        <div class="flex flex-1 flex-col overflow-hidden">
          <component :is="Component" :key="$route.fullPath" />
        </div>
        <template #fallback>
          <SuspenseFallback />
        </template>
      </Suspense>
    </RouterView>
  </div>
</template>
```

**Pattern:** `<Suspense>` wraps page components. `PageShell` (sidebar + content) for authenticated views, bare `RouterView` for guest views.

### 2.6 Page Layout Component

```vue
<!-- components/BasePage.vue -->
<template>
  <div class="flex flex-1 flex-col overflow-hidden bg-white p-5">
    <Breadcrumbs />
    <header class="flex h-10 flex-shrink-0 overflow-visible">
      <slot name="header" />
    </header>
    <main class="flex flex-1 overflow-hidden">
      <slot name="main" />
    </main>
  </div>
</template>
```

```vue
<!-- layouts/BaseLayout.vue — for pages with navbar + sidebar -->
<template>
  <div class="flex h-full w-full flex-col bg-gray-50">
    <div class="flex items-center justify-between bg-white px-5 py-2.5 shadow-sm">
      <slot name="navbar" />
    </div>
    <div class="flex flex-1 overflow-hidden">
      <slot name="content" />
      <div v-if="$slots.sidebar" class="flex flex-shrink-0 overflow-hidden">
        <slot name="sidebar" />
      </div>
    </div>
  </div>
</template>
```

### 2.7 Pinia Store Pattern (Composition API)

```javascript
// stores/sessionStore.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

const sessionStore = defineStore('insights:session', function () {
  const initialized = ref(false)
  const user = ref(emptyUser)

  const isLoggedIn = computed(() => user.value.email && user.value.email !== 'Guest')
  const isAuthorized = computed(() => user.value.is_admin || user.value.is_user)

  async function initialize(force = false) {
    if (initialized.value && !force) return
    Object.assign(user.value, getSessionFromCookies())
    isLoggedIn.value && (await fetchSessionInfo())
    isLoggedIn.value && api.trackActiveSite()
    initialized.value = true
  }

  async function login(email, password) {
    resetSession()
    const userInfo = await api.login(email, password)
    if (!userInfo) return
    Object.assign(user.value, userInfo)
    window.location.reload()
  }

  return { user, initialized, isLoggedIn, isAuthorized, initialize, login, logout, ... }
})

export default sessionStore
```

**Pattern:** Store names are scoped with a prefix (`insights:session`, `insights:cache`). Composition API style (`defineStore('name', () => { ... })`). Return object with refs + computed + functions.

---

## 3. Data Access Patterns

### 3.1 Legacy Pattern (used by Insights): `createDocumentResource`

**This is what Insights uses, but for new code use `useCall` instead** (see §3.2).

```javascript
// Legacy — for reference only
import { createDocumentResource } from 'frappe-ui'

function getDashboardResource(name) {
  return createDocumentResource({
    doctype: 'Insights Dashboard',
    name: name,
    auto: false,                          // don't fetch on mount
    whitelistedMethods: {
      fetch_chart_data: 'fetch_chart_data',
      clear_charts_cache: 'clear_charts_cache',
    },
    transform(doc) {                      // parse JSON fields from Frappe
      doc.items = doc.items.map(transformItem)
      return doc
    },
  })
}
```

**Resource lifecycle:**
- `resource.get.fetch()` — fetch from server
- `resource.setValue.submit({ field: value })` — update fields
- `resource.delete.submit()` — delete
- `resource.customMethod.submit(params)` — call whitelisted DocType method
- `resource.get.loading`, `resource.get.error` — reactive state

**Composable wrapping pattern:**

```javascript
export default function useDashboard(name) {
  const resource = getDashboardResource(name)

  // Reactive state object
  const state = reactive({
    doc: { title: undefined, items: [] },
    loading: false,
    editing: false,
  })

  async function reload() {
    state.loading = true
    await resource.get.fetch()
    state.doc = resource.doc
    state.loading = false
  }
  reload()

  async function save() {
    await resource.setValue.submit(state.doc)
    await reload()
  }

  // Merge methods onto state
  return Object.assign(state, { reload, save })
}
```

### 3.2 Recommended Pattern: `useCall`

**Prefer this for all new Frappe API calls.**

```javascript
import { useCall, useList, useDoc, toast } from 'frappe-ui'

// Read — auto-fetches on mount
const summary = useCall({
  url: '/api/method/api_security_monitor.api.dashboard.get_summary',
  params: { period: 24 },
  refetch: true,
  cacheKey: ['dashboard-summary', 24],
})

// Write — trigger on action
const saveRule = useCall({
  url: '/api/method/api_security_monitor.api.rules.create_rule',
  method: 'POST',
  immediate: false,
  onSuccess: () => toast.success('Rule saved'),
  onError: (err) => toast.error(err.message),
})

async function onSubmit() {
  await saveRule.submit({ title: form.title, threshold: form.threshold })
}

// Frappe doctype document
const doc = useDoc({ doctype: 'User', name: userId })

// Frappe doctype list
const list = useList({
  doctype: 'ToDo',
  fields: ['name', 'description', 'status'],
  order_by: 'modified desc',
  limit: 20,
})
```

**Use `useFetch` from `@vueuse/core`** when the frontend is not connected to a real Frappe backend (e.g., during prototyping against the Express backend).

### 3.3 Fallback: `call` for Simple RPCs

```javascript
import { call } from 'frappe-ui'

const userInfo = await call('insights.api.get_user_info')
// Parameters are passed as keyword arguments:
const tableName = await call('insights.api.data_sources.get_table_name', {
  data_source: 'Site DB',
  table: 'users',
})
```

---

## 4. Realtime via Socket.IO

Insights uses raw `socket.io-client`, not Frappe's built-in realtime.

```javascript
// src/socket.js
import { io } from 'socket.io-client'

export function initSocket() {
  let socketio_port = window.socketio_port || 9000
  let host = window.location.hostname
  let siteName = import.meta.env.DEV ? host : window.site_name
  let port = window.location.port ? `:${socketio_port}` : ''
  let protocol = port ? 'http' : 'https'
  let url = `${protocol}://${host}${port}/${siteName}`

  return io(url, { withCredentials: true, reconnectionAttempts: 5 })
}
```

**Consumed via `provide`/`inject`:**

```javascript
// main.js
app.provide('$socket', initSocket())

// App.vue
const $socket = inject('$socket')
$socket.on('insights_notification', (data) => {
  if (data.user == session.user.email) {
    $notify({ title: data.title || data.message, message: data.title ? data.message : '', variant: data.type })
  }
})
```

For `api_security_monitor`, prefer **Frappe's built-in realtime** (`frappe.publish_realtime` + `frappe.realtime.on`) as described in the architecture plan — it removes the need for a separate socket setup.

---

## 5. Coding Conventions

| Convention | Example |
|---|---|
| **Feature-first folders** | `dashboard/`, `query/`, `datasource/` contain components + composables |
| **Composable naming** | `useDashboard.js`, `useQuery.js`, `useDataSource.js` |
| **Composable return** | Reactive `state` object with methods merged on: `Object.assign(state, { reload, save })` |
| **`<script setup>`** | All Vue components use `<script setup>` exclusively |
| **Props** | `const props = defineProps({ name: { type: String, required: true } })` |
| **Store naming** | Scoped: `insights:session`, `insights:cache` |
| **Icons** | `<FeatherIcon name="chevron-right" class="h-4 w-4" />` |
| **CSS entry** | `@import 'frappe-ui/style.css'` + `@tailwind base/components/utilities` |
| **Custom CSS** | `@layer components { ... }` for scrollbar, `.cm-editor` overrides |
| **Debouncing** | `import { debounce } from 'frappe-ui'` — wrap save/update/execute operations |
| **Task queue** | Custom `createTaskRunner()` to serialize async operations |
| **Type annotations** | Backend uses `@validate_type` decorator + Python type hints |
| **Error toast** | Global `resourceFetcher` error handler in `main.js` |

---

## 6. Key Insights for api_security_monitor

### Do adopt these patterns:

1. **Feature-first frontend folder structure** — one folder per domain (dashboard, logs, alerts, sources)
2. **Composable wrapping data access** — each feature gets a `use*.js` that returns reactive state + methods
3. **`<Suspense>` for async page loading** — wrap page components in `<Suspense>` with a fallback spinner
4. **Router auth guards** — `beforeEach` for session + setup checks
5. **Pinia composition API stores** — `defineStore('name', () => { ... })` with scoped names
6. **`@insights_whitelist`-style decorator** — combine `@frappe.whitelist()` + role check into one decorator
7. **API modules per domain** — `api/dashboard.py`, `api/logs.py`, `api/alerts.py`, etc.

### Do NOT replicate these (use the modern path instead):

| Insights uses | Use this instead |
|---|---|
| `createDocumentResource` / `createResource` | `useCall`, `useDoc`, `useList` |
| `setConfig('resourceFetcher', ...)` | `app.use(FrappeUI)` + `<FrappeUIProvider>` |
| Custom global component registration per-app | `FrappeUI` plugin handles component globals |
| Raw `socket.io-client` | Frappe's `frappe.publish_realtime` / `frappe.realtime.on` |
| Custom `createToast` wrapper | `toast.success()` / `toast.error()` from frappe-ui |

---

## 7. Reference: Backend API Module Template

Use this as a template for `api_security_monitor` API modules:

```python
# api/dashboard.py
import frappe
from api_security_monitor.decorators import whitelist

@whitelist()  # custom decorator combining @frappe.whitelist + role check
def get_summary(period: int = 24):
    """Dashboard KPI summary."""
    # Fetch from OpenSearch with Redis caching
    return {
        "total_requests": 1240,
        "avg_latency": 145,
        "success_rate": 97.5,
        "error_count": 31,
        "active_alerts": 3,
    }

@whitelist()
def get_charts(period: int = 24):
    """Time-bucketed traffic/error/latency histogram."""
    # OpenSearch date_histogram aggregation
    return {"traffic": [], "latency": [], "errors": []}

@whitelist()
def get_breakdown(period: int = 24):
    """Per-source, per-status-code, per-endpoint breakdown."""
    # OpenSearch multi-aggregation query
    return {"sources": [], "status_codes": [], "endpoints": []}
```

---

## 8. Reference: Frontend Composable Template

Use this pattern for each feature composable:

```javascript
// composables/useDashboard.js
import { useCall } from 'frappe-ui'
import { reactive, computed } from 'vue'

export function useDashboard() {
  const state = reactive({
    summary: null,
    charts: null,
    breakdown: null,
    loading: false,
    error: null,
  })

  const summary = useCall({
    url: '/api/method/api_security_monitor.api.dashboard.get_summary',
    immediate: false,
    onSuccess: (data) => { state.summary = data },
    onError: (err) => { state.error = err },
  })

  async function fetchAll(period = 24) {
    state.loading = true
    state.error = null
    try {
      await summary.submit({ period })
    } finally {
      state.loading = false
    }
  }

  return { ...state, fetchAll }
}
```
