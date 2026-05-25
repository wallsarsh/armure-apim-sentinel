<template>
  <div class="flex min-h-screen bg-zinc-950 items-center justify-center p-6">
    <div class="w-full max-w-sm bg-zinc-900 border border-zinc-800 rounded-2xl p-8 space-y-6 shadow-2xl">
      <div class="text-center space-y-1">
        <h1 class="text-white text-xl font-bold">API Security Monitor</h1>
        <p class="text-zinc-500 text-xs">Sign in to your account</p>
      </div>
      <form class="space-y-4" @submit.prevent="makeLoginRequest">
        <div class="space-y-1">
          <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Email</label>
          <input
            v-model="email"
            type="text"
            placeholder="you@example.com"
            autocomplete="email"
            required
            class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-white text-sm focus:outline-none focus:border-emerald-500 font-medium placeholder:text-zinc-600"
          />
        </div>
        <div class="space-y-1">
          <label class="text-zinc-500 font-bold uppercase text-[10px] tracking-wider">Password</label>
          <input
            v-model="password"
            type="password"
            placeholder="••••••••"
            autocomplete="current-password"
            required
            class="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-white text-sm focus:outline-none focus:border-emerald-500 font-medium placeholder:text-zinc-600"
          />
        </div>
        <div v-if="errorMessage" class="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg text-xs font-mono">{{ errorMessage }}</div>
        <button
          type="submit"
          :disabled="loggingIn"
          class="w-full px-4 py-2.5 bg-zinc-100 hover:bg-zinc-200 text-zinc-950 rounded-lg font-bold text-sm cursor-pointer transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loggingIn" class="h-4 w-4 border-2 border-zinc-950/30 border-t-zinc-950 rounded-full animate-spin" />
          <span>{{ loggingIn ? "Signing in..." : "Sign in" }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useSessionStore } from "../stores/sessionStore"

const session = useSessionStore()
const router = useRouter()

const loggingIn = ref(false)
const email = ref("")
const password = ref("")
const errorMessage = ref(null)

async function makeLoginRequest() {
  if (!email.value || !password.value) return
  errorMessage.value = null
  loggingIn.value = true
  try {
    await session.login(email.value, password.value)
    router.push("/")
  } catch (e) {
    errorMessage.value = e.message || "Invalid email or password"
  } finally {
    loggingIn.value = false
  }
}
</script>