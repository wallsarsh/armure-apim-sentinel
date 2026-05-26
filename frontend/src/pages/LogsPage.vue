<template>
  <div class="space-y-4">
    <!-- Filter Row 1: Search & Export -->
    <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-4 selection:bg-emerald-500/20">
      <div class="flex flex-col md:flex-row gap-3">
        <div class="relative flex-1">
          <Search class="absolute left-3.5 top-2.5 h-4.5 w-4.5 text-zinc-500" />
          <input type="text" placeholder="Search by path, IP host, trace ID, user GUID..." v-model="searchQuery" class="w-full bg-zinc-950 border border-zinc-800 rounded-xl pl-10 pr-4 py-2 text-sm text-zinc-100 focus:outline-none focus:border-emerald-500 font-medium placeholder-zinc-500" />
        </div>
        <div class="flex gap-2">
          <button @click="showExportPreview = true" :disabled="!telemetry.logs.length" :class="['px-4 py-2 border rounded-xl text-xs font-semibold cursor-pointer transition-all flex items-center gap-1.5 font-mono select-none', telemetry.logs.length ? 'bg-zinc-100 text-zinc-950 hover:bg-zinc-200' : 'bg-transparent border-zinc-800 text-zinc-600 cursor-not-allowed']">
            <FileSpreadsheet class="h-4 w-4" />
            <span>Export CSV ({{ telemetry.logs.length }})</span>
          </button>
        </div>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-5 gap-3.5 text-xs">
        <div class="space-y-1 font-mono">
          <label class="text-zinc-500 uppercase font-bold text-[10px] tracking-wider">System Source</label>
          <select v-model="selectedSource" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-zinc-100 focus:outline-none focus:border-emerald-500">
            <option value="All Sources">All Sources</option>
            <option v-for="s in sources" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="space-y-1 font-mono">
          <label class="text-zinc-500 uppercase font-bold text-[10px] tracking-wider">HTTP Status</label>
          <select v-model="selectedStatus" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-zinc-100 focus:outline-none focus:border-emerald-500">
            <option value="All Statuses">All Statuses</option>
            <option value="2xx Success">2xx Success</option>
            <option value="429 Rate Limited">429 Rate Limited</option>
            <option value="4xx Client Errors">4xx Client Errors</option>
            <option value="5xx Server Errors">5xx Server Errors</option>
          </select>
        </div>
        <div class="space-y-1 font-mono">
          <label class="text-zinc-500 uppercase font-bold text-[10px] tracking-wider">Request Method</label>
          <select v-model="selectedMethod" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-zinc-100 focus:outline-none focus:border-emerald-500">
            <option value="All Methods">All Methods</option>
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="DELETE">DELETE</option>
          </select>
        </div>
        <div class="space-y-1 font-mono">
          <label class="text-zinc-500 uppercase font-bold text-[10px] tracking-wider">Min Latency (ms)</label>
          <input type="number" placeholder="0" v-model="minLatency" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-zinc-100 focus:outline-none focus:border-emerald-500" />
        </div>
        <div class="space-y-1 font-mono">
          <label class="text-zinc-500 uppercase font-bold text-[10px] tracking-wider">Max Latency (ms)</label>
          <input type="number" placeholder="e.g. 5000" v-model="maxLatency" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-zinc-100 focus:outline-none focus:border-emerald-500" />
        </div>
      </div>
      <div class="border-t border-zinc-800/60 pt-4 text-xs">
        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 font-mono">
          <div class="flex items-center gap-2 text-zinc-400 select-none font-medium text-xs">
            <Calendar class="h-4 w-4 text-emerald-400" />
            <span class="text-zinc-300 font-bold uppercase tracking-wider text-[10px]">Time Period Filter</span>
          </div>
          <div class="flex flex-wrap items-center gap-3 w-full lg:w-auto">
            <div class="flex flex-col sm:flex-row items-start sm:items-center gap-2">
              <span class="text-[10px] text-zinc-500 uppercase font-bold tracking-wider sm:w-10">Start:</span>
              <input type="datetime-local" v-model="startTime" class="w-full sm:w-auto bg-zinc-950 border border-zinc-800 hover:border-zinc-700 focus:border-emerald-500 rounded-lg p-2 text-zinc-100 focus:outline-none text-xs font-mono transition-colors" />
            </div>
            <div class="flex flex-col sm:flex-row items-start sm:items-center gap-2">
              <span class="text-[10px] text-zinc-500 uppercase font-bold tracking-wider sm:w-10">End:</span>
              <input type="datetime-local" v-model="endTime" class="w-full sm:w-auto bg-zinc-950 border border-zinc-800 hover:border-zinc-700 focus:border-emerald-500 rounded-lg p-2 text-zinc-100 focus:outline-none text-xs font-mono transition-colors" />
            </div>
            <button v-if="startTime || endTime" @click="startTime=''; endTime=''" class="px-3 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 rounded-lg text-xs font-semibold flex items-center gap-1 hover:text-rose-300 transition-all cursor-pointer h-[34px]">
              <X class="h-3.5 w-3.5" />
              <span>Reset Time</span>
            </button>
          </div>
          <div v-if="startTime && endTime" class="text-[10px] text-emerald-400 font-mono bg-emerald-500/5 px-2.5 py-1.5 rounded-lg border border-emerald-500/10 flex items-center gap-1.5 w-full lg:w-auto lg:ml-auto">
            <Clock class="h-3.5 w-3.5 shrink-0" />
            <span class="truncate">Selection Active: Narrowing log traces</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Log Table -->
    <div class="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden shadow-sm">
      <div class="overflow-x-auto">
        <table class="min-w-full text-xs text-left">
          <thead>
            <tr class="border-b border-zinc-800 text-zinc-400">
              <th class="py-3 px-4 font-semibold">Status</th>
              <th class="py-3 px-4 font-semibold">Method</th>
              <th class="py-3 px-4 font-semibold">Path</th>
              <th class="py-3 px-4 font-semibold">Source</th>
              <th class="py-3 px-4 font-semibold">Client IP</th>
              <th class="py-3 px-4 font-semibold text-right">Latency</th>
              <th class="py-3 px-4 font-semibold text-right">Timestamp</th>
              <th class="py-3 px-4 font-semibold text-center">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800">
            <tr v-if="!telemetry.logs.length">
              <td colspan="8" class="py-12 text-center text-zinc-500">No API log traces match the configured transaction filters.</td>
            </tr>
            <tr v-for="log in telemetry.logs" :key="log.id" class="hover:bg-zinc-800/20 transition-colors">
              <td class="py-3 px-4">
                <span :class="['px-2 py-0.5 rounded text-[10px] font-bold font-mono inline-block', getStatusStyle(log.status)]">{{ log.status }}</span>
              </td>
              <td class="py-3 px-4">
                <span :class="['px-1.5 py-0.5 rounded text-[10px] font-semibold font-mono uppercase', getMethodStyle(log.method)]">{{ log.method }}</span>
              </td>
              <td class="py-3 px-4 max-w-[180px] break-all truncate font-mono text-zinc-300" :title="log.path">{{ log.path }}</td>
              <td class="py-3 px-4 font-mono text-zinc-400">{{ log.source }}</td>
              <td class="py-3 px-4 font-mono text-zinc-500">{{ log.ip }}</td>
              <td class="py-3 px-4 text-right font-mono text-white font-medium">
                <span :class="log.latency > 1000 ? 'text-rose-400 font-semibold' : log.latency > 300 ? 'text-amber-400' : 'text-zinc-400'">{{ log.latency }} ms</span>
              </td>
              <td class="py-3 px-4 text-right text-zinc-500 font-mono whitespace-nowrap">{{ formatTime(log.timestamp) }}</td>
              <td class="py-3 px-4 text-center">
                <button @click="openInspector(log)" class="text-zinc-100 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700/85 px-2.5 py-1 rounded text-[11px] font-semibold inline-flex items-center gap-1 cursor-pointer transition-colors">
                  <Eye class="h-3 w-3" />
                  <span>Inspect</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Inspector Drawer -->
    <template v-if="selectedLog">
      <div class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex justify-end">
        <div class="w-full max-w-2xl bg-zinc-950 h-full overflow-y-auto border-l border-zinc-800 shadow-2xl flex flex-col justify-between selection:bg-emerald-500/20 text-xs custom-scrollbar">
          <div>
            <div class="p-5 border-b border-zinc-800 flex justify-between items-center bg-zinc-900">
              <div class="flex items-center gap-2.5">
                <Terminal class="text-zinc-400 h-5 w-5" />
                <div>
                  <h4 class="text-white font-bold text-sm">Trace Inspector</h4>
                  <p class="text-[10px] text-zinc-500 font-mono">{{ selectedLog.id }}</p>
                </div>
              </div>
              <button @click="closeInspector" class="p-1.5 hover:bg-zinc-800 text-zinc-400 hover:text-white rounded-lg transition-colors cursor-pointer">
                <X class="h-4 w-4" />
              </button>
            </div>
            <div class="p-6 space-y-6 flex-1 select-text">
              <div class="bg-zinc-900 border border-zinc-800 p-4 rounded-xl space-y-3.5">
                <div class="flex flex-wrap gap-2 justify-between items-center pb-3 border-b border-zinc-800/60">
                  <span :class="['px-2.5 py-1 text-xs font-bold font-mono rounded', getStatusStyle(selectedLog.status)]">HTTP {{ selectedLog.status }}</span>
                  <span class="text-zinc-500 font-mono">{{ selectedLog.source }}</span>
                </div>
                <div class="space-y-1 font-mono">
                  <span class="text-[10px] text-zinc-500 uppercase font-bold tracking-wider">REQUEST URI</span>
                  <div class="text-white text-base font-bold flex items-center gap-2">
                    <span class="text-emerald-500 font-black">{{ selectedLog.method }}</span>
                    <span class="text-gray-100">{{ selectedLog.path }}</span>
                  </div>
                </div>
              </div>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
                <div class="bg-zinc-900 border border-zinc-800/80 p-3 rounded-lg">
                  <span class="text-zinc-500 text-[10px] uppercase font-bold tracking-wider flex items-center gap-1"><Clock class="h-3 w-3" /> Latency</span>
                  <p class="text-white font-semibold text-sm mt-1">{{ selectedLog.latency }} ms</p>
                </div>
                <div class="bg-zinc-900 border border-zinc-800/80 p-3 rounded-lg">
                  <span class="text-zinc-500 text-[10px] uppercase font-bold tracking-wider flex items-center gap-1"><Globe class="h-3 w-3" /> Client IP</span>
                  <p class="text-white font-semibold text-sm mt-1">{{ selectedLog.ip }}</p>
                </div>
                <div class="bg-zinc-900 border border-zinc-800/80 p-3 rounded-lg">
                  <span class="text-zinc-500 text-[10px] uppercase font-bold tracking-wider flex items-center gap-1"><User class="h-3 w-3" /> User GUID</span>
                  <p class="text-white font-semibold text-sm mt-1 truncate">{{ selectedLog.userId || "anonymous" }}</p>
                </div>
                <div class="bg-zinc-900 border border-zinc-800/80 p-3 rounded-lg">
                  <span class="text-zinc-500 text-[10px] uppercase font-bold tracking-wider flex items-center gap-1"><Cpu class="h-3 w-3" /> Payload</span>
                  <p class="text-white font-semibold text-sm mt-1">{{ selectedLog.payloadSize }} B</p>
                </div>
              </div>
              <div class="space-y-4">
                <div class="space-y-1 font-mono">
                  <h5 class="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Transaction Headers</h5>
                  <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-3 max-h-48 overflow-y-auto text-zinc-300 font-medium custom-scrollbar leading-relaxed text-[10px]">
                    <div v-for="(v, k) in selectedLog.requestHeaders" :key="k" class="py-1 truncate border-b border-zinc-800 last:border-0">
                      <span class="text-emerald-500 font-semibold">{{ k }}:</span> <span class="text-zinc-300">{{ v }}</span>
                    </div>
                    <div class="py-1 truncate">
                      <span class="text-emerald-500 font-semibold">User-Agent:</span> <span class="text-zinc-300">{{ selectedLog.userAgent }}</span>
                    </div>
                  </div>
                </div>
                <div class="space-y-1 font-mono">
                  <h5 class="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Mapped ReturnPayload</h5>
                  <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-3 text-zinc-300 max-h-44 overflow-y-auto custom-scrollbar">
                    <pre class="text-[10px] leading-relaxed select-all">{{ selectedLog.responseBody || "{}" }}</pre>
                  </div>
                </div>
              </div>
              <div class="pt-4 border-t border-zinc-800 space-y-4">
                <div class="flex justify-between items-center">
                  <h5 class="text-white font-semibold text-sm flex items-center gap-1.5">
                    <Sparkles class="h-4.5 w-4.5 text-emerald-500" />
                    <span>Armure Vani AI Trace Explainer</span>
                  </h5>
                  <button @click="explainWithAI(selectedLog.id)" :disabled="isExplaining" :class="['px-3 py-1.5 rounded-lg text-[11px] font-semibold cursor-pointer flex items-center gap-1.5 border select-none transition-all', isExplaining ? 'bg-zinc-800 text-zinc-500 border-zinc-700 cursor-wait' : 'bg-emerald-500/10 hover:bg-emerald-500 text-emerald-400 hover:text-zinc-950 border-emerald-500/20 hover:border-emerald-500']">
                    <Cpu v-if="!isExplaining" class="h-3.5 w-3.5" />
                    <div v-if="isExplaining" class="h-3 w-3 border-2 border-t-zinc-400 border-zinc-700 rounded-full animate-spin" />
                    <span>{{ isExplaining ? 'Asking Vani AI...' : 'Explain Trace Cause' }}</span>
                  </button>
                </div>
                <div v-if="isExplaining" class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 text-center flex flex-col items-center justify-center space-y-3 animate-pulse">
                  <Cpu class="h-8 w-8 text-emerald-500 animate-spin" />
                  <p class="text-zinc-300 text-xs">Vani AI model is dissecting HTTP headers and troubleshooting vectors...</p>
                </div>
                <div v-if="explainError" class="p-3 bg-rose-500/5 border border-rose-500/10 rounded-xl text-rose-400 text-xs font-mono">⚠ API Explainer failure: {{ explainError }}</div>
                <div v-if="aiExplanation" class="bg-emerald-950/10 border border-emerald-500/15 p-4 rounded-xl text-xs text-zinc-300 font-sans leading-relaxed space-y-3 custom-scrollbar">
                  <div class="whitespace-pre-line select-text selection:bg-emerald-500/20">{{ aiExplanation }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="p-4 border-t border-zinc-800 bg-zinc-900 flex justify-end">
            <button @click="closeInspector" class="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-white font-medium rounded-lg cursor-pointer transition-colors">Close Investigator</button>
          </div>
        </div>
      </div>
    </template>

    <!-- Export Preview Modal -->
    <template v-if="showExportPreview">
      <div class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="w-full max-w-4xl bg-zinc-950 border border-zinc-800 rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden text-zinc-100">
          <div class="px-5 py-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-900">
            <div class="flex items-center gap-2.5">
              <FileSpreadsheet class="text-emerald-400 h-5 w-5" />
              <div>
                <h4 class="text-white font-bold text-sm">Export Preview (CSV)</h4>
                <p class="text-[10px] text-zinc-500 font-mono">Showing the first {{ Math.min(10, telemetry.logs.length) }} of {{ telemetry.logs.length }} rows to be exported</p>
              </div>
            </div>
            <button @click="showExportPreview = false" class="p-1.5 hover:bg-zinc-800 text-zinc-400 hover:text-white rounded-lg transition-colors cursor-pointer">
              <X class="h-4 w-4" />
            </button>
          </div>
          <div class="p-6 overflow-y-auto space-y-4 flex-1 custom-scrollbar text-xs">
            <div class="text-xs text-zinc-400">Please verify the data columns and row layout before confirming your download.</div>
            <div class="border border-zinc-800 rounded-xl overflow-hidden bg-zinc-900/50">
              <div class="overflow-x-auto custom-scrollbar">
                <table class="min-w-full text-[11px] text-left border-collapse">
                  <thead>
                    <tr class="bg-zinc-900 border-b border-zinc-800 text-zinc-400 font-mono">
                      <th v-for="h in csvHeaders" :key="h" class="py-2.5 px-3 font-semibold whitespace-nowrap">{{ h }}</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-zinc-800">
                    <tr v-for="(l, i) in telemetry.logs.slice(0, 10)" :key="l.id || i" class="hover:bg-zinc-800/10 font-mono text-zinc-300">
                      <td class="py-2 px-3 truncate max-w-[80px]" :title="l.id">{{ l.id }}</td>
                      <td class="py-2 px-3 whitespace-nowrap">{{ l.timestamp?.replace?.('T', ' ')?.slice?.(0, 19) || l.timestamp }}</td>
                      <td class="py-2 px-3 font-bold text-emerald-400">{{ l.method }}</td>
                      <td class="py-2 px-3 truncate max-w-[150px]" :title="l.path">{{ l.path }}</td>
                      <td class="py-2 px-3"><span :class="['px-1 rounded font-bold', getStatusStyle(l.status)]">{{ l.status }}</span></td>
                      <td class="py-2 px-3 text-right text-white font-semibold">{{ l.latency }} ms</td>
                      <td class="py-2 px-3 truncate max-w-[100px]">{{ l.source }}</td>
                      <td class="py-2 px-3 text-zinc-500">{{ l.ip }}</td>
                      <td class="py-2 px-3 text-zinc-500 truncate max-w-[100px]">{{ l.userId || "anon" }}</td>
                      <td class="py-2 px-3 text-right">{{ l.payloadSize }} B</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div class="space-y-1">
              <span class="text-[10px] text-zinc-500 font-mono uppercase font-bold tracking-wider">RAW CSV SNIPPET</span>
              <div class="bg-zinc-950 border border-zinc-800 p-3.5 rounded-xl text-[10px] font-mono text-zinc-400 overflow-x-auto custom-scrollbar max-h-36 whitespace-pre">{{ csvSnippet }}</div>
            </div>
          </div>
          <div class="p-4 border-t border-zinc-800 bg-zinc-900 flex justify-between items-center text-zinc-400 font-mono">
            <span>Total rows to download: <span class="font-bold text-emerald-400">{{ telemetry.logs.length }}</span></span>
            <div class="flex gap-2">
              <button @click="showExportPreview = false" class="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-white font-medium rounded-lg text-xs cursor-pointer transition-colors">Cancel</button>
              <button @click="downloadCsv" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg text-xs cursor-pointer transition-all flex items-center gap-1.5">
                <Download class="h-3.5 w-3.5" />
                <span>Download Complete CSV</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue"
import { useRoute } from "vue-router"
import { useTelemetryStore } from "../stores/telemetry"
import api from "../api"
import { Search, FileSpreadsheet, Calendar, Clock, X, Eye, Terminal, Globe, User, Cpu, Sparkles, Download } from "lucide-vue-next"

const route = useRoute()
const telemetry = useTelemetryStore()

const searchQuery = ref("")
const selectedSource = ref("All Sources")
const selectedStatus = ref("All Statuses")
const selectedMethod = ref("All Methods")
const minLatency = ref("")
const maxLatency = ref("")
const startTime = ref("")
const endTime = ref("")
const selectedLog = ref(null)
const isExplaining = ref(false)
const aiExplanation = ref(null)
const explainError = ref(null)
const showExportPreview = ref(false)

const csvHeaders = ["ID", "Timestamp", "Method", "Path", "Status Code", "Latency (ms)", "Source Module", "Client IP", "User ID", "Payload Size (Bytes)"]

const sources = computed(() => telemetry.sources.map(s => s.name))

const csvSnippet = computed(() => {
  const rows = telemetry.logs.slice(0, 10).map(l =>
    [l.id, l.timestamp, l.method, `"${l.path}"`, l.status, l.latency, `"${l.source}"`, l.ip, l.userId || "anon", l.payloadSize].join(",")
  )
  return [csvHeaders.join(","), ...rows].join("\n") + (telemetry.logs.length > 10 ? "\n... [truncated] ..." : "")
})

function getStatusStyle(status) {
  if (status >= 500) return "bg-rose-500/10 text-rose-400 border border-rose-500/25"
  if (status >= 400) return "bg-amber-500/10 text-amber-400 border border-amber-500/25"
  if (status >= 300) return "bg-blue-500/10 text-blue-400 border border-blue-500/25"
  return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/25"
}

function getMethodStyle(method) {
  if (method === "POST") return "bg-amber-500/10 text-amber-400"
  if (method === "PUT") return "bg-blue-500/10 text-blue-400"
  if (method === "DELETE") return "bg-rose-500/10 text-rose-400"
  return "bg-emerald-500/10 text-emerald-400"
}

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
}

function openInspector(log) {
  selectedLog.value = log
  aiExplanation.value = null
  explainError.value = null
}

function closeInspector() {
  selectedLog.value = null
  aiExplanation.value = null
  explainError.value = null
}

async function explainWithAI(logId) {
  isExplaining.value = true
  explainError.value = null
  aiExplanation.value = null
  try {
    const result = await api.post("armure_apim_sentinel.api.ai.explain_error", { logId })
    aiExplanation.value = result.explanation
  } catch (e) {
    explainError.value = e.message || "Failed calling Armure Vani AI."
  } finally {
    isExplaining.value = false
  }
}

function downloadCsv() {
  if (!telemetry.logs.length) return
  const rows = telemetry.logs.map(l =>
    [l.id, l.timestamp, l.method, `"${l.path}"`, l.status, l.latency, `"${l.source}"`, l.ip, l.userId || "anon", l.payloadSize].join(",")
  )
  const csvContent = [csvHeaders.join(","), ...rows].join("\n")
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `api_transaction_telemetry_export_${Date.now()}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  showExportPreview.value = false
}

let debounceTimer
function refetchLogs() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(async () => {
    await telemetry.fetchLogs({
      search: searchQuery.value || undefined,
      source: selectedSource.value !== "All Sources" ? selectedSource.value : undefined,
      status: selectedStatus.value !== "All Statuses" ? selectedStatus.value : undefined,
      method: selectedMethod.value !== "All Methods" ? selectedMethod.value : undefined,
      minLatency: minLatency.value || undefined,
      maxLatency: maxLatency.value || undefined,
      startTime: startTime.value || undefined,
      endTime: endTime.value || undefined,
    })
  }, 300)
}

watch([searchQuery, selectedSource, selectedStatus, selectedMethod, minLatency, maxLatency, startTime, endTime], refetchLogs)

function toLocalDatetimeString(ms) {
  const d = new Date(ms)
  const pad = (n) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(() => {
  telemetry.fetchSources()
  const startMs = route.query.startMs
  const endMs = route.query.endMs
  if (startMs && endMs) {
    const from = Number(startMs)
    const to = Number(endMs)
    if (!isNaN(from) && !isNaN(to)) {
      startTime.value = toLocalDatetimeString(from)
      endTime.value = toLocalDatetimeString(to)
    }
  }
  refetchLogs()
})
</script>
