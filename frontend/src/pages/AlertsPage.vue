<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-zinc-800">
      <div>
        <h2 class="text-xl font-semibold text-white inline-flex items-center gap-2">
          <Radio class="h-5 w-5 text-rose-500 animate-pulse" />
          <span>Alerts & Governance Center</span>
        </h2>
        <p class="text-xs text-zinc-400">Configure API constraints, monitor metric thresholds, and evaluate anomalies</p>
      </div>
      <div class="flex gap-2">
        <button v-for="t in tabs" :key="t.id" @click="activeTab = t.id" :class="['px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all', activeTab === t.id ? (t.id === 'ai' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold' : 'bg-zinc-800 text-zinc-100 border border-zinc-700/60 shadow-sm') : 'text-zinc-500 hover:text-white']">
          <template v-if="t.id === 'ai'"><Brain class="h-4 w-4 inline mr-1" /></template>
          <span>{{ t.label() }}</span>
        </button>
      </div>
    </div>

    <!-- Tab: Triggered Alerts -->
    <template v-if="activeTab === 'triggered'">
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <h3 class="text-sm font-semibold text-zinc-400">Active Violations ({{ activeAlerts.length }})</h3>
          <button v-if="activeAlerts.length" @click="resolveAllAlerts" class="text-xs font-medium text-emerald-400 hover:text-emerald-300 border border-emerald-500/20 hover:border-emerald-500/40 px-3 py-1.5 rounded-lg cursor-pointer transition-all flex items-center gap-1 bg-emerald-500/5">
            <Check class="h-3.5 w-3.5" />
            <span>Resolve All Alerts</span>
          </button>
        </div>
        <div class="space-y-3">
          <template v-if="!telemetry.alerts.length">
            <div class="flex flex-col items-center justify-center p-12 bg-zinc-900 border border-zinc-800 rounded-xl">
              <ShieldCheck class="text-emerald-500 h-10 w-10 mb-2" />
              <p class="text-white text-sm font-semibold">System Operations Normal</p>
              <p class="text-zinc-500 text-xs">No active alert rule violations reported on any gateway API.</p>
            </div>
          </template>
          <div v-for="al in telemetry.alerts" :key="al.name" :class="['border rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all', alertCardClass(al)]">
            <div class="flex items-start gap-3">
              <div :class="['p-2.5 rounded-lg mt-0.5', alertIconClass(al)]">
                <ShieldAlert v-if="al.type !== 'ai'" class="h-4.5 w-4.5" />
                <Brain v-else class="h-4.5 w-4.5" />
              </div>
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <span class="text-white font-medium text-sm">{{ al.rule_name || al.ruleName }}</span>
                  <span :class="['text-[10px] font-semibold px-2 py-0.5 rounded uppercase font-mono tracking-wider', getSeverityBadge(al.severity)]">{{ al.severity }}</span>
                  <span v-if="al.type === 'ai'" class="bg-purple-500/15 text-purple-300 border border-purple-500/20 rounded px-1.5 py-0.5 text-[10px] inline-flex items-center gap-0.5 font-bold uppercase font-mono">
                    <Sparkles class="h-2.5 w-2.5" /> AI
                  </span>
                  <span v-if="al.resolved" class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] px-1.5 py-0.5 rounded font-semibold font-mono uppercase">RESOLVED</span>
                </div>
                <p class="text-zinc-300 text-xs mt-1.5 max-w-2xl">{{ al.message }}</p>
                <p class="text-zinc-500 font-mono text-[10px] mt-1 flex items-center gap-1">
                  <Clock class="h-3 w-3" />
                  <span>{{ new Date(al.timestamp).toLocaleString() }}</span>
                </p>
              </div>
            </div>
            <button v-if="!al.resolved" @click="resolveAlert(al.name)" class="self-start md:self-center text-xs text-emerald-400 hover:text-white hover:bg-emerald-500 border border-emerald-500/20 hover:border-emerald-500 px-3 py-1.5 rounded-lg cursor-pointer transition-all shrink-0 font-medium">
              Acknowledge & Resolve
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- Tab: Rules -->
    <template v-if="activeTab === 'rules'">
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <h3 class="text-sm font-semibold text-zinc-400">Configured Policy Rule sets ({{ telemetry.rules.length }})</h3>
          <button @click="showAddRule = !showAddRule" class="text-xs font-semibold text-zinc-950 bg-zinc-100 hover:bg-zinc-200 border border-transparent px-3.5 py-1.5 rounded-lg cursor-pointer transition-all flex items-center gap-1.5">
            <Plus class="h-4 w-4" />
            <span>Configure New Rule</span>
          </button>
        </div>
        <form v-if="showAddRule" @submit.prevent="createRule" class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
          <h4 class="text-sm font-semibold text-white">New Policy Formulation</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div class="space-y-1">
              <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Policy Name</label>
              <input type="text" placeholder="e.g. Rate Limiter Outage" v-model="newRule.name" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-medium" required />
            </div>
            <div class="space-y-1">
              <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Condition Target Metric</label>
              <select v-model="newRule.metric" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500">
                <option value="latency">Response Latency (ms)</option>
                <option value="status_code">HTTP Status Errors Threshold</option>
                <option value="rate_limit">Rate Limit Remaining Limit</option>
              </select>
            </div>
            <div class="space-y-1">
              <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Trigger Criteria & Value</label>
              <div class="flex gap-2">
                <select v-model="newRule.condition" class="bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 shrink-0">
                  <option value="gt">Greater Than (&gt;)</option>
                  <option value="lt">Less Than (&lt;)</option>
                  <option value="eq">Equals (=)</option>
                </select>
                <input type="number" v-model.number="newRule.value" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" required />
              </div>
            </div>
            <div class="space-y-1">
              <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Alert Severity Tier</label>
              <select v-model="newRule.severity" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-semibold">
                <option value="info">Info (Blue)</option>
                <option value="warning">Warning (Amber)</option>
                <option value="critical">Critical (Rose)</option>
              </select>
            </div>
          </div>
          <!-- Advanced API Selection -->
          <div class="border-t border-zinc-800 pt-3">
            <button type="button" @click="showAdvancedFilters = !showAdvancedFilters" class="flex items-center gap-2 text-xs text-zinc-400 hover:text-zinc-200 cursor-pointer">
              <span class="font-mono font-bold">{{ showAdvancedFilters ? '▾' : '▸' }}</span>
              <span class="font-semibold">Advanced API Selection</span>
            </button>
          </div>
          <template v-if="showAdvancedFilters">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">HTTP Method</label>
                <select v-model="newRule.filter_method" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500">
                  <option value="Any">Any</option>
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="DELETE">DELETE</option>
                  <option value="PATCH">PATCH</option>
                </select>
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Path Pattern</label>
                <input type="text" placeholder="e.g. /api/v1/users/* or re:^/api" v-model="newRule.filter_path_pattern" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Path Search</label>
                <select v-model="newRule.filter_path_search_type" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500">
                  <option value="glob">Glob</option>
                  <option value="regex">Regex</option>
                </select>
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Source Channel</label>
                <input type="text" placeholder="Leave empty for all" v-model="newRule.filter_source" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">IP Range (CIDR)</label>
                <input type="text" placeholder="10.0.0.0/8,192.168.1.0/24" v-model="newRule.filter_ip_range" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">User-Agent Pattern</label>
                <input type="text" placeholder="*Mozilla* or re:bot" v-model="newRule.filter_user_agent_pattern" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">UA Search</label>
                <select v-model="newRule.filter_user_agent_search_type" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500">
                  <option value="glob">Glob</option>
                  <option value="regex">Regex</option>
                </select>
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Min Payload (bytes)</label>
                <input type="number" v-model.number="newRule.filter_min_payload" min="0" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Max Payload (bytes)</label>
                <input type="number" v-model.number="newRule.filter_max_payload" min="0" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Min Status Code</label>
                <input type="number" v-model.number="newRule.filter_status_min" min="0" max="599" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Max Status Code</label>
                <input type="number" v-model.number="newRule.filter_status_max" min="0" max="599" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
              </div>
            </div>
            <div class="border-t border-zinc-800 pt-3 mt-2">
              <span class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Enhanced Evaluation</span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs mt-2">
              <div class="flex items-center gap-2 pt-2">
                <input type="checkbox" id="cb" v-model="newRule.count_based" class="accent-emerald-500" />
                <label for="cb" class="text-zinc-400 text-xs font-medium cursor-pointer">Count-Based Evaluation</label>
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Window (min)</label>
                <input type="number" v-model.number="newRule.evaluation_window" min="1" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Min Trigger Count</label>
                <input type="number" v-model.number="newRule.min_trigger_count" min="1" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
              </div>
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Group By</label>
                <select v-model="newRule.group_by" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500">
                  <option value="none">None (Global)</option>
                  <option value="source">Source Channel</option>
                  <option value="ip">Client IP</option>
                  <option value="path">API Path</option>
                  <option value="method">HTTP Method</option>
                </select>
              </div>
            </div>
          </template>
          <div class="flex justify-end gap-2 text-xs pt-2">
            <button type="button" @click="showAddRule = false; showAdvancedFilters = false" class="px-3.5 py-2 hover:bg-zinc-800 text-zinc-400 border border-transparent rounded-lg cursor-pointer font-medium">Cancel</button>
            <button type="submit" class="px-4 py-2 bg-zinc-100 hover:bg-zinc-200 text-zinc-950 rounded-lg cursor-pointer font-bold">Deploy Policy Rule</button>
          </div>
        </form>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="ru in telemetry.rules" :key="ru.name" class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col justify-between hover:border-zinc-700 transition-colors">
            <div>
              <div class="flex justify-between items-start">
                <span class="text-white font-medium text-sm">{{ ru.rule_name || ru.name }}</span>
                <span :class="['text-[9px] px-1.5 py-0.5 rounded uppercase font-mono font-bold tracking-wider', getSeverityBadge(ru.severity)]">{{ ru.severity }}</span>
              </div>
              <div class="mt-3 text-xs bg-zinc-950 border border-zinc-800/40 p-2.5 rounded-lg space-y-1 font-mono text-zinc-400">
                <div>Policy Metric: <span class="text-zinc-300">{{ ru.metric }}</span></div>
                <div>Evaluator: <span class="text-zinc-300">{{ ru.condition === 'gt' ? '>' : ru.condition === 'lt' ? '<' : '=' }} {{ ru.threshold || ru.value }}</span></div>
                <div v-if="ru.count_based" class="text-amber-400">Evaluation: Count-based ({{ ru.min_trigger_count }} hits in {{ ru.evaluation_window }}min{{ ru.group_by !== 'none' ? ', grouped by ' + ru.group_by : '' }})</div>
                <div v-else>Policy window: <span class="text-zinc-300">Per-log continuous</span></div>
              </div>
              <div v-if="showRuleFilters(ru)" class="flex flex-wrap gap-1.5 mt-2">
                <span v-if="ru.filter_method && ru.filter_method !== 'Any'" class="text-[10px] bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded font-mono border border-zinc-700/40">METHOD: {{ ru.filter_method }}</span>
                <span v-if="ru.filter_path_pattern" class="text-[10px] bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded font-mono border border-zinc-700/40">{{ ru.filter_path_search_type === 'regex' ? 'REGEX' : 'PATH' }}: {{ ru.filter_path_pattern }}</span>
                <span v-if="ru.filter_source" class="text-[10px] bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded font-mono border border-zinc-700/40">SOURCE: {{ ru.filter_source }}</span>
                <span v-if="ru.filter_ip_range" class="text-[10px] bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded font-mono border border-zinc-700/40">CIDR: {{ ru.filter_ip_range }}</span>
                <span v-if="ru.filter_user_agent_pattern" class="text-[10px] bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded font-mono border border-zinc-700/40">UA: {{ ru.filter_user_agent_pattern }}</span>
                <span v-if="ru.filter_min_payload > 0 || ru.filter_max_payload > 0" class="text-[10px] bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded font-mono border border-zinc-700/40">PAYLOAD: {{ ru.filter_min_payload || 0 }}-{{ ru.filter_max_payload || '∞' }}</span>
                <span v-if="ru.filter_status_min > 0 || ru.filter_status_max > 0" class="text-[10px] bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded font-mono border border-zinc-700/40">STATUS: {{ ru.filter_status_min || 0 }}-{{ ru.filter_status_max || 599 }}</span>
              </div>
            </div>
            <div class="flex justify-between items-center text-xs mt-4 pt-3 border-t border-zinc-800/40">
              <div class="flex items-center gap-2">
                <button @click="toggleRule(ru.name, ru.is_active)" :class="['relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200', ru.is_active ? 'bg-emerald-500' : 'bg-zinc-700']">
                  <span :class="['pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200', ru.is_active ? 'translate-x-4' : 'translate-x-0']" />
                </button>
                <span class="text-zinc-500">{{ ru.is_active ? 'Active Policy' : 'Muted / Inactive' }}</span>
              </div>
              <button @click="deleteRule(ru.name)" class="p-1.5 hover:bg-rose-500/10 hover:text-rose-400 text-zinc-500 rounded border border-transparent hover:border-rose-500/20 transition-all cursor-pointer" title="Remove Rule">
                <Trash2 class="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Tab: AI Scanner -->
    <template v-if="activeTab === 'ai'">
      <div class="space-y-6">
        <div class="bg-purple-950/15 border border-purple-500/25 rounded-2xl p-6 relative overflow-hidden flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div class="absolute right-0 top-0 w-80 h-80 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />
          <div class="space-y-1 z-10">
            <h3 class="text-purple-300 font-semibold text-lg flex items-center gap-2">
              <Brain class="h-5.5 w-5.5 text-purple-400 animate-pulse" />
              <span>AI Anomaly Detection engine</span>
              <span class="bg-purple-500/20 text-purple-300 text-[10px] font-bold px-1.5 py-0.5 rounded font-mono">GEMINI PRO</span>
            </h3>
            <p class="text-xs text-zinc-500 max-w-xl">Deploy Gemini as a virtual Security SRE. It will audit recent system traffic metrics, look for brute force attacks, identify performance drift, and compile a report.</p>
          </div>
          <button @click="runScan" :disabled="telemetry.isScanning" :class="['px-4 py-2.5 rounded-xl text-xs font-semibold select-none shadow hover:shadow-purple-500/10 cursor-pointer flex items-center gap-2 transition-all font-mono shrink-0 z-10', telemetry.isScanning ? 'bg-purple-950/40 text-purple-300 border border-purple-500/20 cursor-wait' : 'bg-purple-600 text-white border border-purple-500 hover:bg-purple-500']">
            <div v-if="telemetry.isScanning" class="h-4.5 w-4.5 border-2 border-t-purple-300 border-purple-900 rounded-full animate-spin" />
            <Sparkles v-else class="h-4 w-4" />
            <span>{{ telemetry.isScanning ? 'Scanning Logs...' : 'Execute Gemini Security Scan' }}</span>
          </button>
        </div>

        <div v-if="telemetry.isScanning" class="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 text-center flex flex-col items-center justify-center space-y-4 animate-pulse">
          <Brain class="h-12 w-12 text-emerald-500 animate-bounce" />
          <div class="space-y-1">
            <p class="text-white text-sm font-semibold">Gemini Security Agent is analyzing API Telemetry</p>
            <p class="text-zinc-500 text-xs">Analyzing response code aggregates, tracking high frequency client IPs, and auditing performance regressions...</p>
          </div>
        </div>

        <div v-if="scanError" class="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl text-xs font-mono">⚠ Anomaly Scan Failure: {{ scanError }}</div>

        <template v-if="!telemetry.isScanning && telemetry.scanHistory.length && currentReport">
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col justify-between">
              <div>
                <h4 class="text-white font-medium text-sm">Security Assessment</h4>
                <p class="text-[11px] text-zinc-500">Model generated anomaly score</p>
              </div>
              <div class="flex flex-col items-center justify-center py-6 text-center">
                <div class="relative flex items-center justify-center">
                  <svg class="w-32 h-32 transform -rotate-90">
                    <circle cx="64" cy="64" r="54" stroke="#27272a" stroke-width="8" fill="transparent" />
                    <circle cx="64" cy="64" r="54" :stroke="scoreColor" stroke-width="8" fill="transparent" stroke-dasharray="339.29" :stroke-dashoffset="339.29 - (339.29 * safeScore) / 100" stroke-linecap="round" class="transition-all duration-1000" />
                  </svg>
                  <div class="absolute text-center">
                    <span class="text-3xl font-extrabold text-white font-mono">{{ safeScore }}</span>
                    <span class="text-zinc-500 text-[10px] block font-mono">/ 100</span>
                  </div>
                </div>
                <span :class="['mt-4 px-2.5 py-0.5 rounded-full text-xs font-semibold', scoreBadgeClass]">{{ scoreLabel }}</span>
              </div>
              <div class="border-t border-zinc-800 pt-3 text-xs text-zinc-400 space-y-1.5 font-mono">
                <div class="flex justify-between"><span>Audit Time:</span><span class="text-white">{{ new Date(currentReport.timestamp).toLocaleTimeString() }}</span></div>
                <div class="flex justify-between"><span>Incident Alerts Generated:</span><span class="text-white">{{ currentReport.detectedAlertsCount }} alerts</span></div>
              </div>
            </div>
            <div class="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-xl p-5 overflow-hidden">
              <div class="flex justify-between items-center mb-3">
                <h4 class="text-white font-medium text-sm inline-flex items-center gap-1.5">
                  <Sparkles class="h-4 w-4 text-emerald-500" />
                  <span>Gemini Generated Report Summary</span>
                </h4>
                <span class="text-[10px] text-zinc-500">Recent scan outputs</span>
              </div>
              <div class="bg-zinc-950 border border-zinc-800 p-4 rounded-xl text-xs max-h-72 overflow-y-auto text-zinc-300 space-y-3 font-sans custom-scrollbar select-text">
                <div class="whitespace-pre-wrap leading-relaxed select-all">{{ currentReport.analysis }}</div>
              </div>
            </div>
          </div>
        </template>

        <div v-if="telemetry.scanHistory.length > 1" class="space-y-3">
          <h4 class="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Historical Scans Log</h4>
          <div class="space-y-2">
            <div v-for="(hist, i) in telemetry.scanHistory.slice(1)" :key="hist.name || i" class="bg-zinc-900 border border-zinc-800/80 p-3 rounded-lg flex justify-between items-center text-xs">
              <div class="flex items-center gap-3">
                <Brain class="h-4 w-4 text-zinc-500" />
                <div>
                  <div class="text-white font-medium font-sans">Automatic SRE Anomaly Assessment</div>
                  <div class="text-zinc-500 text-[10px] font-mono mt-0.5">{{ new Date(hist.timestamp).toLocaleString() }}</div>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-zinc-400 font-mono">Score: <span class="font-bold text-white font-mono">{{ hist.anomalyScore }}</span></span>
                <button @click="loadReport(hist)" class="text-emerald-500 hover:text-emerald-400 underline font-semibold font-mono cursor-pointer">Load Report</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useTelemetryStore } from "../stores/telemetry"
import api from "../api"
import { Radio, Brain, ShieldAlert, Check, ShieldCheck, Clock, Sparkles, Plus, Trash2 } from "lucide-vue-next"

const telemetry = useTelemetryStore()
const activeTab = ref("triggered")
const showAddRule = ref(false)
const scanError = ref(null)
const currentReport = ref(null)

const tabs = [
  { id: "triggered", label: () => `Triggered (${activeAlerts.value.length})` },
  { id: "rules", label: () => `Rules & Policies (${telemetry.rules.length})` },
  { id: "ai", label: () => "AI Scanner" },
]

const activeAlerts = computed(() => telemetry.alerts.filter(a => !a.resolved))

const showAdvancedFilters = ref(false)

const newRule = ref({ name: "", metric: "latency", condition: "gt", value: 500, severity: "warning",
  filter_method: "Any", filter_path_pattern: "", filter_path_search_type: "glob",
  filter_source: "", filter_ip_range: "",
  filter_user_agent_pattern: "", filter_user_agent_search_type: "glob",
  filter_min_payload: 0, filter_max_payload: 0,
  filter_status_min: 0, filter_status_max: 0,
  count_based: false, evaluation_window: 5, min_trigger_count: 1, group_by: "none",
})

const safeScore = computed(() => {
  const r = currentReport.value
  return r && typeof r.anomalyScore === "number" && !isNaN(r.anomalyScore) ? r.anomalyScore : 0
})

const scoreColor = computed(() => safeScore.value > 60 ? "#f43f5e" : safeScore.value > 30 ? "#fbbf24" : "#10b981")

const scoreBadgeClass = computed(() => {
  if (safeScore.value > 60) return "bg-rose-500/10 text-rose-400 border border-rose-500/20"
  if (safeScore.value > 30) return "bg-amber-500/10 text-amber-400 border border-amber-500/20"
  return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
})

const scoreLabel = computed(() => {
  if (safeScore.value > 60) return "⚠ High Threat Incident"
  if (safeScore.value > 30) return "⚠ Elevated Anomaly Score"
  return "✓ Environment Healthy"
})

function alertCardClass(al) {
  if (al.resolved) return "bg-zinc-900/40 border-zinc-800 opacity-60"
  if (al.severity === "critical") return "bg-rose-950/10 border-rose-500/20 hover:border-rose-500/40 animate-pulse"
  if (al.severity === "warning") return "bg-amber-950/10 border-amber-500/20 hover:border-amber-500/40"
  return "bg-zinc-900 border-zinc-800/85 hover:border-zinc-700/80"
}

function alertIconClass(al) {
  if (al.resolved) return "bg-zinc-800 text-zinc-500"
  if (al.severity === "critical") return "bg-rose-500/10 text-rose-400 border border-rose-500/20"
  if (al.severity === "warning") return "bg-amber-500/10 text-amber-400 border border-amber-500/20"
  return "bg-blue-500/10 text-blue-400 border border-blue-500/20"
}

function getSeverityBadge(sev) {
  if (sev === "critical") return "bg-rose-500/10 text-rose-400 border border-rose-500/20"
  if (sev === "warning") return "bg-amber-500/10 text-amber-400 border border-amber-500/20"
  return "bg-blue-500/10 text-blue-400 border border-blue-500/20"
}

async function runScan() {
  scanError.value = null
  await telemetry.triggerAnomalyScan()
  await telemetry.fetchScanHistory()
  if (telemetry.scanHistory.length) {
    currentReport.value = telemetry.scanHistory[0]
  }
}

function showRuleFilters(ru) {
  return ru.filter_method || ru.filter_path_pattern || ru.filter_source || ru.filter_ip_range
    || ru.filter_user_agent_pattern || ru.filter_min_payload > 0 || ru.filter_max_payload > 0
    || ru.filter_status_min > 0 || ru.filter_status_max > 0
    || ru.count_based
}

function loadReport(r) {
  currentReport.value = r
}

async function resolveAlert(name) {
  try { await api.post("armure_apim_sentinel.api.alerts.resolve_alert", { alert_name: name }); await telemetry.fetchAlerts() }
  catch (e) { console.error(e) }
}

async function resolveAllAlerts() {
  try { await api.post("armure_apim_sentinel.api.alerts.resolve_all_alerts"); await telemetry.fetchAlerts() }
  catch (e) { console.error(e) }
}

async function createRule() {
  try {
    const payload = {
      rule_name: newRule.value.name,
      metric: newRule.value.metric,
      condition: newRule.value.condition,
      threshold: newRule.value.value,
      severity: newRule.value.severity,
      filter_method: newRule.value.filter_method === "Any" ? "" : newRule.value.filter_method,
      filter_path_pattern: newRule.value.filter_path_pattern,
      filter_path_search_type: newRule.value.filter_path_search_type,
      filter_source: newRule.value.filter_source,
      filter_ip_range: newRule.value.filter_ip_range,
      filter_user_agent_pattern: newRule.value.filter_user_agent_pattern,
      filter_user_agent_search_type: newRule.value.filter_user_agent_search_type,
      filter_min_payload: newRule.value.filter_min_payload,
      filter_max_payload: newRule.value.filter_max_payload,
      filter_status_min: newRule.value.filter_status_min,
      filter_status_max: newRule.value.filter_status_max,
      count_based: newRule.value.count_based ? 1 : 0,
      evaluation_window: newRule.value.evaluation_window,
      min_trigger_count: newRule.value.min_trigger_count,
      group_by: newRule.value.group_by,
    }
    await api.post("armure_apim_sentinel.api.alerts.create_rule", payload)
    showAddRule.value = false
    showAdvancedFilters.value = false
    newRule.value = { name: "", metric: "latency", condition: "gt", value: 500, severity: "warning",
      filter_method: "Any", filter_path_pattern: "", filter_path_search_type: "glob",
      filter_source: "", filter_ip_range: "",
      filter_user_agent_pattern: "", filter_user_agent_search_type: "glob",
      filter_min_payload: 0, filter_max_payload: 0,
      filter_status_min: 0, filter_status_max: 0,
      count_based: false, evaluation_window: 5, min_trigger_count: 1, group_by: "none",
    }
    await telemetry.fetchRules()
  } catch (e) { console.error(e) }
}

async function toggleRule(name, currentActive) {
  try {
    await api.post("armure_apim_sentinel.api.alerts.toggle_rule", { rule_name: name, is_active: !currentActive })
    await telemetry.fetchRules()
  } catch (e) { console.error(e) }
}

async function deleteRule(name) {
  try {
    await api.post("armure_apim_sentinel.api.alerts.delete_rule", { rule_name: name })
    await telemetry.fetchRules()
  } catch (e) { console.error(e) }
}

onMounted(async () => {
  await telemetry.fetchAlerts()
  await telemetry.fetchRules()
  await telemetry.fetchScanHistory()
  if (telemetry.scanHistory.length) currentReport.value = telemetry.scanHistory[0]
})
</script>
