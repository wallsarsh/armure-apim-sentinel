import { defineStore } from "pinia"
import { ref, computed } from "vue"
import api from "../api"

export const useTelemetryStore = defineStore("telemetry", () => {
  const logs = ref([])
  const alerts = ref([])
  const scanHistory = ref([])
  const sources = ref([])
  const rules = ref([])
  const dashboardMetrics = ref(null)
  const dashboardCharts = ref([])
  const dashboardBreakdown = ref(null)
  const isScanning = ref(false)
  const realtimeReady = ref(false)
  const initialLoading = ref(true)
  const totalLogs = ref(0)

  const activeAlertsCount = computed(() =>
    alerts.value.filter(a => !a.resolved).length
  )

  async function pollAll() {
    await Promise.allSettled([
      fetchDashboard(),
      fetchAlerts(),
    ])
  }

  async function initialLoad() {
    initialLoading.value = true
    await Promise.allSettled([
      fetchDashboard(),
      fetchSources(),
      fetchRules(),
      fetchAlerts(),
      fetchScanHistory(),
    ])
    initialLoading.value = false
  }

  async function fetchDashboard(period = 24) {
    try {
      const [summary, charts, breakdown] = await Promise.all([
        api.call("armure_apim_sentinel.api.dashboard.get_summary", { period }),
        api.call("armure_apim_sentinel.api.dashboard.get_charts", { period }),
        api.call("armure_apim_sentinel.api.dashboard.get_breakdown", { period }),
      ])
      dashboardMetrics.value = summary
      dashboardCharts.value = charts?.timeline || []
      dashboardBreakdown.value = breakdown
    } catch (e) {
      console.error("Dashboard fetch failed:", e)
    }
  }

  async function fetchLogs(params = {}) {
    try {
      const result = await api.call("armure_apim_sentinel.api.logs.query_logs", params)
      logs.value = result.logs || []
      totalLogs.value = result.total || 0
      return result
    } catch (e) {
      console.error("Logs fetch failed:", e)
      return { logs: [], total: 0 }
    }
  }

  async function fetchSources() {
    try {
      sources.value = await api.call("armure_apim_sentinel.api.sources.list_sources")
    } catch (e) {
      console.error("Sources fetch failed:", e)
    }
  }

  async function fetchRules() {
    try {
      rules.value = await api.call("frappe.client.get_list", {
        doctype: "Security Alert Rule",
        fields: JSON.stringify(["name", "rule_name", "metric", "condition", "threshold", "severity", "is_active"]),
        filters: JSON.stringify({}),
      })
    } catch (e) {
      console.error("Rules fetch failed:", e)
    }
  }

  async function fetchAlerts(status = "all", limit = 50) {
    try {
      alerts.value = await api.call("armure_apim_sentinel.api.alerts.list_alerts", { status, limit })
    } catch (e) {
      console.error("Alerts fetch failed:", e)
    }
  }

  async function fetchScanHistory(limit = 10) {
    try {
      scanHistory.value = await api.call("armure_apim_sentinel.api.anomaly.list_anomaly_reports", { limit })
    } catch (e) {
      console.error("Scan history fetch failed:", e)
    }
  }

  async function triggerAnomalyScan() {
    isScanning.value = true
    try {
      await api.post("armure_apim_sentinel.api.anomaly.trigger_anomaly_scan")
    } catch (e) {
      console.error("Scan trigger failed:", e)
    } finally {
      isScanning.value = false
    }
  }

  function initRealtime() {
    if (window.frappe?.realtime) {
      window.frappe.realtime.on("security_anomaly_triggered", (data) => {
        alerts.value.unshift(data)
        if (dashboardMetrics.value) {
          dashboardMetrics.value.activeAlerts++
        }
      })
      window.frappe.realtime.on("security_scan_complete", (data) => {
        scanHistory.value.unshift(data)
      })
      realtimeReady.value = true
    }
  }

  return {
    logs, alerts, scanHistory, sources, rules,
    dashboardMetrics, dashboardCharts, dashboardBreakdown,
    isScanning, realtimeReady, totalLogs, initialLoading, activeAlertsCount,
    initialLoad, pollAll,
    fetchDashboard, fetchLogs, fetchSources, fetchRules,
    fetchAlerts, fetchScanHistory, triggerAnomalyScan, initRealtime,
  }
})
