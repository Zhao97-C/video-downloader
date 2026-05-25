<script setup lang="ts">
defineProps<{
  loading: boolean
  text: string
  error: string
  quotaExceeded: boolean
  fromMetadataOnly: boolean
  summarizeLimit: number
}>()
</script>

<template>
  <div class="mt-4 rounded-xl border border-border bg-bg-input overflow-hidden">
    <div class="px-3 py-2 border-b border-border flex items-center justify-between gap-2">
      <span class="text-xs font-medium text-text-primary uppercase tracking-wider">AI 总结</span>
      <span v-if="loading && !text" class="text-xs text-text-muted">生成中…</span>
    </div>

    <div v-if="quotaExceeded" class="p-4 text-sm text-center space-y-3">
      <p class="text-text-secondary">
        今日免费总结已达 {{ summarizeLimit }} 次（按解析视频计）。升级 PRO 可无限使用。
      </p>
      <router-link
        to="/pricing"
        class="inline-flex px-5 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-[#7c3aed] to-[#3b82f6] text-white hover:opacity-95 transition-opacity"
      >
        升级 PRO
      </router-link>
    </div>

    <div v-else-if="error" class="p-4 text-sm text-red-600">
      {{ error }}
    </div>

    <div v-else-if="loading && !text" class="p-4 space-y-2 animate-pulse">
      <div class="h-3 bg-bg-card rounded w-full" />
      <div class="h-3 bg-bg-card rounded w-5/6" />
      <div class="h-3 bg-bg-card rounded w-4/6" />
      <p class="text-xs text-text-muted pt-1">正在提取字幕并生成总结，请稍候…</p>
    </div>

    <div v-else class="p-4 max-h-[40vh] overflow-y-auto">
      <p
        v-if="fromMetadataOnly"
        class="mb-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2 py-1.5"
      >
        基于视频标题/描述生成（无完整字幕）
      </p>
      <p class="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">
        {{ text }}<span v-if="loading" class="inline-block w-0.5 h-4 ml-0.5 bg-text-secondary animate-pulse align-middle" />
      </p>
    </div>
  </div>
</template>
