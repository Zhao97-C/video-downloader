<script setup lang="ts">
const platforms = [
  { name: 'YouTube', icon: '▶️' },
  { name: 'TikTok', icon: '🎵' },
  { name: 'Instagram', icon: '📷' },
  { name: 'Twitter/X', icon: '🐦' },
  { name: 'Bilibili', icon: '📺' },
  { name: 'Vimeo', icon: '🎬' },
  { name: 'Reddit', icon: '🤖' },
  { name: 'Twitch', icon: '🎮' },
]
</script>

<template>
  <div class="w-full max-w-4xl mx-auto mb-16 text-center">
    <p class="text-text-secondary text-sm mb-4 uppercase tracking-widest">Supports 1000+ platforms</p>
    <div class="flex flex-wrap justify-center gap-3">
      <div
        v-for="platform in platforms"
        :key="platform.name"
        class="px-4 py-2 rounded-full bg-bg-card border border-border text-sm text-text-secondary hover:text-text-primary hover:border-brand-purple/50 transition-all cursor-default"
      >
        <span class="mr-1.5">{{ platform.icon }}</span>
        {{ platform.name }}
      </div>
    </div>
  </div>
</template>
