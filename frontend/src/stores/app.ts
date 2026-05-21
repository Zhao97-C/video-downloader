import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getProfile } from '../api'

export const useAppStore = defineStore('app', () => {
  const user = ref<{ id: number; email: string; isPro: boolean } | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const dailyUsage = ref(parseInt(localStorage.getItem('dailyUsage') || '0'))
  const maxFreeDaily = 3

  const isLoggedIn = computed(() => !!token.value)
  const canDownload = computed(() => user.value?.isPro || dailyUsage.value < maxFreeDaily)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function setUser(u: { id: number; email: string; isPro: boolean } | null) {
    user.value = u
  }

  function incrementUsage() {
    dailyUsage.value++
    localStorage.setItem('dailyUsage', String(dailyUsage.value))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  async function fetchProfile() {
    if (!token.value) return
    try {
      const profile = await getProfile()
      user.value = { id: profile.id, email: profile.email, isPro: profile.is_pro }
    } catch {
      logout()
    }
  }

  return { user, token, dailyUsage, maxFreeDaily, isLoggedIn, canDownload, setToken, setUser, incrementUsage, logout, fetchProfile }
})
