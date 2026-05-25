import { ref, watch, computed, unref } from "vue"

function getCSRFToken() {
  const match = document.cookie.match(/(?:^|; )X-Frappe-CSRF-Token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : ""
}

function headers() {
  const h = { Accept: "application/json" }
  const token = getCSRFToken()
  if (token) h["X-Frappe-CSRF-Token"] = token
  return h
}

async function handleResponse(res) {
  if (res.redirected) throw new Error("Session expired")
  const text = await res.text()
  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    try { const d = JSON.parse(text); msg = d._error_message || d.exception || msg } catch {}
    throw new Error(msg)
  }
  const data = JSON.parse(text)
  if (data.exc) throw new Error(data._error_message || "Request failed")
  return data.message
}

/**
 * Frappe UI–style `useCall` composable.
 *
 * Read (auto-fetches on mount):
 *   const { data, loading, error } = useCall({ url: '/api/method/...' })
 *
 * Write (triggered by submit):
 *   const { submit, loading, error } = useCall({ url: '/api/method/...', method: 'POST', immediate: false })
 *   await submit({ key: 'value' })
 */
export function useCall(opts) {
  const urlRef = typeof opts.url === "function" ? computed(opts.url) : ref(opts.url)
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function execute(body) {
    error.value = null
    loading.value = true
    try {
      const res = await fetch(unref(urlRef), {
        method: opts.method || "GET",
        credentials: "include",
        headers: body ? { "Content-Type": "application/json", ...headers() } : headers(),
        body: body ? JSON.stringify(body) : null,
      })
      data.value = await handleResponse(res)
      if (opts.onSuccess) opts.onSuccess(data.value)
      return data.value
    } catch (e) {
      error.value = e
      if (opts.onError) opts.onError(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  if (opts.immediate !== false && (opts.method || "GET") === "GET") {
    watch(urlRef, () => execute(), { immediate: true })
  }

  return { data, loading, error, submit: execute }
}

/**
 * GET convenience — used in Pinia stores where composables aren't available.
 *   await call('module.api.method', { param1: 'value' })
 */
export async function call(method, params = {}) {
  const url = new URL(`/api/method/${method}`, window.location.origin)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== "") url.searchParams.set(k, v)
  })
  const res = await fetch(url, { credentials: "include", headers: headers() })
  return handleResponse(res)
}

/**
 * POST convenience — used in Pinia stores where composables aren't available.
 *   await post('module.api.method', { key: 'value' })
 */
export async function post(method, payload = {}) {
  const res = await fetch(`/api/method/${method}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", ...headers() },
    body: JSON.stringify(payload),
  })
  return handleResponse(res)
}

export default { call, post }