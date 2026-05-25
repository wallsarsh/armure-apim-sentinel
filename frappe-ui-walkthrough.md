# Frappe UI Walkthrough for the API Security Monitor App

## Purpose

This guide translates the `frappe-ui` framework and its skill notes into a practical workflow for building the Frappe frontend for `api_security_monitor`.

It is written as a **development guide**, not as a generic library summary. The goal is to make the frontend implementation consistent with the framework’s conventions, naming, tokens, and data patterns while preserving the behavior already captured in the prototype.

## Source of truth

The guidance in this walkthrough is based on the framework and skill files under:

- `frappe-reference/frappe-ui/skills/frappe-ui/SKILL.md`
- `frappe-reference/frappe-ui/skills/frappe-ui/SETUP.md`
- `frappe-reference/frappe-ui/skills/frappe-ui/COMPONENTS.md`
- `frappe-reference/frappe-ui/skills/frappe-ui/PATTERNS.md`
- `frappe-reference/frappe-ui/skills/frappe-ui/TOKENS.md`
- `frappe-reference/frappe-ui/CONTEXT.md`
- `frappe-reference/frappe-ui/PHILOSOPHY.md`

Use this walkthrough as the working guide when creating the Vue frontend for the Frappe app.

---

## 1. What frappe-ui is and what it is not

frappe-ui is a **Vue 3 component library and UI system** for Frappe apps. It is not a full application scaffold by itself.

### What you still need

- Vue 3
- Vite
- Vue Router
- Tailwind v3
- `frappe-ui`
- `FrappeUIProvider`
- `FrappeUI` plugin

### Mental model

Think of frappe-ui as:

1. a component library for buttons, inputs, dialogs, dropdowns, lists, and overlays
2. a semantic design system built on Tailwind tokens
3. a data layer wrapper for Frappe APIs via `useCall`

It does **not** replace Frappe backend modules, DocTypes, OpenSearch, Redis, or scheduler logic.

---

## 2. Project setup checklist

Use this when bootstrapping the Vue app for the Frappe frontend.

### Required package versions

- Tailwind **v3.4**
- Vite **v5**
- Vue **v3**
- Vue Router **v4**
- `frappe-ui`
- `unplugin-icons`
- `lucide-static`
- `@iconify/json`

### Why these versions matter

The framework expects a Vite plugin and Tailwind setup that match its package exports and icon resolution logic.

### Recommended install flow

```bash
npm install
npm uninstall tailwindcss @tailwindcss/vite vite @vitejs/plugin-vue
npm install -D \
  tailwindcss@^3.4 \
  postcss \
  autoprefixer \
  vite@^5 \
  @vitejs/plugin-vue@^5 \
  vue-router@^4 \
  unplugin-auto-import \
  unplugin-vue-components \
  unplugin-icons \
  lucide-static \
  @iconify/json
npm install frappe-ui
```

### Vite configuration

Use the framework plugin and disable Frappe-specific defaults unless you are running inside a real Frappe site.

```js
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
})
```

### Tailwind configuration

```js
import frappeUIPreset from 'frappe-ui/tailwind'

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

### CSS entry

```css
@import 'frappe-ui/style.css';
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### App entry

```js
import { createApp } from 'vue'
import { FrappeUI } from 'frappe-ui'
import { router } from './router'
import './style.css'
import App from './App.vue'

const app = createApp(App)
app.use(router)
app.use(FrappeUI)
app.mount('#app')
```

### Provider root

```vue
<script setup>
import { FrappeUIProvider } from 'frappe-ui'
</script>

<template>
  <FrappeUIProvider>
    <router-view />
  </FrappeUIProvider>
</template>
```

### Router stub

Even if the app is single-page, install vue-router.

```js
import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Home', component: () => import('./pages/Home.vue') },
  ],
})
```

---

## 3. Design system rules

### Semantic tokens only

Use semantic tokens such as:

- `bg-surface-white`
- `bg-surface-gray-1`
- `border-outline-gray-1`
- `text-ink-gray-9`
- `text-ink-gray-5`
- `text-ink-red-3`
- `text-ink-green-3`
- `text-ink-blue-link`

Do **not** use raw Tailwind colors like `bg-gray-100` or `text-gray-900`.

### Typography rule

Use two typography scales:

- `text-*` for one-line labels, headings, button labels, badges, values
- `text-p-*` for paragraphs, descriptions, helper text, wrapping copy

### Color rule

Use exactly these color axes:

- `variant`
- `theme`

Do **not** invent props like `intent`, `severity`, `kind`, or `appearance`.

### Layout rule

- Align repeating content in columns.
- Keep one primary action per page.
- Use color for state, not decoration.
- Use borders only where they add meaning.
- Avoid boxing every section.

---

## 4. Component selection rules

### Prefer existing components

When a component exists, use it instead of building your own.

Use these as the first stop:

- `Button`
- `Dialog`
- `Popover`
- `Dropdown`
- `FormControl`
- `TextInput`
- `TextArea`
- `Select`
- `MultiSelect`
- `Combobox`
- `Autocomplete`
- `Badge`
- `Alert`
- `ListView`
- `Tabs`
- `TabButtons`
- `Tooltip`
- `Switch`
- `Checkbox`
- `DatePicker`
- `MonthPicker`
- `TimePicker`
- `DateRangePicker`
- `FileUploader`
- `LoadingText`
- `LoadingIndicator`
- `Spinner`
- `Divider`
- `Breadcrumbs`

### Slots

Use the canonical slot vocabulary:

- `#default`
- `#prefix`
- `#suffix`
- `#trigger`
- `#empty`
- `#header`
- `#footer`
- `#label`
- `#description`

Do not invent component-specific slot names.

### Icons

Render icons as CSS classes, for example:

```vue
<span class="lucide-plus size-4" aria-hidden="true" />
```

For frappe-ui props that accept icons, pass the icon string, for example:

```vue
<Button icon-left="lucide-plus" label="New" />
```

---

## 5. Data access rules

### Preferred data composables

Use `useCall` for Frappe APIs.

Use `useList` and `useDoc` when they match the shape of the data better.

Use `useFetch` only when the frontend is **not** connected to a real Frappe backend.

### Standard read pattern

```ts
import { useCall } from 'frappe-ui'

const summary = useCall({
  url: '/api/method/api_security_monitor.api.dashboard_summary',
  refetch: true,
})
```

### Standard write pattern

```ts
import { useCall, toast } from 'frappe-ui'

const saveRule = useCall({
  url: '/api/method/api_security_monitor.api.create_rule',
  method: 'POST',
  immediate: false,
  onSuccess: () => toast.success('Rule saved'),
  onError: (err) => toast.error(err.message),
})

async function submitRule() {
  await saveRule.submit(payload)
}
```

### Error and loading handling

When using `useCall`, render:

- loading placeholder when data is not ready
- `ErrorMessage` or equivalent text when `error` exists
- real UI once data is available

Do not hand-roll `fetch` calls for real Frappe endpoints.

---

## 6. Recommended app structure for the Frappe frontend

A practical structure for `api_security_monitor` is:

```text
frontend/
├── src/
│   ├── App.vue
│   ├── main.js
│   ├── router.js
│   ├── style.css
│   ├── assets/
│   ├── components/
│   │   ├── layout/
│   │   ├── dashboard/
│   │   ├── logs/
│   │   ├── alerts/
│   │   ├── sources/
│   │   └── shared/
│   ├── composables/
│   │   ├── useDashboard.js
│   │   ├── useLogs.js
│   │   ├── useAlerts.js
│   │   └── useSources.js
│   ├── stores/
│   │   └── telemetry.js
│   └── pages/
│       ├── DashboardPage.vue
│       ├── LogsPage.vue
│       ├── AlertsPage.vue
│       └── SourcesPage.vue
```

### Recommended split

- `pages/` for top-level views
- `components/` for reusable UI pieces
- `composables/` for API logic
- `stores/` for shared state, especially realtime state

### State recommendation

Use Pinia if you want shared state for realtime and cross-page data. The framework itself does not require it, but it is a strong fit here because the app will need to coordinate live activity, filters, and scan state.

---

## 7. Recommended UI composition patterns

### Standard page shell

Create pages using a neutral layout with a header and content area.

```vue
<template>
  <div class="flex h-full flex-col bg-surface-white">
    <header class="flex items-center justify-between border-b border-outline-gray-1 px-6 py-4">
      <div>
        <Breadcrumbs :items="crumbs" />
        <h1 class="mt-1 text-xl text-ink-gray-9">API Security Monitor</h1>
      </div>
      <div class="flex gap-2">
        <Button label="Refresh" @click="refresh" />
        <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Rule" />
      </div>
    </header>

    <main class="flex-1 overflow-y-auto p-6">
      <router-view />
    </main>
  </div>
</template>
```

### Form page pattern

- one-column layout
- `FormControl` for fields
- `label`, `description`, `error`, `required`
- primary action on the right
- secondary action on the left

### List page pattern

Prefer `ListView` over hand-built tables when data is structured and repeated.

### Empty state pattern

Use a centered empty state with a clear call to action, not an empty table.

### Confirmation pattern

Use `dialog.confirm` for destructive actions.

```ts
import { dialog, toast } from 'frappe-ui'

async function deleteRule(id) {
  dialog.confirm({
    title: 'Delete rule?',
    message: 'This action cannot be undone.',
    theme: 'red',
    confirmLabel: 'Delete',
    onConfirm: async ({ close }) => {
      await deleteRuleApi(id)
      close()
      toast.success('Rule deleted')
    },
  })
}
```

---

## 8. Realtime integration pattern

The app will need to react to live events for:

- new logs
- new alerts
- scan completion
- simulation changes

### Recommended approach

- Keep Frappe backend as the source of truth.
- Use realtime events to push updates to the Vue client.
- Keep polling as a fallback for dashboard state if needed.

### Practical guidance

- Store live state in Pinia.
- Keep one source of truth for logs, alerts, scans, and simulation state.
- Use realtime events to append or update local state.
- Use `useCall` for initial hydration and fallback fetches.

---

## 9. What to avoid

### Avoid these anti-patterns

- Using raw `fetch` or `axios` for Frappe APIs
- Importing invalid package subpaths
- Using Tailwind v4 or Vite 6+
- Ignoring `vue-router`
- Hand-rolling buttons, dialogs, selects, and dropdowns
- Using `bg-gray-*` and `text-gray-*`
- Using `intent`, `kind`, or `appearance`
- Using placeholder text as the only label
- Building a custom confirm modal instead of using `dialog.confirm`
- Using `createResource` in new code when `useCall` is appropriate

---

## 10. How to map the current prototype into frappe-ui

### Current prototype behavior

The current prototype already defines the feature contract:

- dashboard metrics
- traffic and latency charts
- endpoint breakdowns
- filters and time range controls
- logs explorer
- AI explanation flow
- alert rules and alert acknowledgements
- source management
- simulation controls
- JSON and CSV ingestion
- AI anomaly scans

### Mapping to frappe-ui

#### Dashboard

Use `Button`, `Badge`, `Tabs`, `ListView`, and `Alert` where appropriate.

#### Logs

Use:

- `TextInput`
- `Select`
- `DatePicker` / `DateRangePicker`
- `ListView`
- `Dialog` for log details
- `Button` for actions like export and explain

#### Alerts

Use:

- `Tabs` or `TabButtons`
- `Badge`
- `Dialog` for confirmations
- `Button` for resolve actions
- `FormControl` for rule creation

#### Sources

Use:

- `Select`
- `TextInput`
- `Switch`
- `FileUploader`
- `Alert` for parse or ingest feedback

### Important portability rule

The frontend should preserve the current behavior and user flows, even if the internal implementation changes from React/Express to Vue/Frappe.

---

## 11. Recommended build workflow

### Phase A — bootstrap the Vue app

1. Create the frontend scaffold
2. Install the correct dependency versions
3. Wire router and provider
4. Add Tailwind and frappe-ui CSS
5. Build a simple route shell

### Phase B — define the page structure

1. Dashboard page
2. Logs page
3. Alerts page
4. Sources page
5. Shared layout

### Phase C — bind data

1. Add `useCall` hooks for summary, logs, alerts, rules, sources, and scan history
2. Add realtime store for live updates
3. Add fallback polling if needed

### Phase D — implement interactions

1. filters and time range controls
2. log detail dialog
3. AI explain action
4. alert resolve and rule CRUD
5. source enable/disable
6. manual JSON/CSV ingest
7. simulation controls

### Phase E — polish

1. semantic tokens only
2. dark mode verification
3. loading and empty states
4. validation and error text
5. accessibility labels

---

## 12. Practical patterns for the API Security Monitor app

### Dashboard page

Use a neutral top header, summary cards, charts, and a small details pane. Keep actions minimal.

### Logs page

Use filter controls at the top, a list view below, and a detail dialog for inspection.

### Alerts page

Use tabs for:

- triggered alerts
- rule configuration
- AI scan history

### Sources page

Use a card or list layout with source status, counters, and quick actions.

### Ingest workflow

- Use `TextInput` and `Textarea` for manual JSON
- Use `FileUploader` for file ingestion
- Display success/error states using `Alert`

---

## 13. Implementation checklist

Use this checklist while developing the app.

- [ ] Tailwind v3 and Vite v5 are pinned
- [ ] `frappe-ui` is installed
- [ ] `FrappeUI` plugin and `FrappeUIProvider` are configured
- [ ] Vue Router is installed
- [ ] Semantic tokens are used everywhere
- [ ] Buttons, dialogs, forms, and overlays come from frappe-ui
- [ ] `useCall` is used for Frappe API calls
- [ ] `useFetch` is used only for non-Frappe prototypes
- [ ] Current UI behavior is preserved
- [ ] Loading, empty, and error states are present
- [ ] Dark mode is tested
- [ ] Realtime updates are routed through a shared store

---

## 14. Final guidance

The fastest path to a good Frappe frontend is to **treat frappe-ui as the UI contract, not as a decorative layer**.

In practice:

1. start from the current prototype behavior
2. match the existing user flows
3. use frappe-ui components for the UI surface
4. use semantic tokens for styling
5. use `useCall` for data
6. use `dialog.confirm` for confirmations
7. preserve the current loading, empty, and error behavior

If you follow this guide, the Vue frontend will feel native to frappe-ui while still preserving the operational workflows already built in the prototype.
