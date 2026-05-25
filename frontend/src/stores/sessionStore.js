import { defineStore } from "pinia"
import { ref } from "vue"

export const useSessionStore = defineStore("session", () => {
  const user = ref(null)
  const isLoggedIn = ref(false)
  const initialized = ref(false)

  async function init() {
    try {
      const res = await fetch("/api/method/frappe.auth.get_logged_user", {
        credentials: "include",
      })
      const data = await res.json()
      if (data.message) {
        user.value = data.message
        isLoggedIn.value = true
      }
    } catch {
      user.value = null
      isLoggedIn.value = false
    } finally {
      initialized.value = true
    }
  }

  function logout() {
    user.value = null
    isLoggedIn.value = false
  }

  return { user, isLoggedIn, initialized, init, logout }
})
