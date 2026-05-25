<template>
  <div class="space-y-6">
    <!-- Simulator Controls -->
    <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div class="space-y-1">
          <h3 class="text-white font-semibold text-base inline-flex items-center gap-2">
            <Terminal class="text-emerald-500 h-5 w-5" />
            <span>Real-Time Traffic Simulator</span>
          </h3>
          <p class="text-xs text-zinc-400">Use our built-in simulator background client to generate stream activity. You can configure ticks or pause feed.</p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex bg-zinc-950 border border-zinc-800 rounded-xl p-1 shrink-0">
            <button @click="toggleSim(true)" :class="['px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all flex items-center gap-1', simActive ? 'bg-emerald-500/15 text-emerald-400 font-bold' : 'text-zinc-500']">
              <Play class="h-3.5 w-3.5" /><span>Active</span>
            </button>
            <button @click="toggleSim(false)" :class="['px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all flex items-center gap-1', !simActive ? 'bg-rose-500/15 text-rose-400 font-bold' : 'text-zinc-500']">
              <Pause class="h-3.5 w-3.5" /><span>Paused</span>
            </button>
          </div>
          <div class="flex bg-zinc-950 border border-zinc-800 rounded-xl p-1 shrink-0">
            <button v-for="sp in speedOptions" :key="sp.value" @click="setSimSpeed(sp.value)" :class="['px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all', simSpeed === sp.value ? 'bg-zinc-800 text-white' : 'text-zinc-500']" :title="sp.title">
              <FastForward v-if="sp.value === 900" class="h-3 w-3 inline mr-0.5" />
              <span>{{ sp.label }}</span>
            </button>
          </div>
        </div>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6 pt-5 border-t border-zinc-800/60 text-xs">
        <div class="bg-zinc-950 border border-zinc-800/60 rounded-xl p-3">
          <span class="text-zinc-500 font-mono font-bold uppercase text-[9px] tracking-wider">Simulation State</span>
          <div class="text-white font-semibold mt-1 flex items-center gap-1.5">
            <span :class="['w-2.5 h-2.5 rounded-full', true ? 'bg-emerald-500 animate-ping' : 'bg-rose-500']" />
            <span>{{ simActive ? 'STREAMING ACTIVE' : 'STREAM MUTED' }}</span>
          </div>
        </div>
        <div class="bg-zinc-950 border border-zinc-800/60 rounded-xl p-3">
          <span class="text-zinc-500 font-mono font-bold uppercase text-[9px] tracking-wider">Ingest Frequency</span>
          <div class="text-white font-mono font-semibold mt-1">1 log / {{ simSpeed }}ms</div>
        </div>
        <div class="bg-zinc-950 border border-zinc-800/60 rounded-xl p-3">
          <span class="text-zinc-500 font-mono font-bold uppercase text-[9px] tracking-wider">Simulated Sources</span>
          <div class="text-white font-semibold mt-1">4 core modules active</div>
        </div>
      </div>
    </div>

    <!-- Sources + Import -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Sources List -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-4">
        <div class="flex justify-between items-center">
          <div>
            <h4 class="text-white font-semibold text-sm">Ingested API Channels</h4>
            <p class="text-xs text-zinc-500">API adapters streaming telemetry</p>
          </div>
          <button @click="showAddSource = !showAddSource" class="text-white text-xs font-semibold bg-zinc-800 hover:bg-zinc-700 hover:border-zinc-500 border border-zinc-700 px-3 py-1.5 rounded-lg cursor-pointer transition-all flex items-center gap-1">
            <Plus class="h-4 w-4" /><span>Hook Adapter</span>
          </button>
        </div>
        <form v-if="showAddSource" @submit.prevent="addSource" class="bg-zinc-950 border border-zinc-800 p-4 rounded-xl space-y-3">
          <h5 class="text-white text-xs font-semibold">Configure Log Endpoint Channel</h5>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider block mb-1">Source Endpoint Title</label>
              <input type="text" placeholder="e.g. Stripe Gateway" v-model="sourceName" class="w-full bg-zinc-900 border border-zinc-800 rounded p-2 text-white focus:outline-none focus:border-emerald-500" required />
            </div>
            <div>
              <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider block mb-1">Ingest Protocol Type</label>
              <select v-model="sourceType" class="w-full bg-zinc-900 border border-zinc-800 rounded p-2 text-white focus:outline-none focus:border-emerald-500 font-medium">
                <option value="gateway">API Gateway (Server REST)</option>
                <option value="webhook">Webhook Listener (Push)</option>
                <option value="agent">Host daemon Agent</option>
                <option value="custom">Custom JSON Endpoint</option>
              </select>
            </div>
          </div>
          <div class="flex justify-end gap-2 text-xs pt-1">
            <button type="button" @click="showAddSource = false" class="px-2.5 py-1.5 hover:bg-zinc-800 text-zinc-400 rounded cursor-pointer font-medium">Cancel</button>
            <button type="submit" class="bg-zinc-100 hover:bg-zinc-200 text-zinc-950 font-bold px-3 py-1.5 rounded cursor-pointer">Add Adapter</button>
          </div>
        </form>
        <div class="space-y-2.5 max-h-96 overflow-y-auto custom-scrollbar">
          <div v-for="s in telemetry.sources" :key="s.name" class="bg-zinc-950 border border-zinc-800/80 p-3.5 rounded-xl flex items-center justify-between gap-4 shadow-sm">
            <div class="flex items-center gap-3">
              <div :class="['p-2 rounded-lg', s.status === 'inactive' ? 'bg-zinc-800 text-zinc-500' : 'bg-emerald-500/10 text-emerald-400']">
                <Server class="h-4 w-4" />
              </div>
              <div>
                <div class="flex items-center gap-1.5">
                  <span class="text-white font-semibold text-xs font-mono">{{ s.name }}</span>
                  <span :class="['text-[9px] px-1.5 py-0.5 border rounded font-bold uppercase', s.status === 'inactive' ? 'bg-zinc-800 border-zinc-700 text-zinc-400' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400']">{{ s.status }}</span>
                </div>
                <div class="text-[10px] text-zinc-500 font-mono mt-0.5 flex items-center gap-1">
                  <Lock class="h-3 w-3" />
                  <span>secretToken: {{ s.apiKeySnippet }}</span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-[10px] text-zinc-400 font-mono hidden sm:inline">{{ s.totalLogsReceived || 0 }} items</span>
              <button @click="toggleSource(s.name, s.status)" :class="['px-2 py-1 rounded text-[10px] border font-semibold cursor-pointer transition-colors', s.status === 'active' ? 'bg-amber-500/10 border-amber-500/10 text-amber-400 hover:bg-amber-500/25' : 'bg-emerald-500/10 border-emerald-500/10 text-emerald-400 hover:bg-emerald-500/25']">
                {{ s.status === 'active' ? 'Disable' : 'Enable' }}
              </button>
              <button @click="removeSource(s.name)" class="text-zinc-500 hover:text-rose-400 hover:border-rose-500/20 border border-transparent p-1 rounded transition-colors cursor-pointer" title="Delete source">
                <XCircle class="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Manual Ingestion Console -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 flex flex-col justify-between">
        <div>
          <h4 class="text-white font-semibold text-sm">Manual Ingestion Console</h4>
          <p class="text-xs text-zinc-500 mb-4">Paste API JSON transaction trace logs or import CSV templates directly.</p>
        </div>
        <div class="space-y-4">
          <div class="space-y-1.5">
            <div class="flex justify-between items-center text-xs">
              <span class="text-zinc-500 font-mono text-[9px] font-bold uppercase tracking-wider">Batch Ingestion Presets</span>
              <div class="flex gap-1">
                <button v-for="p in presets" :key="p.id" @click="choosePreset(p.id)" :class="['px-2 py-0.5 rounded text-[10px] border cursor-pointer font-mono font-medium transition-colors', pastePreset === p.id ? 'bg-emerald-500/15 border-emerald-500 text-emerald-400 font-bold' : 'bg-transparent border-zinc-800 text-zinc-400 hover:text-white']">{{ p.label }}</button>
              </div>
            </div>
            <textarea v-model="logPayload" placeholder='Paste raw JSON log or batch array here. E.g.: [{"method":"GET","path":"/test","status":200,"latency":45}]' class="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-2.5 font-mono text-[10px] h-36 focus:outline-none focus:border-emerald-500 text-zinc-300 placeholder-zinc-600 custom-scrollbar resize-none font-medium" />
          </div>
          <div class="space-y-1.5">
            <span class="text-xs text-zinc-500 font-mono font-bold uppercase text-[9px] block">Import Telemetry Log File (CSV)</span>
            <div class="border border-dashed border-zinc-800 hover:border-emerald-500/50 rounded-xl p-4 text-center cursor-pointer relative bg-zinc-950/40 hover:bg-zinc-950/80 group transition-all">
              <input type="file" accept=".csv" @change="handleCSVUpload" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
              <Upload class="h-5 w-5 mx-auto text-zinc-400 group-hover:text-emerald-400 transition-colors mb-1.5" />
              <span class="text-white font-medium text-xs block">{{ csvFileName || "Select custom log file (.csv)" }}</span>
              <span class="text-zinc-500 text-[10px] font-mono mt-0.5 block">Required headings: method, path, status, latency</span>
            </div>
          </div>
          <div v-if="parseError" class="p-3 bg-rose-500/5 border border-rose-500/20 rounded-xl flex items-start gap-2 text-rose-400 text-xs">
            <AlertCircle class="h-4 w-4 shrink-0 mt-0.5" /><span>{{ parseError }}</span>
          </div>
          <div v-if="parseSuccessMessage" class="p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-xl flex items-start gap-2 text-emerald-400 text-xs text-left">
            <CheckCircle2 class="h-4 w-4 shrink-0 mt-0.5" /><span>{{ parseSuccessMessage }}</span>
          </div>
          <div class="flex justify-end pt-1">
            <button @click="ingestPaste" :disabled="!logPayload.trim()" :class="['px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap cursor-pointer select-none transition-all flex items-center gap-1.5', logPayload.trim() ? 'bg-zinc-100 text-zinc-950 hover:bg-zinc-200' : 'bg-transparent text-zinc-500 border border-zinc-800 cursor-not-allowed']">
              <FileText class="h-3.5 w-3.5" /><span>Ingest Custom Logs</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { useTelemetryStore } from "../stores/telemetry"
import api from "../api"
import { Terminal, Play, Pause, FastForward, Plus, Server, Lock, XCircle, Upload, AlertCircle, CheckCircle2, FileText } from "lucide-vue-next"

const telemetry = useTelemetryStore()
const simActive = ref(true)
const simSpeed = ref(3000)
const showAddSource = ref(false)
const sourceName = ref("")
const sourceType = ref("gateway")
const logPayload = ref("")
const pastePreset = ref("")
const csvFileName = ref("")
const parseError = ref(null)
const parseSuccessMessage = ref(null)

const speedOptions = [
  { label: "Slow", value: 6000, title: "Log generated every 6 seconds" },
  { label: "Medium", value: 3000, title: "Log generated every 3 seconds" },
  { label: "Fast", value: 900, title: "Fast log streaming every 900ms" },
]

const presets = [
  { id: "ddos", label: "DDoS Peak" },
  { id: "slow_db", label: "Slow DB" },
  { id: "latency", label: "Data Load" },
]

function toggleSim(active) {
  api.post("armure_apim_sentinel.api.sources.toggle_simulation", { active }).catch(console.error)
}

function setSimSpeed(speed) {
  simSpeed.value = speed
  api.post("armure_apim_sentinel.api.sources.set_simulation_speed", { speed }).catch(console.error)
}

async function addSource() {
  try {
    await api.post("armure_apim_sentinel.api.sources.add_source", { name: sourceName.value, type: sourceType.value })
    showAddSource.value = false
    sourceName.value = ""
    sourceType.value = "gateway"
    await telemetry.fetchSources()
  } catch (e) { console.error(e) }
}

async function toggleSource(name, currentStatus) {
  const next = currentStatus === "active" ? "inactive" : "active"
  try {
    await api.post("armure_apim_sentinel.api.sources.toggle_source_status", { source_name: name, status: next })
    await telemetry.fetchSources()
  } catch (e) { console.error(e) }
}

async function removeSource(name) {
  try {
    await api.post("armure_apim_sentinel.api.sources.remove_source", { source_name: name })
    await telemetry.fetchSources()
  } catch (e) { console.error(e) }
}

function choosePreset(id) {
  pastePreset.value = id
  parseError.value = null
  parseSuccessMessage.value = null
  const now = new Date().toISOString()
  const older1 = new Date(Date.now() - 5000).toISOString()
  const older2 = new Date(Date.now() - 10000).toISOString()
  if (id === "ddos") {
    logPayload.value = JSON.stringify([
      { timestamp: now, method: "POST", path: "/api/v1/users/login", status: 401, latency: 15, source: "Auth Service", ip: "34.120.45.99", userAgent: "curl/8.4.0", payloadSize: 450, responseBody: '{"error":"Invalid login credentials"}' },
      { timestamp: now, method: "POST", path: "/api/v1/users/login", status: 401, latency: 12, source: "Auth Service", ip: "34.120.45.99", userAgent: "curl/8.4.0", payloadSize: 450, responseBody: '{"error":"Invalid login credentials"}' },
      { timestamp: older1, method: "POST", path: "/api/v1/users/login", status: 401, latency: 18, source: "Auth Service", ip: "34.120.45.99", userAgent: "curl/8.4.0", payloadSize: 450, responseBody: '{"error":"Invalid login credentials"}' },
      { timestamp: older2, method: "POST", path: "/api/v1/users/login", status: 429, latency: 2, source: "Auth Service", ip: "34.120.45.99", userAgent: "curl/8.4.0", payloadSize: 450, responseBody: '{"error":"Too Many Requests"}' },
    ], null, 2)
  } else if (id === "slow_db") {
    logPayload.value = JSON.stringify([
      { timestamp: now, method: "GET", path: "/api/v1/billing/invoices", status: 500, latency: 4500, source: "Billing Gateway", ip: "198.51.100.12", userAgent: "PostmanRuntime/7.35.0", payloadSize: 0, responseBody: '{"error":"Database connection timeout after 5000ms"}' },
      { timestamp: older1, method: "GET", path: "/api/v1/billing/invoices", status: 500, latency: 4800, source: "Billing Gateway", ip: "198.51.100.12", userAgent: "PostmanRuntime/7.35.0", payloadSize: 0, responseBody: '{"error":"Database connection timeout after 5000ms"}' },
    ], null, 2)
  } else if (id === "latency") {
    logPayload.value = JSON.stringify([
      { timestamp: now, method: "POST", path: "/api/v1/analytics/stream", status: 200, latency: 1200, source: "Data Collector", ip: "8.8.8.8", userAgent: "Data-Collector-Bot/1.2", payloadSize: 25000, responseBody: '{"status":"ok"}' },
      { timestamp: older1, method: "POST", path: "/api/v1/analytics/stream", status: 200, latency: 1550, source: "Data Collector", ip: "8.8.8.8", userAgent: "Data-Collector-Bot/1.2", payloadSize: 22000, responseBody: '{"status":"ok"}' },
    ], null, 2)
  }
}

async function ingestPaste() {
  parseError.value = null
  parseSuccessMessage.value = null
  if (!logPayload.value.trim()) return
  try {
    const parsed = JSON.parse(logPayload.value)
    await api.post("armure_apim_sentinel.api.logs.ingest_logs", { logs: parsed })
    parseSuccessMessage.value = "Pasted logs ingested successfully! Check telemetry metrics and triggered rules."
    logPayload.value = ""
    pastePreset.value = ""
    await telemetry.fetchSources()
  } catch (e) {
    parseError.value = "Log payload must be a valid JSON array or object. Err: " + e.message
  }
}

function handleCSVUpload(e) {
  parseError.value = null
  parseSuccessMessage.value = null
  const file = e.target.files?.[0]
  if (!file) return
  csvFileName.value = file.name
  const reader = new FileReader()
  reader.onload = async (event) => {
    const text = event.target?.result
    try {
      const lines = text.split("\n").map(l => l.trim()).filter(l => l.length > 0)
      if (lines.length < 2) throw new Error("CSV file requires a header and at least 1 log row.")
      const headers = lines[0].split(",").map(h => h.trim().replace(/^"|"$/g, ""))
      const parsedLogs = []
      for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(",").map(c => c.trim().replace(/^"|"$/g, ""))
        const item = {}
        headers.forEach((h, idx) => {
          let val = cols[idx]
          if (["status", "latency", "payloadSize"].includes(h)) val = parseInt(val) || 0
          item[h] = val
        })
        if (!item.timestamp) item.timestamp = new Date().toISOString()
        if (!item.method) item.method = "GET"
        if (!item.path) item.path = "/api/csv-upload"
        if (!item.status) item.status = 200
        if (!item.latency) item.latency = 45
        if (!item.source) item.source = "CSV Ingester"
        parsedLogs.push(item)
      }
      await api.post("armure_apim_sentinel.api.logs.ingest_logs", { logs: parsedLogs })
      parseSuccessMessage.value = `Processed & uploaded ${parsedLogs.length} logs successfully from CSV file "${file.name}"!`
      csvFileName.value = ""
      await telemetry.fetchSources()
    } catch (err) {
      parseError.value = `CSV Parsing Error: ${err.message}. Format: method,path,status,latency,source,ip`
    }
  }
  reader.readAsText(file)
}

onMounted(() => telemetry.fetchSources())
</script>
