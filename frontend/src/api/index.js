function getCSRFToken() {
  const name = "X-Frappe-CSRF-Token"
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : ""
}

async function handleResponse(res) {
  if (res.redirected) {
    throw new Error("Session expired — redirect to login")
  }
  if (!res.ok) {
    const text = await res.text()
    let msg = `HTTP ${res.status}`
    try {
      const data = JSON.parse(text)
      msg = data._error_message || data.exception || msg
    } catch {}
    throw new Error(msg)
  }
  const data = await res.json()
  if (data.exc) {
    const msg = data._error_message || "Request failed"
    throw new Error(msg)
  }
  return data.message
}

async function call(method, params = {}, options = {}) {
  const url = new URL(`/api/method/${method}`, window.location.origin)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== "") {
      url.searchParams.set(k, v)
    }
  })

  const res = await fetch(url, {
    credentials: "include",
    headers: {
      Accept: "application/json",
      "X-Frappe-CSRF-Token": getCSRFToken(),
    },
    ...options,
  })

  return handleResponse(res)
}

async function post(method, payload = {}) {
  const res = await fetch(`/api/method/${method}`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      "X-Frappe-CSRF-Token": getCSRFToken(),
    },
    body: JSON.stringify(payload),
  })
  return handleResponse(res)
}

export function useCall() {
  return { call, post }
}

export default { call, post }
