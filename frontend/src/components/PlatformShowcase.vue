<script setup lang="ts">
const platforms = [
  { name: 'YouTube' },
  { name: 'TikTok' },
  { name: 'Instagram' },
  { name: 'Twitter / X' },
  { name: 'Bilibili' },
  { name: 'Vimeo' },
  { name: 'Reddit' },
  { name: 'Twitch' },
]
</script>

<template>
  <div class="mb-20 md:mb-28">
    <p class="text-text-muted text-xs uppercase tracking-widest text-center mb-5">
      1000+ supported platforms
    </p>
    <div class="flex flex-wrap justify-center gap-2">
      <span
        v-for="platform in platforms"
        :key="platform.name"
        class="px-4 py-2 rounded-full bg-bg-card border border-border text-sm text-text-secondary hover:border-border-strong hover:text-text-primary transition-all cursor-default"
      >
        {{ platform.name }}
      </span>
    </div>
  </div>
</template>
