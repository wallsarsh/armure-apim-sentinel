import { createRouter, createWebHistory } from "vue-router"

const routes = [
  {
    path: "/",
    name: "dashboard",
    component: () => import("./pages/DashboardPage.vue"),
  },
  {
    path: "/logs",
    name: "logs",
    component: () => import("./pages/LogsPage.vue"),
  },
  {
    path: "/alerts",
    name: "alerts",
    component: () => import("./pages/AlertsPage.vue"),
  },
  {
    path: "/sources",
    name: "sources",
    component: () => import("./pages/SourcesPage.vue"),
  },
]

const router = createRouter({
  history: createWebHistory("/api-security-monitor/"),
  routes,
})

export default router
