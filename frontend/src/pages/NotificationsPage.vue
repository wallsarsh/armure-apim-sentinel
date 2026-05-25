<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-zinc-800">
      <div>
        <h2 class="text-xl font-semibold text-white inline-flex items-center gap-2">
          <Bell class="h-5 w-5 text-emerald-500" />
          <span>Notifications</span>
        </h2>
        <p class="text-xs text-zinc-400">Configure notification channels, monitor queue, and view delivery logs</p>
      </div>
      <div class="flex gap-2">
        <button v-for="t in tabs" :key="t.id" @click="activeTab = t.id" :class="['px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all', activeTab === t.id ? 'bg-zinc-800 text-zinc-100 border border-zinc-700/60 shadow-sm' : 'text-zinc-500 hover:text-white']">
          <span>{{ t.label }}</span>
        </button>
      </div>
    </div>

    <!-- Tab: Channels -->
    <template v-if="activeTab === 'channels'">
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <h3 class="text-sm font-semibold text-zinc-400">Notification Channels ({{ channels.length }})</h3>
          <button @click="showAddChannel = true" class="text-xs font-semibold text-zinc-950 bg-zinc-100 hover:bg-zinc-200 border border-transparent px-3.5 py-1.5 rounded-lg cursor-pointer transition-all flex items-center gap-1.5">
            <Plus class="h-4 w-4" />
            <span>Add Channel</span>
          </button>
        </div>

        <!-- Channel Form -->
        <form v-if="showAddChannel" @submit.prevent="createChannel" class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
          <h4 class="text-sm font-semibold text-white">New Notification Channel</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div class="space-y-1">
              <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Channel Name</label>
              <input type="text" placeholder="e.g. Slack Ops" v-model="newChannel.name" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-medium" required />
            </div>
            <div class="space-y-1">
              <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Channel Type</label>
              <select v-model="newChannel.type" @change="onTypeChange" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500">
                <option v-for="t in channelTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
            </div>
            <div class="space-y-1">
              <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Rate Limit (per min)</label>
              <input type="number" v-model.number="newChannel.rateLimit" min="1" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
            </div>
          </div>
          <!-- Dynamic Config Fields -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <template v-for="(cfg, key) in channelConfigFields" :key="key">
              <div class="space-y-1">
                <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">{{ cfg.label }}</label>
                <input v-if="cfg.type === 'textarea'" type="text" v-model="newChannel.config[key]" :placeholder="cfg.placeholder" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
                <input v-else-if="cfg.type === 'number'" type="number" v-model.number="newChannel.config[key]" :placeholder="cfg.placeholder" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
                <input v-else type="text" v-model="newChannel.config[key]" :placeholder="cfg.placeholder" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-white focus:outline-none focus:border-emerald-500 font-mono" />
              </div>
            </template>
          </div>
          <div v-if="validationErrors.length" class="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg text-xs">
            <div v-for="err in validationErrors" :key="err" class="font-mono">⚠ {{ err }}</div>
          </div>
          <div class="flex justify-end gap-2 text-xs pt-2">
            <button type="button" @click="showAddChannel = false; validationErrors = []" class="px-3.5 py-2 hover:bg-zinc-800 text-zinc-400 border border-transparent rounded-lg cursor-pointer font-medium">Cancel</button>
            <button type="submit" class="px-4 py-2 bg-zinc-100 hover:bg-zinc-200 text-zinc-950 rounded-lg cursor-pointer font-bold">Create Channel</button>
          </div>
        </form>

        <!-- Channel Cards -->
        <div v-if="!channels.length && !loading" class="flex flex-col items-center justify-center p-12 bg-zinc-900 border border-zinc-800 rounded-xl">
          <Bell class="text-zinc-600 h-10 w-10 mb-2" />
          <p class="text-white text-sm font-semibold">No Channels Configured</p>
          <p class="text-zinc-500 text-xs">Add a notification channel to route alerts.</p>
        </div>
        <div v-if="loading" class="text-center p-12 text-zinc-500 text-sm animate-pulse">Loading channels...</div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="ch in channels" :key="ch.name" class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col justify-between hover:border-zinc-700 transition-colors">
            <div>
              <div class="flex justify-between items-start">
                <div class="flex items-center gap-2">
                  <span class="text-white font-medium text-sm">{{ ch.channel_name }}</span>
                  <span class="text-[9px] bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded uppercase font-mono font-bold tracking-wider border border-zinc-700/40">{{ ch.channel_type }}</span>
                </div>
                <span :class="ch.is_active ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-zinc-800 text-zinc-500 border border-zinc-700/40'" class="text-[9px] px-1.5 py-0.5 rounded uppercase font-mono font-bold tracking-wider">{{ ch.is_active ? 'Active' : 'Inactive' }}</span>
              </div>
              <div class="mt-2 flex flex-wrap gap-1.5">
                <span class="text-[10px] bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded font-mono border border-zinc-700/40">Rate: {{ ch.rate_limit_per_minute }}/min</span>
              </div>
              <!-- Linked Rules -->
              <div v-if="ch._linkedRules && ch._linkedRules.length" class="mt-2">
                <div class="text-[10px] text-zinc-500 font-semibold uppercase tracking-wider mb-1">Linked Alert Rules</div>
                <div class="flex flex-wrap gap-1.5">
                  <span v-for="lr in ch._linkedRules" :key="lr.name" class="text-[10px] bg-blue-950/20 text-blue-400 border border-blue-700/30 px-1.5 py-0.5 rounded font-mono inline-flex items-center gap-1">
                    <span>{{ lr.rule_name }}</span>
                    <span :class="lr.severity === 'critical' ? 'text-rose-400' : lr.severity === 'warning' ? 'text-amber-400' : 'text-blue-400'" class="text-[8px] uppercase font-bold">({{ lr.severity }})</span>
                    <button @click="unlinkRule(ch.channel_name, lr.name)" class="hover:text-rose-400 ml-0.5 cursor-pointer" title="Unlink rule">×</button>
                  </span>
                </div>
              </div>
            </div>
            <!-- Link to Rule Form -->
            <div v-if="ch._showLink" class="mt-3 pt-3 border-t border-zinc-800/40 text-xs flex items-center gap-2">
              <select v-model="ch._linkRuleName" class="bg-zinc-950 border border-zinc-800 rounded-lg p-1.5 text-zinc-300 focus:outline-none focus:border-emerald-500 min-w-[180px]">
                <option value="">Select a rule...</option>
                <option v-for="r in unlinkedRules" :key="r.name" :value="r.name">{{ r.rule_name }}</option>
              </select>
              <button @click="linkToRule(ch)" :disabled="!ch._linkRuleName" class="px-2.5 py-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg hover:bg-emerald-500/20 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer font-medium">Link</button>
            </div>
            <div class="flex justify-between items-center text-xs mt-3 pt-3 border-t border-zinc-800/40">
              <div class="flex items-center gap-2">
                <button @click="toggleChannel(ch.name, ch.is_active)" :class="['relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200', ch.is_active ? 'bg-emerald-500' : 'bg-zinc-700']">
                  <span :class="['pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200', ch.is_active ? 'translate-x-4' : 'translate-x-0']" />
                </button>
                <button @click="testChannel(ch.name)" class="text-emerald-400 hover:text-emerald-300 font-semibold cursor-pointer">Test</button>
              </div>
              <div class="flex items-center gap-1">
                <button @click="ch._showLink = !ch._showLink" class="p-1.5 hover:bg-zinc-700 hover:text-zinc-200 text-zinc-500 rounded border border-transparent hover:border-zinc-700/40 transition-all cursor-pointer" title="Link to Alert Rule">
                  <Link class="h-4 w-4" />
                </button>
                <button @click="deleteChannel(ch.name)" class="p-1.5 hover:bg-rose-500/10 hover:text-rose-400 text-zinc-500 rounded border border-transparent hover:border-rose-500/20 transition-all cursor-pointer" title="Remove Channel">
                  <Trash2 class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Tab: Queue -->
    <template v-if="activeTab === 'queue'">
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <h3 class="text-sm font-semibold text-zinc-400">Notification Queue ({{ queueItems.length }})</h3>
          <select v-model="queueFilter" @change="fetchQueue" class="bg-zinc-900 border border-zinc-800 rounded-lg p-1.5 text-xs text-zinc-300 focus:outline-none focus:border-emerald-500">
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="sending">Sending</option>
            <option value="sent">Sent</option>
            <option value="failed">Failed</option>
            <option value="retrying">Retrying</option>
          </select>
        </div>
        <div v-if="!queueItems.length && !queueLoading" class="flex flex-col items-center justify-center p-12 bg-zinc-900 border border-zinc-800 rounded-xl">
          <Bell class="text-zinc-600 h-10 w-10 mb-2" />
          <p class="text-white text-sm font-semibold">Queue Empty</p>
          <p class="text-zinc-500 text-xs">No notifications in queue.</p>
        </div>
        <div v-if="queueLoading" class="text-center p-12 text-zinc-500 text-sm animate-pulse">Loading queue...</div>
        <div class="space-y-2">
          <div v-for="item in queueItems" :key="item.name" class="bg-zinc-900 border border-zinc-800 rounded-xl p-3 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
            <div class="flex items-start gap-3 min-w-0">
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-white font-medium">{{ item.title }}</span>
                  <span :class="getSeverityBadge(item.severity)">{{ item.severity }}</span>
                  <span :class="getStatusBadge(item.status)">{{ item.status }}</span>
                </div>
                <div class="text-zinc-500 font-mono mt-1 space-x-2">
                  <span>Channel: {{ item.channel }}</span>
                  <span v-if="item.rule">Rule: {{ item.rule }}</span>
                  <span>Retries: {{ item.retry_count || 0 }}</span>
                </div>
                <div v-if="item.last_error" class="text-rose-400 font-mono text-[10px] mt-1 truncate max-w-md">{{ item.last_error }}</div>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <button v-if="item.status === 'failed' || item.status === 'retrying'" @click="retryItem(item.name)" class="text-xs text-emerald-400 hover:text-white hover:bg-emerald-500 border border-emerald-500/20 hover:border-emerald-500 px-2.5 py-1 rounded-lg cursor-pointer transition-all font-medium">
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Tab: Logs -->
    <template v-if="activeTab === 'logs'">
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <h3 class="text-sm font-semibold text-zinc-400">Notification Audit Log ({{ logs.length }})</h3>
        </div>
        <div v-if="!logs.length && !logsLoading" class="flex flex-col items-center justify-center p-12 bg-zinc-900 border border-zinc-800 rounded-xl">
          <Bell class="text-zinc-600 h-10 w-10 mb-2" />
          <p class="text-white text-sm font-semibold">No Notification Logs</p>
          <p class="text-zinc-500 text-xs">Logs appear here when notifications are sent.</p>
        </div>
        <div v-if="logsLoading" class="text-center p-12 text-zinc-500 text-sm animate-pulse">Loading logs...</div>
        <div class="space-y-2">
          <div v-for="l in logs" :key="l.name" class="bg-zinc-900 border border-zinc-800 rounded-xl p-3">
            <div class="flex items-start justify-between gap-3 cursor-pointer" @click="l._expanded = !l._expanded">
              <div class="flex items-center gap-2 min-w-0">
                <span class="text-white text-xs font-medium truncate">{{ l.title }}</span>
                <span :class="getSeverityBadge(l.severity)">{{ l.severity }}</span>
                <span :class="getStatusBadge(l.status)">{{ l.status }}</span>
                <span class="text-zinc-500 font-mono text-[10px]">{{ l.channel_type }} / {{ l.channel }}</span>
              </div>
              <div class="text-zinc-500 font-mono text-[10px] shrink-0 flex items-center gap-2">
                <span>{{ l.attempts || 0 }} attempts</span>
                <span>{{ l.sent_at ? new Date(l.sent_at).toLocaleString() : '' }}</span>
              </div>
            </div>
            <div v-if="l._expanded" class="mt-2 pt-2 border-t border-zinc-800/40 text-xs space-y-2">
              <div v-if="l.response" class="bg-zinc-950 border border-zinc-800/40 rounded-lg p-2 font-mono text-zinc-400 max-h-32 overflow-y-auto">
                <div class="text-zinc-500 text-[10px] uppercase font-bold mb-1">Response:</div>
                <pre class="text-zinc-300 text-[10px] whitespace-pre-wrap">{{ l.response }}</pre>
              </div>
              <div v-if="l.error_message" class="bg-rose-950/10 border border-rose-500/20 rounded-lg p-2 font-mono text-rose-400">
                <div class="text-[10px] uppercase font-bold mb-1">Error:</div>
                {{ l.error_message }}
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
import api from "../api"
import { useTelemetryStore } from "../stores/telemetry"
import { Bell, Plus, Trash2, Link, Unlink } from "lucide-vue-next"

const activeTab = ref("channels")
const loading = ref(false)
const queueLoading = ref(false)
const logsLoading = ref(false)
const showAddChannel = ref(false)
const queueFilter = ref("all")
const validationErrors = ref([])

const tabs = [
  { id: "channels", label: "Channels" },
  { id: "queue", label: "Queue" },
  { id: "logs", label: "Logs" },
]

const channels = ref([])
const queueItems = ref([])
const logs = ref([])
const telemetry = useTelemetryStore()

const unlinkedRules = computed(() => {
  return (telemetry.rules || []).filter(r => {
    const linkedNames = (channels.value || []).reduce((acc, ch) => {
      (ch._linkedRules || []).forEach(lr => acc.add(lr.name))
      return acc
    }, new Set())
    return !linkedNames.has(r.name)
  })
})

const channelTypes = [
  { value: "discord", label: "Discord" },
  { value: "email", label: "Email" },
  { value: "slack", label: "Slack" },
  { value: "http", label: "Generic HTTP" },
  { value: "teams", label: "Microsoft Teams" },
  { value: "telegram", label: "Telegram" },
  { value: "whatsapp", label: "WhatsApp (Meta)" },
  { value: "sms", label: "SMS" },
]

function getConfigFields(type) {
  const fields = {
    discord: { webhook_url: { label: "Webhook URL", type: "text", placeholder: "https://discord.com/api/webhooks/..." } },
    slack: { webhook_url: { label: "Webhook URL", type: "text", placeholder: "https://hooks.slack.com/services/..." } },
    email: {
      smtp_host: { label: "SMTP Host", type: "text", placeholder: "smtp.gmail.com" },
      smtp_port: { label: "SMTP Port", type: "number", placeholder: "587" },
      smtp_user: { label: "SMTP User", type: "text", placeholder: "user@example.com" },
      smtp_password: { label: "SMTP Password", type: "text", placeholder: "********" },
      from_email: { label: "From Email", type: "text", placeholder: "armure@example.com" },
      to_emails: { label: "To Emails (comma-sep)", type: "text", placeholder: "ops@example.com,admin@example.com" },
      use_tls: { label: "Use TLS (true/false)", type: "text", placeholder: "true" },
    },
    http: {
      url: { label: "URL", type: "text", placeholder: "https://example.com/webhook" },
      method: { label: "Method", type: "text", placeholder: "POST" },
      headers: { label: "Headers (JSON)", type: "text", placeholder: '{"Authorization":"Bearer ..."}' },
      template: { label: "Body Template", type: "textarea", placeholder: '{"message":"{message}","severity":"{severity}"}' },
    },
    teams: { webhook_url: { label: "Webhook URL", type: "text", placeholder: "https://..." } },
    telegram: { bot_token: { label: "Bot Token", type: "text", placeholder: "..." }, chat_id: { label: "Chat ID", type: "text", placeholder: "..." } },
    whatsapp: { api_endpoint: { label: "API Endpoint", type: "text", placeholder: "..." }, api_key: { label: "API Key", type: "text", placeholder: "..." }, phone_number_id: { label: "Phone Number ID", type: "text", placeholder: "..." }, to_number: { label: "To Number", type: "text", placeholder: "+1234567890" } },
    sms: { provider: { label: "Provider", type: "text", placeholder: "twilio" }, account_sid: { label: "Account SID", type: "text", placeholder: "..." }, auth_token: { label: "Auth Token", type: "text", placeholder: "..." }, from_number: { label: "From Number", type: "text", placeholder: "+1234567890" }, to_number: { label: "To Number", type: "text", placeholder: "+1234567890" } },
  }
  return fields[type] || {}
}

const channelConfigFields = computed(() => getConfigFields(newChannel.value.type))

const newChannel = ref({
  name: "", type: "slack", rateLimit: 60, config: {},
})

function onTypeChange() {
  newChannel.value.config = {}
  validationErrors.value = []
}

function getSeverityBadge(sev) {
  if (sev === "critical") return "bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[10px] px-1.5 py-0.5 rounded font-semibold font-mono uppercase"
  if (sev === "warning") return "bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] px-1.5 py-0.5 rounded font-semibold font-mono uppercase"
  return "bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px] px-1.5 py-0.5 rounded font-semibold font-mono uppercase"
}

function getStatusBadge(status) {
  const map = {
    sent: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] px-1.5 py-0.5 rounded font-semibold font-mono uppercase",
    sending: "bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px] px-1.5 py-0.5 rounded font-semibold font-mono uppercase",
    pending: "bg-zinc-700/30 text-zinc-400 border border-zinc-700/40 text-[10px] px-1.5 py-0.5 rounded font-semibold font-mono uppercase",
    failed: "bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[10px] px-1.5 py-0.5 rounded font-semibold font-mono uppercase",
    retrying: "bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] px-1.5 py-0.5 rounded font-semibold font-mono uppercase",
  }
  return map[status] || "bg-zinc-700/30 text-zinc-400 border border-zinc-700/40 text-[10px] px-1.5 py-0.5 rounded font-semibold font-mono uppercase"
}

async function fetchChannels() {
  loading.value = true
  try {
    const chs = await api.call("armure_apim_sentinel.api.notifications.list_channels")
    // Fetch linked rules for each channel
    for (const ch of chs) {
      try {
        ch._linkedRules = await api.call("armure_apim_sentinel.api.notifications.get_channel_rules", { channel_name: ch.channel_name })
      } catch {
        ch._linkedRules = []
      }
    }
    channels.value = chs
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function unlinkRule(channelName, ruleName) {
  try {
    await api.post("armure_apim_sentinel.api.notifications.unlink_rule_from_channel", { channel_name: channelName, rule_name: ruleName })
    await fetchChannels()
  } catch (e) { console.error(e) }
}

async function linkToRule(ch) {
  if (!ch._linkRuleName) return
  try {
    await api.post("armure_apim_sentinel.api.notifications.link_rule_to_channel", { channel_name: ch.channel_name, rule_name: ch._linkRuleName })
    ch._linkRuleName = ""
    ch._showLink = false
    await fetchChannels()
  } catch (e) { console.error(e) }
}

async function fetchQueue() {
  queueLoading.value = true
  try {
    queueItems.value = await api.call("armure_apim_sentinel.api.notifications.list_queue", { status: queueFilter.value })
  } catch (e) {
    console.error(e)
  } finally {
    queueLoading.value = false
  }
}

async function fetchLogs() {
  logsLoading.value = true
  try {
    logs.value = await api.call("armure_apim_sentinel.api.notifications.list_notification_logs", { limit: 50 })
  } catch (e) {
    console.error(e)
  } finally {
    logsLoading.value = false
  }
}

async function createChannel() {
  validationErrors.value = []
  try {
    const payload = {
      channel_name: newChannel.value.name,
      channel_type: newChannel.value.type,
      rate_limit_per_minute: newChannel.value.rateLimit,
      config_json: newChannel.value.config,
    }
    const result = await api.post("armure_apim_sentinel.api.notifications.create_channel", payload)
    if (result.errors) {
      validationErrors.value = result.errors
      return
    }
    showAddChannel.value = false
    newChannel.value = { name: "", type: "slack", rateLimit: 60, config: {} }
    await fetchChannels()
  } catch (e) {
    console.error(e)
  }
}

async function toggleChannel(name, currentActive) {
  try {
    await api.post("armure_apim_sentinel.api.notifications.toggle_channel", { name, is_active: !currentActive })
    await fetchChannels()
  } catch (e) { console.error(e) }
}

async function deleteChannel(name) {
  try {
    await api.post("armure_apim_sentinel.api.notifications.delete_channel", { name })
    await fetchChannels()
  } catch (e) { console.error(e) }
}

async function testChannel(name) {
  try {
    const result = await api.post("armure_apim_sentinel.api.notifications.test_channel", { name })
    if (result.status === "success") {
      alert("Test notification sent successfully!")
    } else {
      alert("Test failed: " + (result.error || result.result?.error || "Unknown error"))
    }
  } catch (e) { console.error(e) }
}

async function retryItem(name) {
  try {
    await api.post("armure_apim_sentinel.api.notifications.retry_queue_item", { queue_item_name: name })
    await fetchQueue()
  } catch (e) { console.error(e) }
}

onMounted(async () => {
  await Promise.all([fetchChannels(), fetchQueue(), fetchLogs(), telemetry.fetchRules()])
})
</script>
