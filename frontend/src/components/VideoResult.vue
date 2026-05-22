<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  summarizeVideoStream,
  translateSubtitle,
  fetchSubtitles,
  mindmapStream,
  type SubtitlesResponse,
} from '../api'
import { useAppStore } from '../stores/app'
import MindMapViewer from './MindMapViewer.vue'
import VideoChatPanel from './VideoChatPanel.vue'

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

const mindmapMarkdown = ref('')
const mindmapLoading = ref(false)
const mindmapError = ref('')
const mindmapFromMetadata = ref(false)
const mindmapLoaded = ref(false)
const mindmapFullscreen = ref(false)
let mindmapAbort: AbortController | null = null

const isPro = computed(() => !!store.user?.isPro)

const mindmapPreviewMarkdown = computed(() => {
  const title = props.data.title.replace(/[#\n]/g, ' ').trim() || 'Video'
  return `# ${title}

## Key topics
- Main theme and context
- Core arguments or steps

## Highlights
- Important detail A
- Important detail B

## Takeaways
- Summary point 1
- Summary point 2`
})

const subtitles = ref<SubtitlesResponse | null>(null)
const subtitlesLoading = ref(false)
const subtitlesError = ref('')
const showPlainText = ref(false)
const subtitlesLoaded = ref(false)

type MainTab = 'download' | 'subtitles' | 'ai'
type AiSubTab = 'summary' | 'translate' | 'mindmap' | 'chat'
const activeMainTab = ref<MainTab>('download')
const activeAiSubTab = ref<AiSubTab>('summary')

const mainTabs: { id: MainTab; label: string }[] = [
  { id: 'download', label: 'Download' },
  { id: 'subtitles', label: 'Subtitles' },
  { id: 'ai', label: 'AI Tools' },
]

const aiSubTabs: { id: AiSubTab; label: string; pro?: boolean }[] = [
  { id: 'summary', label: 'Summary' },
  { id: 'translate', label: 'Translate' },
  { id: 'mindmap', label: 'Mind Map', pro: true },
  { id: 'chat', label: 'Q&A', pro: true },
]

function mainTabClass(tab: MainTab) {
  return [
    'shrink-0 px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors',
    activeMainTab.value === tab
      ? 'border-text-primary text-text-primary'
      : 'border-transparent text-text-secondary hover:text-text-primary',
  ]
}

function aiSubTabClass(tab: AiSubTab) {
  return [
    'shrink-0 px-3 py-2 text-xs font-medium whitespace-nowrap rounded-lg transition-colors',
    activeAiSubTab.value === tab
      ? 'bg-bg-input text-text-primary border border-border-strong'
      : 'text-text-secondary hover:text-text-primary hover:bg-bg-input/60',
  ]
}

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
  activeMainTab.value = 'subtitles'
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
  activeMainTab.value = 'ai'
  activeAiSubTab.value = 'summary'
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
  activeMainTab.value = 'ai'
  activeAiSubTab.value = 'translate'
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

async function handleMindmap() {
  activeMainTab.value = 'ai'
  activeAiSubTab.value = 'mindmap'
  if (!store.isLoggedIn || !isPro.value) return
  mindmapAbort?.abort()
  mindmapAbort = new AbortController()
  mindmapLoading.value = true
  mindmapError.value = ''
  mindmapMarkdown.value = ''
  mindmapFromMetadata.value = false
  try {
    await mindmapStream(
      props.data.task_id,
      aiOutputLang.value,
      {
        onChunk: (text) => {
          mindmapMarkdown.value += text
        },
        onDone: (meta) => {
          mindmapFromMetadata.value = !!meta?.from_metadata_only
          mindmapLoaded.value = true
        },
        onError: (message) => {
          mindmapError.value = message
        },
      },
      mindmapAbort.signal,
    )
  } catch (e: unknown) {
    if (e instanceof DOMException && e.name === 'AbortError') return
    const msg = e instanceof Error ? e.message : 'Failed to generate mind map'
    mindmapError.value = msg
  } finally {
    mindmapLoading.value = false
    mindmapAbort = null
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

    <!-- Main tabs -->
    <div class="border-t border-border">
      <div
        class="flex overflow-x-auto border-b border-border scrollbar-thin"
        role="tablist"
        aria-label="Video actions"
      >
        <button
          v-for="tab in mainTabs"
          :key="tab.id"
          type="button"
          role="tab"
          :aria-selected="activeMainTab === tab.id"
          :class="mainTabClass(tab.id)"
          @click="activeMainTab = tab.id"
        >
          {{ tab.label }}
          <span v-if="tab.id === 'ai'" class="pro-badge ml-1.5">PRO</span>
        </button>
      </div>

      <div class="min-h-[280px] max-h-[min(55vh,520px)] overflow-y-auto p-5">
        <!-- Download -->
        <div v-show="activeMainTab === 'download'" role="tabpanel">
          <div v-if="videoFormats.length" class="mb-5">
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

          <div v-if="audioFormats.length">
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

          <p
            v-if="!videoFormats.length && !audioFormats.length"
            class="text-sm text-text-secondary"
          >
            No downloadable formats found.
          </p>
        </div>

        <!-- Subtitles -->
        <div v-show="activeMainTab === 'subtitles'" role="tabpanel">
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
              class="p-4 text-sm text-text-secondary leading-relaxed font-mono tabular-nums space-y-1"
            >
              <p v-for="(line, i) in displayLines" :key="i" class="whitespace-pre-wrap break-words">
                {{ line }}
              </p>
            </div>
          </div>

          <p v-else-if="!subtitlesLoading" class="text-sm text-text-muted">
            Click View Subtitles to load transcript for this video.
          </p>
        </div>

        <!-- AI Tools -->
        <div v-show="activeMainTab === 'ai'" role="tabpanel">
          <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div
              class="flex gap-1 overflow-x-auto"
              role="tablist"
              aria-label="AI features"
            >
              <button
                v-for="tab in aiSubTabs"
                :key="tab.id"
                type="button"
                role="tab"
                :aria-selected="activeAiSubTab === tab.id"
                :class="aiSubTabClass(tab.id)"
                @click="activeAiSubTab = tab.id"
              >
                {{ tab.label }}
                <span v-if="tab.pro" class="pro-badge ml-1 scale-90">PRO</span>
              </button>
            </div>
            <label class="flex items-center gap-1.5 text-xs text-text-secondary shrink-0">
              <span class="whitespace-nowrap">Output</span>
              <select
                v-model="aiOutputLang"
                class="px-3 py-2 rounded-lg text-sm border border-border bg-bg-input text-text-primary"
                title="AI output language"
              >
                <option value="Chinese">Chinese</option>
                <option value="English">English</option>
                <option value="Japanese">Japanese</option>
                <option value="Korean">Korean</option>
                <option value="Spanish">Spanish</option>
              </select>
            </label>
          </div>

          <!-- Summary -->
          <div v-show="activeAiSubTab === 'summary'">
            <button
              @click="handleSummarize"
              :disabled="aiLoading"
              class="px-4 py-2 rounded-lg text-sm border border-border bg-bg-input hover:border-border-strong text-text-primary transition-all disabled:opacity-50"
            >
              {{ aiLoading ? 'Summarizing...' : 'AI Summary' }}
            </button>
            <div
              v-if="aiSummary || aiLoading"
              class="mt-4 p-4 rounded-xl bg-bg-input border border-border text-text-secondary text-sm leading-relaxed whitespace-pre-wrap"
            >
              <div class="font-medium text-text-primary mb-1.5 text-xs uppercase tracking-wider flex items-center gap-2">
                Summary
                <span v-if="aiLoading && !aiSummary" class="text-text-muted font-normal normal-case">Generating...</span>
              </div>
              {{ aiSummary }}<span v-if="aiLoading" class="inline-block w-0.5 h-4 ml-0.5 bg-text-secondary animate-pulse align-middle" />
            </div>
            <p v-else class="mt-4 text-sm text-text-muted">Click AI Summary to generate from subtitles.</p>
          </div>

          <!-- Translate -->
          <div v-show="activeAiSubTab === 'translate'">
            <button
              @click="handleTranslate"
              :disabled="translateLoading"
              class="px-4 py-2 rounded-lg text-sm border border-border bg-bg-input hover:border-border-strong text-text-primary transition-all disabled:opacity-50"
            >
              {{ translateLoading ? 'Translating...' : 'Translate Subtitles' }}
            </button>
            <div
              v-if="translateResult"
              class="mt-4 p-4 rounded-xl bg-bg-input border border-border text-text-secondary text-sm leading-relaxed whitespace-pre-wrap"
            >
              <div class="font-medium text-text-primary mb-1.5 text-xs uppercase tracking-wider">Translation</div>
              {{ translateResult }}
            </div>
            <p v-else class="mt-4 text-sm text-text-muted">Click Translate Subtitles to convert transcript to your output language.</p>
          </div>

          <!-- Mind Map -->
          <div v-show="activeAiSubTab === 'mindmap'">
            <div class="flex flex-wrap items-center gap-2 mb-3">
              <button
                @click="handleMindmap"
                :disabled="mindmapLoading"
                class="px-4 py-2 rounded-lg text-sm border border-border bg-bg-input hover:border-border-strong text-text-primary transition-all disabled:opacity-50"
              >
                {{ mindmapLoading ? 'Building map...' : mindmapLoaded ? 'Refresh Mind Map' : 'Mind Map' }}
              </button>
              <button
                v-if="isPro && mindmapLoaded && mindmapMarkdown"
                type="button"
                class="px-3 py-1.5 rounded-lg text-xs border border-border bg-bg-input hover:border-border-strong text-text-primary transition-all"
                @click="mindmapFullscreen = true"
              >
                Fullscreen
              </button>
            </div>

            <div v-if="mindmapError" class="mb-3 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm">
              {{ mindmapError }}
            </div>

            <div
              v-if="mindmapFromMetadata && mindmapLoaded"
              class="mb-3 px-3 py-2 rounded-lg text-xs text-amber-700 bg-amber-50 border border-amber-200"
            >
              Based on limited metadata (no timed subtitles).
            </div>

            <div class="relative rounded-xl border border-border overflow-hidden h-[min(50vh,400px)]">
              <div :class="{ 'blur-[6px] select-none pointer-events-none': !isPro }" class="h-full">
                <MindMapViewer
                  :markdown="isPro && mindmapMarkdown && !mindmapLoading ? mindmapMarkdown : mindmapPreviewMarkdown"
                  :loading="isPro && mindmapLoading"
                  :interactive="isPro && !!mindmapMarkdown && !mindmapLoading"
                  class="h-full"
                />
              </div>
              <div
                v-if="!isPro"
                class="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-bg-card/55 backdrop-blur-[2px] px-6 text-center"
              >
                <p class="text-sm text-text-primary font-medium">Visualize video structure as a mind map</p>
                <p class="text-xs text-text-secondary max-w-sm">Upgrade to PRO to generate interactive maps from subtitles.</p>
                <router-link
                  to="/pricing"
                  class="px-5 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-[#7c3aed] to-[#3b82f6] text-white shadow-sm hover:opacity-95 transition-opacity"
                >
                  Upgrade to PRO
                </router-link>
              </div>
              <div
                v-else-if="isPro && !mindmapLoaded && !mindmapLoading"
                class="absolute inset-0 flex items-center justify-center bg-bg-card/40 pointer-events-none"
              >
                <p class="text-xs text-text-secondary px-4 text-center">Click Mind Map to generate from subtitles</p>
              </div>
            </div>
          </div>

          <!-- Q&A -->
          <div v-show="activeAiSubTab === 'chat'">
            <VideoChatPanel
              embedded
              :task-id="data.task_id"
              :title="data.title"
              :output-language="aiOutputLang"
              :is-pro="isPro"
              :is-logged-in="store.isLoggedIn"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Mind map fullscreen -->
    <Teleport to="body">
      <div
        v-if="mindmapFullscreen && mindmapMarkdown"
        class="fixed inset-0 z-[100] flex flex-col bg-bg-primary"
      >
        <div class="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
          <span class="text-sm font-medium text-text-primary">Mind Map</span>
          <button
            type="button"
            class="px-4 py-2 rounded-lg text-sm border border-border bg-bg-input hover:border-border-strong text-text-primary"
            @click="mindmapFullscreen = false"
          >
            Close
          </button>
        </div>
        <div class="flex-1 min-h-0 p-4">
          <MindMapViewer
            :markdown="mindmapMarkdown"
            :interactive="true"
            class="h-full"
          />
        </div>
      </div>
    </Teleport>
  </div>
</template>
