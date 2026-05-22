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

export interface SubtitleSegment {
  start: number
  end: number
  text: string
}

export type SubtitleSource = 'auto_subtitle' | 'manual_subtitle' | 'description' | 'none'

export interface SubtitlesResponse {
  source: SubtitleSource
  language: string | null
  segments: SubtitleSegment[]
  plain_text: string
  char_count: number
  truncated: boolean
  has_timestamps: boolean
  extraction_method: string | null
  hint: string | null
}

export async function fetchSubtitles(taskId: string): Promise<SubtitlesResponse> {
  const res = await api.post('/ai/subtitles', { task_id: taskId })
  return res.data
}

export interface SummarizeStreamCallbacks {
  onChunk: (text: string) => void
  onDone?: () => void
  onError?: (message: string) => void
}

function parseSseBlock(block: string): { event: string; data: string } | null {
  const lines = block.split('\n').filter(Boolean)
  if (!lines.length) return null
  let event = 'message'
  const dataLines: string[] = []
  for (const line of lines) {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim())
    }
  }
  if (!dataLines.length) return null
  return { event, data: dataLines.join('\n') }
}

export async function summarizeVideoStream(
  taskId: string,
  outputLanguage: string,
  callbacks: SummarizeStreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const token = localStorage.getItem('token')
  const res = await fetch('/api/ai/summarize', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      task_id: taskId,
      output_language: outputLanguage,
    }),
    signal,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    const detail = err.detail
    const message = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('; ')
        : `Failed (${res.status})`
    throw new Error(message || `Failed (${res.status})`)
  }

  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    const data = await res.json() as { result?: string; detail?: string }
    if (data.result) {
      callbacks.onChunk(data.result)
      callbacks.onDone?.()
      return
    }
    throw new Error(
      typeof data.detail === 'string' ? data.detail : 'Empty summary response',
    )
  }

  const reader = res.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  const processBlocks = (blocks: string[]) => {
    for (const block of blocks) {
      const parsed = parseSseBlock(block)
      if (!parsed) continue
      try {
        const payload = JSON.parse(parsed.data) as { content?: string; done?: boolean; detail?: string }
        if (parsed.event === 'error') {
          callbacks.onError?.(payload.detail || 'Stream error')
          return false
        }
        if (payload.content) callbacks.onChunk(payload.content)
        if (payload.done) callbacks.onDone?.()
      } catch {
        // ignore malformed SSE frames
      }
    }
    return true
  }

  const drainBuffer = () => {
    buffer = buffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() ?? ''
    return processBlocks(blocks)
  }

  const readRest = async () => {
    while (true) {
      const { done, value } = await reader.read()
      if (value) buffer += decoder.decode(value, { stream: true })
      if (!drainBuffer()) return
      if (done) {
        buffer += decoder.decode()
        drainBuffer()
        break
      }
    }
  }

  const first = await reader.read()
  if (first.value) buffer += decoder.decode(first.value, { stream: true })

  if (buffer.trimStart().startsWith('{')) {
    await readRest()
    const data = JSON.parse(buffer) as { result?: string; detail?: string }
    if (data.result) {
      callbacks.onChunk(data.result)
      callbacks.onDone?.()
      return
    }
    throw new Error(
      typeof data.detail === 'string' ? data.detail : 'Empty summary response',
    )
  }

  if (!drainBuffer()) return
  if (!first.done) await readRest()
  else {
    buffer += decoder.decode()
    drainBuffer()
  }
}

export async function translateSubtitle(taskId: string, targetLanguage: string = 'Chinese') {
  const res = await api.post('/ai/translate-subtitle', {
    task_id: taskId,
    target_language: targetLanguage,
  })
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
