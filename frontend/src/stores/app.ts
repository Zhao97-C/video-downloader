import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getProfile, getSiteConfig, type SiteConfig } from '../api'

const DEFAULT_CONFIG: SiteConfig = {
  site_name: 'SaveAny',
  free_daily_limit: 3,
  free_max_resolution: 720,
  pro_monthly_price: '$9.9',
  pro_monthly_period: '/month',
  pro_yearly_price: '$99',
  pro_yearly_period: '/year',
  pro_yearly_savings: 'Save 17%',
  payment_enabled: false,
}

export const useAppStore = defineStore('app', () => {
  const user = ref<{ id: number; email: string; isPro: boolean } | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const dailyUsage = ref(parseInt(localStorage.getItem('dailyUsage') || '0'))
  const siteConfig = ref<SiteConfig>({ ...DEFAULT_CONFIG })

  const isLoggedIn = computed(() => !!token.value)
  const canDownload = computed(
    () => user.value?.isPro || dailyUsage.value < siteConfig.value.free_daily_limit,
  )

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

  async function fetchConfig() {
    try {
      siteConfig.value = await getSiteConfig()
    } catch {
      // backend offline – keep defaults
    }
  }

  return {
    user,
    token,
    dailyUsage,
    siteConfig,
    isLoggedIn,
    canDownload,
    setToken,
    setUser,
    incrementUsage,
    logout,
    fetchProfile,
    fetchConfig,
  }
})
