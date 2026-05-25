import { defineStore } from "pinia"
import { computed, ref } from "vue"
import { call, post } from "../api"

const emptyUser = { email: "", full_name: "", user_image: "" }

export const useSessionStore = defineStore("session", () => {
  const initialized = ref(false)
  const user = ref({ ...emptyUser })
  const isLoggedIn = computed(() => user.value.email && user.value.email !== "Guest")

  async function initialize(force = false) {
    if (initialized.value && !force) return
    Object.assign(user.value, getSessionFromCookies())
    if (isLoggedIn.value) await fetchUserInfo()
    initialized.value = true
  }

  async function fetchUserInfo() {
    if (!isLoggedIn.value) return
    try {
      const info = await call("frappe.auth.get_logged_user")
      user.value.email = info || user.value.email
      if (info && info !== "Guest") {
        try {
          const full = await call("frappe.client.get_value", {
            doctype: "User",
            fieldname: ["full_name", "user_image"],
            filters: JSON.stringify({ name: info }),
          })
          user.value.full_name = full?.full_name || info
          user.value.user_image = full?.user_image || ""
        } catch {}
      }
    } catch {}
  }

  async function login(email, password) {
    try {
      const res = await fetch("/api/method/login", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ usr: email, pwd: password }),
      })
      if (res.redirected) throw new Error("Redirect blocked")
      const data = await res.json()
      if (data.exc) throw new Error(data._error_message || "Login failed")
      user.value.email = email
      user.value.full_name = data.full_name || email
    } catch (e) {
      throw new Error(e.message || "Login failed")
    }
  }

  async function logout() {
    try {
      await post("logout")
    } catch {}
    user.value = { ...emptyUser }
    window.location.reload()
  }

  return { user, initialized, isLoggedIn, initialize, fetchUserInfo, login, logout }
})

function getSessionFromCookies() {
  const cookies = document.cookie.split("; ").reduce((acc, c) => {
    const [k, v] = c.split("=")
    acc[k === "user_id" ? "email" : k] = decodeURIComponent(v)
    return acc
  }, {})
  return { email: cookies.email || "", full_name: cookies.full_name || "", user_image: "" }
}