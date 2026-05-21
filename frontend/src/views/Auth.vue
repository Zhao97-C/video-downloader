<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import NavBar from '../components/NavBar.vue'
import { login, register } from '../api'
import { useAppStore } from '../stores/app'

const router = useRouter()
const store = useAppStore()

const isLogin = ref(true)
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  if (!email.value || !password.value) return
  loading.value = true
  error.value = ''

  try {
    const fn = isLogin.value ? login : register
    const data = await fn(email.value, password.value)
    store.setToken(data.access_token)
    await store.fetchProfile()
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <NavBar />
    <main class="flex-1 flex items-center justify-center px-4 pt-16">
      <div class="w-full max-w-sm">
        <div class="rounded-2xl bg-bg-card border border-border p-8">
          <h1 class="text-2xl font-bold text-center mb-2">
            {{ isLogin ? 'Welcome Back' : 'Create Account' }}
          </h1>
          <p class="text-text-secondary text-sm text-center mb-6">
            {{ isLogin ? 'Sign in to access your downloads' : 'Start downloading in seconds' }}
          </p>

          <form @submit.prevent="handleSubmit" class="space-y-4">
            <div>
              <label class="text-text-secondary text-xs font-medium mb-1 block">Email</label>
              <input
                v-model="email"
                type="email"
                required
                class="w-full bg-bg-input border border-border rounded-lg px-4 py-3 text-text-primary placeholder-text-secondary/50 outline-none focus:border-brand-purple/50 transition-colors text-sm"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label class="text-text-secondary text-xs font-medium mb-1 block">Password</label>
              <input
                v-model="password"
                type="password"
                required
                minlength="6"
                class="w-full bg-bg-input border border-border rounded-lg px-4 py-3 text-text-primary placeholder-text-secondary/50 outline-none focus:border-brand-purple/50 transition-colors text-sm"
                placeholder="••••••••"
              />
            </div>

            <div v-if="error" class="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
              {{ error }}
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full gradient-btn text-white py-3 rounded-xl font-medium text-sm disabled:opacity-50"
            >
              {{ loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account') }}
            </button>
          </form>

          <div class="mt-6 text-center">
            <button
              @click="isLogin = !isLogin; error = ''"
              class="text-brand-purple text-sm hover:underline"
            >
              {{ isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in' }}
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
