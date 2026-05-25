import { createRouter, createWebHistory } from "vue-router"

const routes = [
  {
    path: "/login",
    name: "login",
    meta: { guestOnly: true },
    component: () => import("./pages/Login.vue"),
  },
  {
    path: "/",
    name: "dashboard",
    meta: { auth: true },
    component: () => import("./pages/DashboardPage.vue"),
  },
  {
    path: "/logs",
    name: "logs",
    meta: { auth: true },
    component: () => import("./pages/LogsPage.vue"),
  },
  {
    path: "/alerts",
    name: "alerts",
    meta: { auth: true },
    component: () => import("./pages/AlertsPage.vue"),
  },
  {
    path: "/sources",
    name: "sources",
    meta: { auth: true },
    component: () => import("./pages/SourcesPage.vue"),
  },
  {
    path: "/notifications",
    name: "notifications",
    meta: { auth: true },
    component: () => import("./pages/NotificationsPage.vue"),
  },
]

const router = createRouter({
  history: createWebHistory("/api-security-monitor/"),
  routes,
})

function getLoggedUser() {
  try {
    const match = document.cookie.match(/(?:^|; )user_id=([^;]*)/)
    return match ? decodeURIComponent(match[1]) : "Guest"
  } catch {
    return "Guest"
  }
}

router.beforeEach((to, from, next) => {
  if (to.meta.auth) {
    const user = getLoggedUser()
    if (!user || user === "Guest") {
      return next({ name: "login", query: { redirect: to.fullPath } })
    }
  }
  if (to.meta.guestOnly) {
    const user = getLoggedUser()
    if (user && user !== "Guest") {
      return next({ name: "dashboard" })
    }
  }
  next()
})

export default router