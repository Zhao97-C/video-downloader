<script setup lang="ts">
import { ref, computed } from 'vue'
import { summarizeVideo, translateSubtitle } from '../api'
import { useAppStore } from '../stores/app'

const store = useAppStore()

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
}

const props = defineProps<{ data: VideoData }>()
const downloading = ref(false)
const selectedFormat = ref<string>('')

const videoFormats = computed(() => props.data.formats.filter(f => f.resolution))
const audioFormats = computed(() => props.data.formats.filter(f => !f.resolution))

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

const aiSummary = ref('')
const aiLoading = ref(false)
const translateResult = ref('')
const translateLoading = ref(false)

function handleDownload(format: FormatInfo) {
  if (format.is_pro) {
    alert('This quality requires a PRO subscription. Upgrade to unlock!')
    return
  }
  selectedFormat.value = format.format_id
  downloading.value = true

  const url = `/api/download/${props.data.task_id}?format_id=${format.format_id}`
  window.open(url, '_blank')

  setTimeout(() => {
    downloading.value = false
    selectedFormat.value = ''
  }, 3000)
}

async function handleSummarize() {
  if (!store.isLoggedIn || !store.user?.isPro) {
    alert('AI Summary requires a PRO subscription.')
    return
  }
  aiLoading.value = true
  try {
    const res = await summarizeVideo(props.data.title, `Video: ${props.data.title}`)
    aiSummary.value = res.result
  } catch (e: any) {
    aiSummary.value = `Error: ${e.response?.data?.detail || 'Failed to generate summary'}`
  } finally {
    aiLoading.value = false
  }
}

async function handleTranslate() {
  if (!store.isLoggedIn || !store.user?.isPro) {
    alert('Subtitle translation requires a PRO subscription.')
    return
  }
  translateLoading.value = true
  try {
    const res = await translateSubtitle(`Video: ${props.data.title}`, 'Chinese')
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
        <img :src="data.thumbnail" :alt="data.title" class="w-full h-full object-cover" />
      </div>
      <div class="flex-1 min-w-0">
        <h3 class="font-semibold text-text-primary text-sm md:text-base line-clamp-2 mb-2 leading-snug">
          {{ data.title }}
        </h3>
        <div class="flex items-center gap-2 text-xs text-text-secondary">
          <span v-if="data.platform" class="px-2 py-0.5 rounded-md bg-bg-input capitalize">
            {{ data.platform }}
          </span>
          <span>{{ formatDuration(data.duration) }}</span>
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

      <!-- AI Features -->
      <div class="p-5 border-t border-border">
        <h4 class="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
          AI Tools <span class="pro-badge">PRO</span>
        </h4>
        <div class="flex gap-2 flex-wrap">
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
        </div>

        <div v-if="aiSummary" class="mt-4 p-4 rounded-xl bg-bg-input border border-border text-text-secondary text-sm leading-relaxed whitespace-pre-wrap">
          <div class="font-medium text-text-primary mb-1.5 text-xs uppercase tracking-wider">Summary</div>
          {{ aiSummary }}
        </div>

        <div v-if="translateResult" class="mt-4 p-4 rounded-xl bg-bg-input border border-border text-text-secondary text-sm leading-relaxed whitespace-pre-wrap">
          <div class="font-medium text-text-primary mb-1.5 text-xs uppercase tracking-wider">Translation</div>
          {{ translateResult }}
        </div>
      </div>
    </div>
  </div>
</template>
