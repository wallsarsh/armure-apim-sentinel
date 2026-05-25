<template>
  <div v-if="isGuestView" :class="['min-h-screen antialiased font-sans', isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-zinc-50 text-zinc-900']">
    <router-view />
  </div>
  <div v-else :class="['flex flex-col md:flex-row min-h-screen antialiased font-sans', isDark ? 'bg-zinc-950 text-zinc-100' : 'bg-zinc-50 text-zinc-900']">
    <AppSidebar
      :current-tab="currentTab"
      :active-alerts-count="telemetry.activeAlertsCount"
      :is-dark="isDark"
      @toggle-dark="toggleDark"
      @update:current-tab="navigateToTab"
    />
    <main class="main-content flex-1 flex flex-col min-h-0 overflow-y-auto">
      <header class="app-header p-5 md:px-8 md:py-6 border-b border-zinc-800 flex flex-wrap justify-between items-center gap-4 bg-zinc-950/80 sticky top-0 z-30 backdrop-blur-md bg-opacity-70">
        <div>
          <span class="text-zinc-500 text-[10px] font-mono font-bold uppercase tracking-wider">Gateway Governance Control</span>
          <div class="flex items-center gap-2 mt-0.5">
            <h2 class="text-white text-lg font-bold">API Security Aggregator</h2>
            <div class="flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-sans font-semibold">
              <span class="h-1.5 w-1.5 bg-emerald-400 rounded-full animate-ping" />
              <span>ONLINE</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-4 text-xs">
          <div class="flex items-center gap-3">
            <span class="text-zinc-400 font-medium">Time Window:</span>
            <div class="flex bg-zinc-900 border border-zinc-800 rounded-xl p-1 font-mono">
              <button
                v-for="opt in periodOptions"
                :key="opt.value"
                @click="periodHours = opt.value"
                :class="[ 'px-3 py-1 rounded-lg font-semibold text-xs cursor-pointer transition-all', periodHours === opt.value ? 'bg-zinc-100 text-zinc-950' : 'text-zinc-400 hover:text-white hover:bg-zinc-800' ]"
              >{{ opt.label }}</button>
            </div>
          </div>
          <div v-if="session.initialized && session.isLoggedIn" class="flex items-center gap-2 border-l border-zinc-800 pl-3 ml-3">
            <span class="text-zinc-400 text-[10px] font-mono truncate max-w-[120px]">{{ session.user.email }}</span>
            <button @click="session.logout" class="p-1.5 hover:bg-rose-500/10 hover:text-rose-400 text-zinc-500 rounded border border-transparent hover:border-rose-500/20 transition-all cursor-pointer" title="Sign out">
              <LogOut class="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>
      <div class="p-5 md:p-8 space-y-6 flex-1 select-none">
        <MetricsCards
          :metrics="telemetry.dashboardMetrics"
          :loading="telemetry.initialLoading"
          :period-label="periodLabel"
        />
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue"
import { useRouter, useRoute } from "vue-router"
import { useTelemetryStore } from "./stores/telemetry"
import { useSessionStore } from "./stores/sessionStore"
import AppSidebar from "./components/layout/AppSidebar.vue"
import MetricsCards from "./components/shared/MetricsCards.vue"
import { LogOut } from "lucide-vue-next"

const router = useRouter()
const route = useRoute()
const telemetry = useTelemetryStore()
const session = useSessionStore()

const isDark = ref(true)
const periodHours = ref(24)
const periodOptions = [
  { label: '2 Hours', value: 2 },
  { label: '24 Hours', value: 24 },
  { label: '3 Days', value: 72 },
]
const periodLabel = computed(() => {
  const map = { 2: 'Last 2h', 24: 'Last 24h', 72: 'Last 3d' }
  return map[periodHours.value] || 'Last 24h'
})

const isGuestView = computed(() => route.meta?.guestOnly)

let pollInterval = null

const currentTab = computed(() => route.name || "dashboard")

function navigateToTab(tab) {
  router.push({ name: tab })
}

function toggleDark() {
  isDark.value = !isDark.value
  document.documentElement.setAttribute("data-theme", isDark.value ? "dark" : "light")
  localStorage.setItem("theme", isDark.value ? "dark" : "light")
}

watch(periodHours, (val) => {
  telemetry.fetchDashboard(val)
})

onMounted(async () => {
  const stored = localStorage.getItem("theme")
  isDark.value = stored !== "light"
  document.documentElement.setAttribute("data-theme", isDark.value ? "dark" : "light")

  await session.initialize()

  if (!isGuestView.value) {
    await telemetry.initialLoad()
    pollInterval = setInterval(() => telemetry.pollAll(periodHours.value), 2500)
  }
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>