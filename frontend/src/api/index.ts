import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api

export async function parseVideo(url: string, mode: string = 'auto') {
  const res = await api.post('/parse', { url, mode })
  return res.data
}

export function getDownloadUrl(taskId: string, formatId: string) {
  return `/api/download/${taskId}?format_id=${formatId}`
}

export async function register(email: string, password: string) {
  const res = await api.post('/auth/register', { email, password })
  return res.data
}

export async function login(email: string, password: string) {
  const res = await api.post('/auth/login', { email, password })
  return res.data
}

export async function getProfile() {
  const res = await api.get('/auth/profile')
  return res.data
}

export async function createCheckout(plan: string = 'monthly') {
  const res = await api.post('/payment/create-checkout', null, { params: { plan } })
  return res.data
}

export async function summarizeVideo(title: string, subtitles: string) {
  const res = await api.post('/ai/summarize', { title, subtitles })
  return res.data
}

export async function translateSubtitle(text: string, targetLanguage: string = 'Chinese') {
  const res = await api.post('/ai/translate-subtitle', { text, target_language: targetLanguage })
  return res.data
}

export interface SiteConfig {
  site_name: string
  free_daily_limit: number
  free_max_resolution: number
  pro_monthly_price: string
  pro_monthly_period: string
  pro_yearly_price: string
  pro_yearly_period: string
  pro_yearly_savings: string
  payment_enabled: boolean
}

export async function getSiteConfig(): Promise<SiteConfig> {
  const res = await api.get('/config')
  return res.data
}
