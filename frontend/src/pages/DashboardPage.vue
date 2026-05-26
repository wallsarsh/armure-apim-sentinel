<template>
  <div class="space-y-6">
    <!-- Date Range Filter -->
    <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 md:p-5 shadow-sm">
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 font-mono text-xs">
        <div class="flex items-center gap-2.5">
          <div class="p-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
            <Calendar class="h-4.5 w-4.5" />
          </div>
          <div>
            <h4 class="text-white font-bold text-xs uppercase tracking-wider">Dashboard Historical Lens</h4>
            <p class="text-[10px] text-zinc-400">Click a chart data point or drag to zoom to isolate specific time ranges</p>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <button v-if="telemetry.timeRange" @click="clearLens" class="px-3 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer">
            <X class="h-3.5 w-3.5" />
            <span>Clear Lens</span>
          </button>
        </div>
      </div>
      <div v-if="telemetry.timeRange" class="mt-3.5 pt-3.5 border-t border-zinc-800/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-[11px] font-mono text-emerald-400 rounded-lg border border-emerald-500/5 bg-emerald-500/5 p-2.5">
        <div class="flex items-center gap-2">
          <Clock class="h-4 w-4 text-emerald-400 animate-pulse shrink-0" />
          <span>
            Isolated Interval:
            <span class="font-bold underline text-white">{{ formatTime(telemetry.timeRange.from) }}</span>
            to
            <span class="font-bold underline text-white">{{ formatTime(telemetry.timeRange.to) }}</span>
          </span>
        </div>
        <button @click="exploreLogs" class="px-3 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 rounded-md font-semibold flex items-center gap-1 hover:text-emerald-300 transition-colors cursor-pointer text-[10px]">
          <span>Explore Logs for Timeframe</span>
          <ArrowRight class="h-3 w-3" />
        </button>
      </div>
    </div>

    <!-- Charts: loading state -->
    <template v-if="telemetry.initialLoading && (!telemetry.dashboardCharts || telemetry.dashboardCharts.length === 0)">
      <div class="flex flex-col items-center justify-center p-20 bg-zinc-900/50 border border-zinc-800 rounded-xl">
        <div class="h-10 w-10 border-4 border-t-emerald-500 border-zinc-800 rounded-full animate-spin mb-4" />
        <p class="text-zinc-400 text-xs font-mono">Aggregating real-time API performance telemetry...</p>
      </div>
    </template>

    <!-- Charts -->
    <template v-else>
      <!-- Section 1: Traffic + Latency -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-sm">
          <div class="flex justify-between items-center mb-4">
            <div>
              <h3 class="text-white font-medium text-base">Traffic Volume</h3>
              <p class="text-xs text-zinc-400">Success and failed calls aggregate • <span class="text-emerald-400 font-semibold" title="Click on the chart to filter by that time slot">Click slot to select time period</span></p>
            </div>
            <div class="flex items-center gap-3 text-xs text-zinc-400">
              <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 bg-emerald-500 rounded-full" /> Success</span>
              <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 bg-red-500 rounded-full" /> Errors</span>
            </div>
          </div>
          <div class="h-72 w-full cursor-pointer">
            <VChart v-if="trafficChartOptions" :option="trafficChartOptions" autoresize class="h-full w-full" @click="handleChartClick" @datazoom="handleDataZoom" />
          </div>
        </div>
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-sm">
          <div>
            <h3 class="text-white font-medium text-base">Average Latency Trend</h3>
            <p class="text-xs text-zinc-400">System-wide responses • <span class="text-indigo-400 font-semibold" title="Click on the chart to filter by that time slot">Click bar to select time period</span></p>
          </div>
          <div class="h-72 w-full mt-4 cursor-pointer">
            <VChart v-if="latencyChartOptions" :option="latencyChartOptions" autoresize class="h-full w-full" @click="handleChartClick" @datazoom="handleDataZoom" />
          </div>
        </div>
      </div>

      <!-- Section 2: Status codes + Endpoints -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 class="text-white font-medium text-base mb-1">Response Codes</h3>
            <p class="text-xs text-zinc-400 mb-4">Percentage and volume of returned HTTP status codes</p>
          </div>
          <div class="flex items-center justify-center h-48">
            <template v-if="bd?.statuses?.length">
              <VChart :option="pieChartOptions" autoresize class="h-full w-full" />
            </template>
            <p v-else class="text-xs text-zinc-400">No status data mapped</p>
          </div>
          <div class="mt-4 space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
            <div v-for="st in (bd?.statuses || []).slice(0, 4)" :key="st.code" class="flex justify-between items-center text-xs">
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-sm" :style="{ backgroundColor: getStatusColor(st.code) }" />
                <span class="text-white font-mono font-semibold">{{ st.code }}</span>
                <span class="text-zinc-400">{{ st.description }}</span>
              </div>
              <span class="text-white font-mono">{{ st.count }} calls</span>
            </div>
          </div>
        </div>
        <div class="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-sm">
          <div class="flex justify-between items-center mb-4">
            <div>
              <h3 class="text-white font-medium text-base">Heavy / Active Endpoints</h3>
              <p class="text-xs text-zinc-400">Active routes sorted by transactional load</p>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-xs">
              <thead>
                <tr class="border-b border-zinc-800 text-zinc-400 text-left">
                  <th class="pb-2 font-medium">Method</th>
                  <th class="pb-2 font-medium">Path</th>
                  <th class="pb-2 font-medium text-right">Transactions</th>
                  <th class="pb-2 font-medium text-right">Avg Latency</th>
                  <th class="pb-2 font-medium text-right">Error Rate</th>
                  <th class="pb-2 font-medium text-center">Action</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-zinc-800">
                <tr v-for="(ep, i) in (bd?.endpoints || [])" :key="i" class="hover:bg-zinc-800/40 transition-colors" @mouseenter="hoveredEndpoint=`${ep.method}-${ep.path}`" @mouseleave="hoveredEndpoint=null">
                  <td class="py-2.5 pr-3">
                    <span :class="['px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider font-mono', methodBadgeClass(ep.method)]">{{ ep.method }}</span>
                  </td>
                  <td class="py-2.5 max-w-[200px] truncate font-mono text-zinc-300">{{ ep.path }}</td>
                  <td class="py-2.5 text-right text-white font-mono font-semibold">{{ ep.hits }}</td>
                  <td class="py-2.5 text-right font-mono">
                    <span :class="ep.avgLatency > 500 ? 'text-rose-400 font-semibold' : ep.avgLatency > 200 ? 'text-amber-400' : 'text-zinc-400'">{{ ep.avgLatency }} ms</span>
                  </td>
                  <td class="py-2.5 text-right font-mono">
                    <span :class="['inline-block px-1.5 py-0.5 rounded text-[11px]', errorRateBadgeClass(ep.errorRate)]">{{ ep.errorRate }}%</span>
                  </td>
                  <td class="py-2.5 text-center">
                    <button @click="navigateToLogs('', ep.path)" class="text-emerald-500 hover:text-emerald-400 inline-flex items-center gap-1 cursor-pointer font-bold" title="Drill down to endpoint logs">
                      <span>Analyze</span>
                      <ArrowRight class="h-3.5 w-3.5" :class="hoveredEndpoint === `${ep.method}-${ep.path}` ? 'translate-x-1' : ''" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- AI Anomaly Chart -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-sm">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
          <div>
            <h3 class="text-white font-medium text-base inline-flex items-center gap-1.5">
              <Sparkles class="h-4.5 w-4.5 text-purple-400" />
              <span>AI Anomaly Score Trend</span>
            </h3>
            <p class="text-xs text-zinc-400">Past AI audits • <span class="text-purple-400 font-semibold">Click point to view logs</span></p>
          </div>
          <div v-if="telemetry.scanHistory.length" class="flex items-center gap-3.5 text-xs text-zinc-400 select-none">
            <span class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Latest Scan: <span class="font-bold text-white font-mono">{{ latestScan.anomalyScore }}</span> / 100
            </span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-1 bg-purple-500 rounded-full" /> Anomaly Score</span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-1 bg-green-500 rounded-full" /> Triggered Alerts</span>
          </div>
        </div>
        <template v-if="telemetry.scanHistory.length">
          <div class="h-64 w-full cursor-pointer">
            <VChart :option="anomalyChartOptions" autoresize class="h-full w-full" />
          </div>
        </template>
        <template v-else>
          <div class="flex flex-col items-center justify-center py-12 px-6 bg-zinc-950/40 border border-dashed border-zinc-800 rounded-xl text-center">
            <Activity class="h-8 w-8 text-zinc-500 mb-2.5 animate-pulse" />
            <span class="text-white text-xs font-semibold block">No Scan History Records Available</span>
            <p class="text-zinc-400 text-[11px] max-w-sm mt-1 mx-auto leading-relaxed">Activate AI anomaly analysis in the "Alerts & Policy" panel. Your prior scanning score runs will automatically map here.</p>
          </div>
        </template>
      </div>

      <!-- Quick Actions -->
      <div class="p-4 bg-zinc-900 border border-zinc-800 rounded-xl flex flex-wrap gap-4 items-center justify-between">
        <div class="flex items-center gap-2">
          <ShieldCheck class="text-emerald-500 h-5 w-5" />
          <span class="text-xs text-zinc-300">All gateways reporting normally. Active limits are strictly enforced server-side.</span>
        </div>
        <div class="flex gap-2">
          <button @click="navigateToLogs('', '')" class="text-zinc-950 bg-zinc-100 hover:bg-zinc-200 text-xs px-3.5 py-2 rounded-lg font-semibold cursor-pointer flex items-center gap-1 transition-all">
            <span>Raw Logs Explorer</span>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import { useTelemetryStore } from "../stores/telemetry"
import VChart from "vue-echarts"
import "echarts"
import { Calendar, Clock, X, ArrowRight, Sparkles, Activity, ShieldCheck } from "lucide-vue-next"

const router = useRouter()
const telemetry = useTelemetryStore()

const hoveredEndpoint = ref(null)

const bd = computed(() => telemetry.dashboardBreakdown)
const latestScan = computed(() => {
  const h = [...telemetry.scanHistory]
  h.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  return h[0] || { anomalyScore: 0 }
})

function formatTime(ms) {
  return new Date(ms).toLocaleString().replace(",", " •")
}

function clearLens() {
  telemetry.clearTimeRange()
}

function navigateToLogs(searchVal, pathFilter) {
  router.push({ name: "logs", query: { search: searchVal || pathFilter } })
}

function exploreLogs() {
  if (!telemetry.timeRange) return
  router.push({
    name: "logs",
    query: {
      startMs: String(telemetry.timeRange.from),
      endMs: String(telemetry.timeRange.to),
    },
  })
}

let dataZoomTimer = null

function handleChartClick(params) {
  if (!params) return
  let idx = params.dataIndex
  if (idx == null && params.name != null) {
    idx = telemetry.dashboardCharts.findIndex(
      d => d.timeLabel === String(params.name)
    )
  }
  if (idx == null || idx < 0) return
  const point = telemetry.dashboardCharts[idx]
  if (!point) return
  const ts = new Date(point.timestamp || point.timeLabel).getTime()
  if (isNaN(ts)) return
  telemetry.setTimeRange(ts - 1800000, ts + 1800000)
}

function resolveZoomIndex(value) {
  if (value == null) return null
  const labels = telemetry.dashboardCharts.map(d => d.timeLabel)
  if (typeof value === "number" && Number.isFinite(value)) {
    const idx = Math.min(labels.length - 1, Math.max(0, Math.round(value)))
    return idx >= 0 ? idx : null
  }
  const exact = labels.indexOf(String(value))
  return exact >= 0 ? exact : null
}

function handleDataZoom(params) {
  const batch = params?.batch || [params]
  const zoom = batch[0]
  if (!zoom) return

  let startIdx = null
  let endIdx = null

  if (zoom.startValue != null && zoom.endValue != null) {
    startIdx = resolveZoomIndex(zoom.startValue)
    endIdx = resolveZoomIndex(zoom.endValue)
  }

  if (startIdx == null && zoom.start != null && zoom.end != null) {
    const total = telemetry.dashboardCharts.length
    if (total > 0) {
      startIdx = Math.max(0, Math.round(total * zoom.start / 100))
      endIdx = Math.min(total - 1, Math.round(total * zoom.end / 100))
    }
  }

  if (startIdx == null || endIdx == null) return

  const startTs = new Date(telemetry.dashboardCharts[startIdx].timestamp).getTime()
  const endTs = new Date(telemetry.dashboardCharts[endIdx].timestamp).getTime()
  if (isNaN(startTs) || isNaN(endTs)) return

  const from = Math.min(startTs, endTs)
  const to = Math.max(startTs, endTs)

  if (telemetry.timeRange &&
      Math.abs(telemetry.timeRange.from - from) < 1000 &&
      Math.abs(telemetry.timeRange.to - (to + 3600000)) < 1000) {
    return
  }

  if (dataZoomTimer) clearTimeout(dataZoomTimer)
  dataZoomTimer = setTimeout(() => {
    telemetry.setTimeRange(from, to + 3600000)
  }, 250)
}

onUnmounted(() => {
  if (dataZoomTimer) clearTimeout(dataZoomTimer)
})

const STATUS_COLORS = {
  "200": "#10b981", "201": "#059669", "304": "#3b82f6", "400": "#f59e0b",
  "401": "#fbbf24", "403": "#f97316", "404": "#ef4444", "429": "#ec4899",
  "500": "#dc2626", "503": "#b91c1c",
}
function getStatusColor(code) { return STATUS_COLORS[String(code)] || "#8b949e" }

function methodBadgeClass(m) {
  if (m === "POST") return "bg-amber-500/10 text-amber-400 border border-amber-500/20"
  if (m === "GET") return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
  return "bg-zinc-800 text-zinc-400"
}

function errorRateBadgeClass(r) {
  if (r > 5) return "bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold"
  if (r > 0) return "bg-amber-500/10 text-amber-400"
  return "bg-emerald-500/10 text-emerald-400"
}

// Chart options
const trafficChartOptions = computed(() => {
  if (!telemetry.dashboardCharts?.length) return null
  return {
    tooltip: { trigger: "axis", backgroundColor: "#18181b", borderColor: "#27272a", borderRadius: 8, textStyle: { fontSize: 11 } },
    legend: { show: false },
    grid: { top: 10, right: 10, left: 40, bottom: 30 },
    dataZoom: [
      { type: "inside", xAxisIndex: 0, throttle: 50 },
      { type: "slider", xAxisIndex: 0, bottom: 0, height: 18, borderColor: "#27272a", fillerColor: "rgba(16,185,129,0.18)", textStyle: { color: "#71717a" } },
    ],
    xAxis: { type: "category", data: telemetry.dashboardCharts.map(d => d.timeLabel), axisLabel: { color: "#71717a", fontSize: 10 }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { type: "value", splitLine: { lineStyle: { color: "#27272a", type: "dashed" } }, axisLabel: { color: "#71717a", fontSize: 10 } },
    series: [
      { name: "Success", type: "line", data: telemetry.dashboardCharts.map(d => d.success), smooth: true, triggerLineEvent: true, lineStyle: { color: "#10b981", width: 2 }, areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "rgba(16,185,129,0.25)" }, { offset: 1, color: "rgba(16,185,129,0)" }] } }, itemStyle: { color: "#10b981" } },
      { name: "Errors", type: "line", data: telemetry.dashboardCharts.map(d => d.errors), smooth: true, triggerLineEvent: true, lineStyle: { color: "#ef4444", width: 1.5 }, areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "rgba(239,68,68,0.25)" }, { offset: 1, color: "rgba(239,68,68,0)" }] } }, itemStyle: { color: "#ef4444" } },
    ],
  }
})

const latencyChartOptions = computed(() => {
  if (!telemetry.dashboardCharts?.length) return null
  return {
    tooltip: { trigger: "axis", backgroundColor: "#18181b", borderColor: "#27272a", borderRadius: 8, textStyle: { fontSize: 11 } },
    grid: { top: 10, right: 10, left: 40, bottom: 30 },
    dataZoom: [
      { type: "inside", xAxisIndex: 0, throttle: 50 },
      { type: "slider", xAxisIndex: 0, bottom: 0, height: 18, borderColor: "#27272a", fillerColor: "rgba(99,102,241,0.2)", textStyle: { color: "#71717a" } },
    ],
    xAxis: { type: "category", data: telemetry.dashboardCharts.map(d => d.timeLabel), axisLabel: { color: "#71717a", fontSize: 10 }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { type: "value", splitLine: { lineStyle: { color: "#27272a", type: "dashed" } }, axisLabel: { color: "#71717a", fontSize: 10 }, axisLabel: { formatter: "{value} ms" } },
    series: [{ type: "bar", data: telemetry.dashboardCharts.map(d => d.avgLatency), itemStyle: { color: "#6366f1", borderRadius: [4, 4, 0, 0] } }],
  }
})

const pieChartOptions = computed(() => {
  const statuses = bd.value?.statuses
  if (!statuses?.length) return null
  return {
    tooltip: { trigger: "item", backgroundColor: "#18181b", borderColor: "#27272a", borderRadius: 8, formatter: (p) => `${p.name}<br/>Count: <strong>${p.value}</strong>` },
    series: [{
      type: "pie", radius: ["55%", "75%"], center: ["50%", "50%"], avoidLabelOverlap: true,
      data: statuses.map(s => ({ name: `HTTP ${s.code}`, value: s.count, itemStyle: { color: getStatusColor(s.code) } })),
      label: { show: false }, emphasis: { scale: false },
    }],
  }
})

const anomalyChartOptions = computed(() => {
  if (!telemetry.scanHistory.length) return null
  const sorted = [...telemetry.scanHistory].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
  return {
    tooltip: { trigger: "axis", backgroundColor: "#18181b", borderColor: "#27272a", borderRadius: 8 },
    legend: { data: ["Anomaly Score", "Alerts Count"], textStyle: { color: "#a1a1aa", fontSize: 10 }, icon: "circle" },
    grid: { top: 30, right: 10, left: 40, bottom: 20 },
    xAxis: { type: "category", data: sorted.map(d => new Date(d.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })), axisLabel: { color: "#71717a", fontSize: 10 }, axisLine: { show: false } },
    yAxis: { type: "value", min: 0, max: 100, splitLine: { lineStyle: { color: "#27272a", type: "dashed" } }, axisLabel: { color: "#71717a", fontSize: 10 } },
    series: [
      { name: "Anomaly Score", type: "line", data: sorted.map(d => d.anomalyScore), smooth: true, lineStyle: { color: "#a855f7", width: 2.5 }, itemStyle: { color: "#a855f7" }, symbol: "circle", symbolSize: 6 },
      { name: "Alerts Count", type: "line", data: sorted.map(d => d.detectedAlertsCount), smooth: true, lineStyle: { color: "#22c55e", width: 1.5 }, itemStyle: { color: "#22c55e" }, symbol: "circle", symbolSize: 4 },
    ],
  }
})
</script>
