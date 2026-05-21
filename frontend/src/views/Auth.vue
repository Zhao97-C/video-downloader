<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
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
  <div class="flex-1 flex items-center justify-center px-6 sm:px-10 py-20">
    <div class="w-full max-w-sm">
      <div class="rounded-2xl bg-bg-card border border-border p-8 sm:p-10 shadow-sm">
        <h1 class="text-2xl font-bold text-text-primary text-center mb-2 tracking-tight">
          {{ isLogin ? 'Welcome back' : 'Create account' }}
        </h1>
        <p class="text-text-secondary text-sm text-center mb-8">
          {{ isLogin ? 'Sign in to access your downloads' : 'Start downloading in seconds' }}
        </p>

        <form @submit.prevent="handleSubmit" class="space-y-5">
          <div>
            <label class="text-text-secondary text-xs font-medium mb-2 block">Email</label>
            <input
              v-model="email"
              type="email"
              required
              class="w-full bg-bg-input border border-border rounded-xl px-4 py-3.5 text-text-primary placeholder-text-muted outline-none focus:border-border-strong transition-colors text-sm"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label class="text-text-secondary text-xs font-medium mb-2 block">Password</label>
            <input
              v-model="password"
              type="password"
              required
              minlength="6"
              class="w-full bg-bg-input border border-border rounded-xl px-4 py-3.5 text-text-primary placeholder-text-muted outline-none focus:border-border-strong transition-colors text-sm"
              placeholder="••••••••"
            />
          </div>

          <div v-if="error" class="p-4 rounded-xl bg-red-50 border border-red-200 text-red-600 text-xs">
            {{ error }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="accent-btn w-full py-3.5 rounded-xl font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed mt-2"
          >
            {{ loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account') }}
          </button>
        </form>

        <div class="mt-6 text-center">
          <button
            @click="isLogin = !isLogin; error = ''"
            class="text-text-secondary text-sm hover:text-text-primary transition-colors"
          >
            {{ isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
