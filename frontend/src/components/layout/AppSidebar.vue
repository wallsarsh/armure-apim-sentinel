<template>
  <aside class="w-full md:w-64 bg-zinc-900/50 border-b md:border-b-0 md:border-r border-zinc-800 flex flex-col justify-between shrink-0 p-5 md:h-screen md:sticky md:top-0 select-none">
    <div class="space-y-6">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 bg-emerald-500 rounded flex items-center justify-center text-zinc-950 font-bold shadow-lg shadow-emerald-500/10 shrink-0">
          <Cpu class="h-4.5 w-4.5" />
        </div>
        <div>
          <h1 class="text-zinc-100 font-bold text-sm tracking-tight leading-none uppercase">Gateway Sentinel</h1>
          <span class="text-zinc-500 text-[10px] uppercase font-bold tracking-widest mt-1 block">API MONITOR v2.4</span>
        </div>
      </div>
      <div class="bg-zinc-900 border border-zinc-800 p-3 rounded-xl flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span class="text-zinc-300 font-medium text-[11px] font-mono uppercase tracking-wider">Gateway Stream Live</span>
        </div>
        <span class="text-[9px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 font-bold px-1.5 py-0.5 rounded font-mono">100% OK</span>
      </div>
      <nav class="space-y-1">
        <!-- Dashboard -->
        <button @click="$emit('update:currentTab', 'dashboard')" :class="navBtnClass('dashboard')">
          <div class="flex items-center gap-2.5">
            <Activity class="h-4.5 w-4.5 text-zinc-400" />
            <span>Dashboard</span>
          </div>
        </button>
        <!-- Raw API Logs -->
        <button @click="$emit('update:currentTab', 'logs')" :class="navBtnClass('logs')">
          <div class="flex items-center gap-2.5">
            <Terminal class="h-4.5 w-4.5 text-zinc-400" />
            <span>Raw API Logs</span>
          </div>
        </button>
        <!-- Alerts & Anomalies -->
        <button @click="$emit('update:currentTab', 'alerts')" :class="navBtnClass('alerts')">
          <div class="flex items-center gap-2.5">
            <Radio class="h-4.5 w-4.5 text-zinc-400" />
            <span>Alerts & Anomalies</span>
          </div>
          <span v-if="activeAlertsCount > 0" :class="['px-2 py-0.5 rounded-full text-[10px] font-bold font-mono transition-colors', currentTab === 'alerts' ? 'bg-zinc-100 text-zinc-900 border border-zinc-350' : 'bg-rose-500/20 text-rose-500 animate-pulse']">{{ activeAlertsCount }}</span>
        </button>
        <!-- Log Channels -->
        <button @click="$emit('update:currentTab', 'sources')" :class="navBtnClass('sources')">
          <div class="flex items-center gap-2.5">
            <Server class="h-4.5 w-4.5 text-zinc-400" />
            <span>Log Channels</span>
          </div>
        </button>
      </nav>
    </div>
    <div class="pt-6 border-t border-zinc-800 mt-5 md:mt-0 text-[10px] text-zinc-500 space-y-1.5 font-mono">
      <div class="flex justify-between">
        <span>SRE TIMING:</span>
        <span class="text-zinc-300 select-text">UTC</span>
      </div>
      <div class="text-zinc-100 select-text font-semibold min-h-[16px]">{{ currentTime || "UTC Loading..." }}</div>
      <div class="text-[9px] text-zinc-500 pt-1 border-t border-zinc-800/40">Governance Sentinel Agent</div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue"
import { Cpu, Activity, Terminal, Radio, Server } from "lucide-vue-next"

const props = defineProps({
  currentTab: { type: String, default: "dashboard" },
  activeAlertsCount: { type: Number, default: 0 },
})

defineEmits(["update:currentTab"])

const currentTime = ref("")
let clockInterval = null

onMounted(() => {
  clockInterval = setInterval(() => {
    const now = new Date()
    currentTime.value = now.toUTCString().replace("GMT", "UTC")
  }, 1000)
})

onUnmounted(() => {
  if (clockInterval) clearInterval(clockInterval)
})

function navBtnClass(tab) {
  const base = "w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-between cursor-pointer transition-all"
  if (props.currentTab === tab) {
    return `${base} bg-zinc-800 text-zinc-100 border border-zinc-700/50 shadow-sm`
  }
  return `${base} text-zinc-400 hover:bg-zinc-800/40 hover:text-white`
}
</script>
