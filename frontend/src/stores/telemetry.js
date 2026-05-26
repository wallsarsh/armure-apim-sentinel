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
  const timeRange = ref(null)
  const aiConfigured = ref(false)
  const aiProvider = ref("")
  const aiModel = ref("")
  const aiApiBase = ref("")
  const autoRefreshActive = ref(false)
  const autoRefreshInterval = ref(5)
  let autoRefreshTimer = null

  const activeAlertsCount = computed(() =>
    alerts.value.filter(a => !a.resolved).length
  )

  async function pollAll(period = 24) {
    await Promise.allSettled([
      fetchDashboard(period),
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
      fetchAIConfig(),
    ])
    initialLoading.value = false
  }

  async function fetchDashboard(period = 24) {
    try {
      const params = { period }
      if (timeRange.value) {
        params.from_ = new Date(timeRange.value.from).toISOString()
        params.to = new Date(timeRange.value.to).toISOString()
      }
      const [summary, charts, breakdown] = await Promise.all([
        api.call("armure_apim_sentinel.api.dashboard.get_summary", params),
        api.call("armure_apim_sentinel.api.dashboard.get_charts", params),
        api.call("armure_apim_sentinel.api.dashboard.get_breakdown", params),
      ])
      dashboardMetrics.value = summary
      dashboardCharts.value = charts?.timeline || []
      dashboardBreakdown.value = breakdown
    } catch (e) {
      console.error("Dashboard fetch failed:", e)
    }
  }

  async function setTimeRange(from, to) {
    timeRange.value = { from, to }
    await fetchDashboard()
  }

  async function clearTimeRange() {
    timeRange.value = null
    await fetchDashboard()
  }

  async function fetchAIConfig() {
    try {
      const data = await api.call("armure_apim_sentinel.api.config.get_settings_data")
      aiConfigured.value = data.ai_configured
      aiProvider.value = data.ai_provider
      aiModel.value = data.ai_model
      aiApiBase.value = data.ai_api_base
    } catch (e) {
      console.error("AI config fetch failed:", e)
      aiConfigured.value = false
    }
  }

  function startAutoRefresh() {
    stopAutoRefresh()
    autoRefreshActive.value = true
    autoRefreshTimer = setInterval(() => pollAll(), autoRefreshInterval.value * 1000)
  }

  function stopAutoRefresh() {
    if (autoRefreshTimer) {
      clearInterval(autoRefreshTimer)
      autoRefreshTimer = null
    }
  }

  function toggleAutoRefresh() {
    if (autoRefreshActive.value) {
      stopAutoRefresh()
      autoRefreshActive.value = false
    } else {
      startAutoRefresh()
    }
  }

  function setAutoRefreshInterval(seconds) {
    autoRefreshInterval.value = seconds
    if (autoRefreshActive.value) {
      stopAutoRefresh()
      startAutoRefresh()
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
      rules.value = await api.call("armure_apim_sentinel.api.alerts.list_rules")
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
      const raw = await api.call("armure_apim_sentinel.api.anomaly.list_anomaly_reports", { limit })
      scanHistory.value = (raw || []).map(r => ({
        name: r.name,
        timestamp: r.scan_time,
        anomalyScore: r.anomaly_score,
        detectedAlertsCount: r.triggered_alerts_count,
        analysis: r.generated_summary,
      }))
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
        scanHistory.value.unshift({
          name: data.name,
          timestamp: data.scan_time || new Date().toISOString(),
          anomalyScore: data.score || 0,
          detectedAlertsCount: data.alerts_count || 0,
          analysis: data.summary || "",
        })
      })
      realtimeReady.value = true
    }
  }

  return {
    logs, alerts, scanHistory, sources, rules,
    dashboardMetrics, dashboardCharts, dashboardBreakdown,
    isScanning, realtimeReady, totalLogs, initialLoading, activeAlertsCount,
    timeRange, aiConfigured, aiProvider, aiModel, aiApiBase,
    autoRefreshActive, autoRefreshInterval,
    initialLoad, pollAll,
    fetchDashboard, fetchLogs, fetchSources, fetchRules,
    fetchAlerts, fetchScanHistory, triggerAnomalyScan, initRealtime,
    setTimeRange, clearTimeRange, fetchAIConfig,
    startAutoRefresh, stopAutoRefresh, toggleAutoRefresh, setAutoRefreshInterval,
  }
})
