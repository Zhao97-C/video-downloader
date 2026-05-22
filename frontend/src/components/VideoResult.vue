<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  summarizeVideoStream,
  translateSubtitle,
  fetchSubtitles,
  type SubtitlesResponse,
} from '../api'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const router = useRouter()

interface FormatInfo {
  format_id: string
  ext: string
  resolution: string | null
  filesize: number | null
  vcodec: string | null
  acodec: string | null
  quality_label: string | null
  is_pro: boolean
}

interface VideoData {
  title: string
  thumbnail: string | null
  duration: number | null
  platform: string | null
  formats: FormatInfo[]
  task_id: string
  has_subtitles?: boolean
  subtitle_languages?: string[] | null
}

const props = defineProps<{ data: VideoData }>()
const downloading = ref(false)
const selectedFormat = ref<string>('')

const videoFormats = computed(() => props.data.formats.filter(f => f.resolution))
const audioFormats = computed(() => props.data.formats.filter(f => !f.resolution))

const subtitleBadge = computed(() => {
  if (props.data.has_subtitles && props.data.subtitle_languages?.length) {
    const langs = props.data.subtitle_languages.slice(0, 3).join(', ')
    return `Subtitles · ${langs}`
  }
  if (props.data.has_subtitles) return 'Subtitles available'
  return 'Subtitles may be unavailable'
})

const sourceLabel: Record<string, string> = {
  auto_subtitle: 'Auto-generated',
  manual_subtitle: 'Manual',
  description: 'From description',
  none: 'None',
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return '--:--'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatFileSize(bytes: number | null): string {
  if (!bytes) return '?'
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

function formatCueTime(seconds: number): string {
  const total = Math.floor(seconds)
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  if (h > 0) return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const aiSummary = ref('')
const aiLoading = ref(false)
let summarizeAbort: AbortController | null = null
const translateResult = ref('')
const translateLoading = ref(false)
const aiOutputLang = ref('Chinese')

const subtitles = ref<SubtitlesResponse | null>(null)
const subtitlesLoading = ref(false)
const subtitlesError = ref('')
const showPlainText = ref(false)
const subtitlesLoaded = ref(false)

const displayLines = computed(() => {
  if (!subtitles.value) return []
  if (showPlainText.value || !subtitles.value.segments.length) {
    return subtitles.value.plain_text.split('\n').filter(Boolean)
  }
  return subtitles.value.segments.map(
    seg => `${formatCueTime(seg.start)}  ${seg.text}`,
  )
})

async function handleDownload(format: FormatInfo) {
  if (format.is_pro) {
    alert('This quality requires a PRO subscription. Upgrade to unlock!')
    return
  }
  selectedFormat.value = format.format_id
  downloading.value = true

  const url = `/api/download/${props.data.task_id}?format_id=${encodeURIComponent(format.format_id)}`
  try {
    const res = await fetch(url)
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Download failed (${res.status})`)
    }
    const blob = await res.blob()
    const filename = `${props.data.title.replace(/[<>:"/\\|?*]/g, '_')}.${format.ext || 'mp4'}`
    const objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = filename
    a.click()
    URL.revokeObjectURL(objectUrl)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Download failed'
    alert(msg)
  } finally {
    downloading.value = false
    selectedFormat.value = ''
  }
}

function promptLogin() {
  const go = confirm('Sign in to view subtitles and copy transcript text.')
  if (go) router.push('/auth')
}

async function handleLoadSubtitles() {
  if (!store.isLoggedIn) {
    promptLogin()
    return
  }
  subtitlesLoading.value = true
  subtitlesError.value = ''
  try {
    subtitles.value = await fetchSubtitles(props.data.task_id)
    subtitlesLoaded.value = true
    showPlainText.value = false
  } catch (e: any) {
    subtitlesError.value = e.response?.data?.detail || 'Failed to load subtitles'
  } finally {
    subtitlesLoading.value = false
  }
}

async function handleCopySubtitles() {
  if (!store.isLoggedIn) {
    promptLogin()
    return
  }
  if (!subtitles.value) {
    await handleLoadSubtitles()
  }
  if (!subtitles.value?.plain_text) return
  try {
    await navigator.clipboard.writeText(subtitles.value.plain_text)
  } catch {
    alert('Could not copy to clipboard')
  }
}

async function handleSummarize() {
  if (!store.isLoggedIn || !store.user?.isPro) {
    alert('AI Summary requires a PRO subscription.')
    return
  }
  summarizeAbort?.abort()
  summarizeAbort = new AbortController()
  aiLoading.value = true
  aiSummary.value = ''
  try {
    await summarizeVideoStream(
      props.data.task_id,
      aiOutputLang.value,
      {
        onChunk: (text) => {
          aiSummary.value += text
        },
        onError: (message) => {
          aiSummary.value = `Error: ${message}`
        },
      },
      summarizeAbort.signal,
    )
  } catch (e: unknown) {
    if (e instanceof DOMException && e.name === 'AbortError') return
    const msg = e instanceof Error ? e.message : 'Failed to generate summary'
    aiSummary.value = `Error: ${msg}`
  } finally {
    aiLoading.value = false
    summarizeAbort = null
  }
}

async function handleTranslate() {
  if (!store.isLoggedIn || !store.user?.isPro) {
    alert('Subtitle translation requires a PRO subscription.')
    return
  }
  translateLoading.value = true
  try {
    const res = await translateSubtitle(props.data.task_id, aiOutputLang.value)
    translateResult.value = res.result
  } catch (e: any) {
    translateResult.value = `Error: ${e.response?.data?.detail || 'Failed to translate'}`
  } finally {
    translateLoading.value = false
  }
}
</script>

<template>
  <div class="rounded-2xl bg-bg-card border border-border overflow-hidden shadow-sm">
    <!-- Video Info -->
    <div class="flex gap-4 p-5">
      <div v-if="data.thumbnail" class="flex-shrink-0 w-28 h-[72px] md:w-40 md:h-24 rounded-lg overflow-hidden bg-bg-secondary">
        <img :src="`/api/proxy-image?url=${encodeURIComponent(data.thumbnail)}`" :alt="data.title" class="w-full h-full object-cover" referrerpolicy="no-referrer" />
      </div>
      <div class="flex-1 min-w-0">
        <h3 class="font-semibold text-text-primary text-sm md:text-base line-clamp-2 mb-2 leading-snug">
          {{ data.title }}
        </h3>
        <div class="flex flex-wrap items-center gap-2 text-xs text-text-secondary">
          <span v-if="data.platform" class="px-2 py-0.5 rounded-md bg-bg-input capitalize">
            {{ data.platform }}
          </span>
          <span>{{ formatDuration(data.duration) }}</span>
          <span
            class="px-2 py-0.5 rounded-md"
            :class="data.has_subtitles ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-bg-input text-text-muted'"
          >
            {{ subtitleBadge }}
          </span>
        </div>
      </div>
    </div>

    <!-- Format Selection -->
    <div class="border-t border-border">
      <!-- Video Formats -->
      <div v-if="videoFormats.length" class="p-5">
        <h4 class="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3">Video</h4>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
          <button
            v-for="fmt in videoFormats"
            :key="fmt.format_id"
            @click="handleDownload(fmt)"
            :disabled="downloading && selectedFormat === fmt.format_id"
            :class="[
              'relative px-3 py-3 rounded-xl text-left transition-all text-sm border',
              fmt.is_pro
                ? 'border-pro/30 bg-pro-light hover:bg-yellow-100'
                : 'border-border bg-bg-input hover:border-border-strong card-hover'
            ]"
          >
            <div class="flex items-center justify-between mb-0.5">
              <span class="font-semibold text-text-primary text-sm">{{ fmt.resolution }}</span>
              <span v-if="fmt.is_pro" class="pro-badge">PRO</span>
            </div>
            <div class="text-text-secondary text-xs">
              {{ fmt.ext.toUpperCase() }} · {{ formatFileSize(fmt.filesize) }}
            </div>
            <div v-if="downloading && selectedFormat === fmt.format_id" class="absolute inset-0 flex items-center justify-center bg-bg-card/80 rounded-xl">
              <svg class="w-4 h-4 animate-spin text-text-secondary" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
            </div>
          </button>
        </div>
      </div>

      <!-- Audio Formats -->
      <div v-if="audioFormats.length" class="p-5 border-t border-border">
        <h4 class="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3">Audio Only</h4>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
          <button
            v-for="fmt in audioFormats"
            :key="fmt.format_id"
            @click="handleDownload(fmt)"
            class="px-3 py-3 rounded-xl text-left transition-all text-sm border border-border bg-bg-input hover:border-border-strong card-hover"
          >
            <div class="font-semibold text-text-primary text-sm mb-0.5">{{ fmt.ext.toUpperCase() }}</div>
            <div class="text-text-secondary text-xs">{{ fmt.acodec }} · {{ formatFileSize(fmt.filesize) }}</div>
          </button>
        </div>
      </div>

      <!-- Subtitles / Transcript -->
      <div class="p-5 border-t border-border">
        <h4 class="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3">
          Subtitles / Transcript
        </h4>
        <div class="flex flex-wrap gap-2 mb-3">
          <button
            @click="handleLoadSubtitles"
            :disabled="subtitlesLoading"
            class="px-4 py-2 rounded-lg text-sm border border-border bg-bg-input hover:border-border-strong text-text-primary transition-all disabled:opacity-50"
          >
            {{ subtitlesLoading ? 'Loading...' : subtitlesLoaded ? 'Reload' : 'View Subtitles' }}
          </button>
          <button
            v-if="subtitlesLoaded && subtitles?.plain_text"
            @click="handleCopySubtitles"
            class="px-4 py-2 rounded-lg text-sm border border-border bg-bg-input hover:border-border-strong text-text-primary transition-all"
          >
            Copy
          </button>
          <button
            v-if="subtitlesLoaded && subtitles?.segments?.length"
            @click="showPlainText = !showPlainText"
            class="px-4 py-2 rounded-lg text-sm border border-border bg-bg-input hover:border-border-strong text-text-secondary transition-all"
          >
            {{ showPlainText ? 'Show timestamps' : 'Plain text only' }}
          </button>
        </div>

        <div v-if="subtitlesError" class="p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm">
          {{ subtitlesError }}
        </div>

        <div
          v-else-if="subtitlesLoaded && subtitles"
          class="rounded-xl border border-border bg-bg-input overflow-hidden"
        >
          <div class="px-4 py-2 border-b border-border flex flex-wrap gap-2 text-xs text-text-secondary">
            <span v-if="subtitles.language" class="px-2 py-0.5 rounded-md bg-bg-card">{{ subtitles.language }}</span>
            <span class="px-2 py-0.5 rounded-md bg-bg-card">{{ sourceLabel[subtitles.source] || subtitles.source }}</span>
            <span v-if="subtitles.extraction_method" class="px-2 py-0.5 rounded-md bg-bg-card capitalize">
              via {{ subtitles.extraction_method.replace('_', ' ') }}
            </span>
            <span v-if="subtitles.truncated" class="text-amber-600">Truncated preview</span>
          </div>

          <div
            v-if="subtitles.source === 'none'"
            class="p-4 text-sm text-text-secondary space-y-2"
          >
            <p>No timed subtitles could be extracted for this video.</p>
            <p v-if="subtitles.hint" class="text-xs text-amber-700">{{ subtitles.hint }}</p>
            <p v-else-if="data.platform?.toLowerCase().includes('bilibili')" class="text-xs text-amber-700">
              Bilibili CC/AI subtitles often require <code class="text-xs">BILIBILI_SESSDATA</code> in backend .env.
            </p>
          </div>

          <div
            v-else
            class="p-4 max-h-[40vh] overflow-y-auto text-sm text-text-secondary leading-relaxed font-mono tabular-nums space-y-1"
          >
            <p v-for="(line, i) in displayLines" :key="i" class="whitespace-pre-wrap break-words">
              {{ line }}
            </p>
          </div>
        </div>
      </div>

      <!-- AI Features -->
      <div class="p-5 border-t border-border">
        <h4 class="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
          AI Tools <span class="pro-badge">PRO</span>
        </h4>
        <div class="flex gap-2 flex-wrap items-center">
          <button
            @click="handleSummarize"
            :disabled="aiLoading"
            class="px-4 py-2 rounded-lg text-sm border border-border bg-bg-input hover:border-border-strong text-text-primary transition-all disabled:opacity-50"
          >
            {{ aiLoading ? 'Summarizing...' : 'AI Summary' }}
          </button>
          <button
            @click="handleTranslate"
            :disabled="translateLoading"
            class="px-4 py-2 rounded-lg text-sm border border-border bg-bg-input hover:border-border-strong text-text-primary transition-all disabled:opacity-50"
          >
            {{ translateLoading ? 'Translating...' : 'Translate Subtitles' }}
          </button>
          <label class="flex items-center gap-1.5 text-xs text-text-secondary">
            <span class="whitespace-nowrap">Output</span>
            <select
              v-model="aiOutputLang"
              class="px-3 py-2 rounded-lg text-sm border border-border bg-bg-input text-text-primary"
              title="Summary and translation output language"
            >
              <option value="Chinese">Chinese</option>
              <option value="English">English</option>
              <option value="Japanese">Japanese</option>
              <option value="Korean">Korean</option>
              <option value="Spanish">Spanish</option>
            </select>
          </label>
        </div>

        <div v-if="aiSummary || aiLoading" class="mt-4 p-4 rounded-xl bg-bg-input border border-border text-text-secondary text-sm leading-relaxed whitespace-pre-wrap">
          <div class="font-medium text-text-primary mb-1.5 text-xs uppercase tracking-wider flex items-center gap-2">
            Summary
            <span v-if="aiLoading && !aiSummary" class="text-text-muted font-normal normal-case">Generating...</span>
          </div>
          {{ aiSummary }}<span v-if="aiLoading" class="inline-block w-0.5 h-4 ml-0.5 bg-text-secondary animate-pulse align-middle" />
        </div>

        <div v-if="translateResult" class="mt-4 p-4 rounded-xl bg-bg-input border border-border text-text-secondary text-sm leading-relaxed whitespace-pre-wrap">
          <div class="font-medium text-text-primary mb-1.5 text-xs uppercase tracking-wider">Translation</div>
          {{ translateResult }}
        </div>
      </div>
    </div>
  </div>
</template>
