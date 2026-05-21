<script setup lang="ts">
import { ref } from 'vue'
import { parseVideo } from '../api'
import VideoResult from './VideoResult.vue'

const url = ref('')
const loading = ref(false)
const error = ref('')
const result = ref<any>(null)
const selectedMode = ref<'auto' | 'audio' | 'video'>('auto')

async function handlePaste() {
  try {
    const text = await navigator.clipboard.readText()
    url.value = text
  } catch {
    // clipboard permission denied
  }
}

async function handleSubmit() {
  if (!url.value.trim()) return
  loading.value = true
  error.value = ''
  result.value = null

  try {
    const data = await parseVideo(url.value.trim(), selectedMode.value)
    result.value = data
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to parse the video URL. Please check and try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-2xl mx-auto mb-20 md:mb-28">
    <!-- Input -->
    <div class="flex items-center bg-bg-card border border-border rounded-2xl overflow-hidden shadow-sm hover:border-border-strong transition-colors">
      <div class="pl-5 text-text-muted flex-shrink-0">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
      </div>
      <input
        v-model="url"
        type="url"
        placeholder="paste the link here"
        class="flex-1 bg-transparent px-4 py-5 text-text-primary placeholder-text-muted outline-none text-sm md:text-base"
        @keydown.enter="handleSubmit"
      />
      <button
        @click="handleSubmit"
        :disabled="loading || !url.trim()"
        class="accent-btn px-5 py-3 mr-2 rounded-xl font-medium text-sm disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 flex-shrink-0"
      >
        <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        <span class="hidden sm:inline">{{ loading ? 'Parsing...' : 'Download' }}</span>
      </button>
    </div>

    <!-- Mode + Paste Row -->
    <div class="flex items-center justify-between mt-3 px-1">
      <div class="flex items-center gap-1.5">
        <button
          v-for="mode in (['auto', 'video', 'audio'] as const)"
          :key="mode"
          @click="selectedMode = mode"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            selectedMode === mode ? 'mode-pill-active' : 'mode-pill-inactive'
          ]"
        >
          {{ mode === 'auto' ? 'auto' : mode === 'video' ? 'video' : 'audio' }}
        </button>
      </div>

      <div class="flex items-center gap-2">
        <span class="text-text-muted text-xs">3 free / day</span>
        <button
          @click="handlePaste"
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-text-secondary hover:text-text-primary hover:bg-bg-secondary transition-colors border border-border"
          title="Paste from clipboard"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          paste
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mt-4 p-4 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm text-center">
      {{ error }}
    </div>

    <!-- Result -->
    <VideoResult v-if="result" :data="result" class="mt-6" />
  </div>
</template>
