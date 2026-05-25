<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-0">
    <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-sm relative overflow-hidden group hover:border-zinc-700 transition-colors duration-200">
      <div class="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition-colors pointer-events-none" />
      <div class="flex justify-between items-start">
        <div>
          <p class="text-zinc-500 text-xs uppercase font-bold tracking-wider">Total Traffic</p>
          <h3 class="text-3xl font-semibold text-zinc-100 mt-2 font-mono tracking-tight">
            {{ loading ? "..." : formatNum(m?.totalRequests || 0) }}
          </h3>
          <p class="text-emerald-500 text-xs mt-2 flex items-center gap-1">
            <span>● Live Ingesting</span>
            <span class="text-zinc-500">({{ periodLabel }})</span>
          </p>
        </div>
        <div class="p-3 bg-zinc-800/80 border border-zinc-700/85 text-zinc-300 rounded-lg">
          <span class="lucide-activity size-5" />
        </div>
      </div>
    </div>
    <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-sm relative overflow-hidden group hover:border-zinc-700 transition-colors duration-200">
      <div class="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition-colors pointer-events-none" />
      <div class="flex justify-between items-start">
        <div>
          <p class="text-zinc-500 text-xs uppercase font-bold tracking-wider">Average Latency</p>
          <h3 class="text-3xl font-semibold text-zinc-100 mt-2 font-mono tracking-tight">
            {{ loading ? "..." : `${m?.avgLatency || 0} ms` }}
          </h3>
          <p class="text-emerald-500 text-xs mt-2">
            {{ (m?.avgLatency || 0) < 150 ? "✓ Excellent response times" : "⚠ Latency warning" }}
          </p>
        </div>
        <div class="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 rounded-lg">
          <span class="lucide-clock size-5" />
        </div>
      </div>
    </div>
    <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-sm relative overflow-hidden group hover:border-zinc-700 transition-colors duration-200">
      <div class="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition-colors pointer-events-none" />
      <div class="flex justify-between items-start">
        <div>
          <p class="text-zinc-500 text-xs uppercase font-bold tracking-wider">Success Rate</p>
          <h3 class="text-3xl font-semibold text-zinc-100 mt-2 font-mono tracking-tight">
            {{ loading ? "..." : `${m?.successRate || 100}%` }}
          </h3>
          <p class="text-xs mt-2">
            <span :class="(m?.successRate || 100) >= 98 ? 'text-emerald-500' : 'text-amber-500'">
              {{ m?.errorCount || 0 }} total errors
            </span>
          </p>
        </div>
        <div class="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 rounded-lg">
          <span class="lucide-check-circle size-5" />
        </div>
      </div>
    </div>
    <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-sm relative overflow-hidden group hover:border-zinc-700 transition-colors duration-200">
      <div class="absolute top-0 right-0 w-24 h-24 bg-rose-500/5 rounded-full blur-2xl group-hover:bg-rose-500/10 transition-colors pointer-events-none" />
      <div class="flex justify-between items-start">
        <div>
          <p class="text-zinc-500 text-xs uppercase font-bold tracking-wider">Breaches / Alerts</p>
          <h3 class="text-3xl font-semibold text-zinc-100 mt-2 font-mono tracking-tight">
            {{ loading ? "..." : (m?.activeAlerts || 0) }}
          </h3>
          <p class="text-rose-400 text-xs mt-2 flex items-center gap-1">
            <span>{{ (m?.activeAlerts || 0) > 0 ? "⚠ Rule violations active" : "✓ Safe configuration" }}</span>
          </p>
        </div>
        <div :class="(m?.activeAlerts || 0) > 0 ? 'p-3 bg-rose-500/20 text-rose-400 animate-pulse border border-rose-500/30 rounded-lg' : 'p-3 bg-zinc-800 text-zinc-400 border border-zinc-700 rounded-lg'">
          <span class="lucide-alert-triangle size-5" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  metrics: { type: Object, default: null },
  loading: { type: Boolean, default: true },
  periodLabel: { type: String, default: "Last 24h" },
})

const formatNum = (num) => new Intl.NumberFormat().format(num)
</script>
