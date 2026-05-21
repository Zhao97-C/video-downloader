<script setup lang="ts">
const platforms = [
  { name: 'YouTube', icon: '▶' },
  { name: 'TikTok', icon: '♪' },
  { name: 'Instagram', icon: '◉' },
  { name: 'Twitter / X', icon: '✕' },
  { name: 'Bilibili', icon: '⊕' },
  { name: 'Vimeo', icon: '◈' },
  { name: 'Reddit', icon: '⊗' },
  { name: 'Twitch', icon: '▸' },
]
</script>

<template>
  <div class="w-full max-w-2xl mx-auto mb-24 md:mb-32 text-center">
    <p class="text-text-muted text-xs uppercase tracking-widest mb-5">1000+ supported platforms</p>
    <div class="flex flex-wrap justify-center gap-2 sm:gap-2.5">
      <span
        v-for="platform in platforms"
        :key="platform.name"
        class="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-bg-card border border-border text-sm text-text-secondary hover:border-border-strong hover:text-text-primary transition-all cursor-default"
      >
        <span class="font-mono text-xs text-text-muted">{{ platform.icon }}</span>
        {{ platform.name }}
      </span>
    </div>
  </div>
</template>
