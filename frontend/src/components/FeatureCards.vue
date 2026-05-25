<script setup lang="ts">
const features = [
  {
    title: 'Lightning Fast',
    desc: 'Direct link detection & smart routing for maximum download speed.',
    icon: '⚡',
  },
  {
    title: 'Highest Quality',
    desc: 'Up to 4K resolution with original audio. No re-encoding.',
    icon: '◈',
    pro: true,
  },
  {
    title: 'AI Summary',
    desc: 'Free: auto summaries in Chinese (3 videos/day). PRO: unlimited summaries, mind maps, Q&A, and translation.',
    icon: '◎',
  },
  {
    title: 'Batch Download',
    desc: 'Download entire playlists and channels in one go.',
    icon: '⊕',
    pro: true,
  },
]
</script>

<template>
  <div class="mb-20 md:mb-28">
    <h2 class="text-lg font-bold text-text-primary mb-6 md:mb-8">
      Why SaveAny?
    </h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div
        v-for="feature in features"
        :key="feature.title"
        class="p-6 rounded-2xl bg-bg-card border border-border card-hover"
      >
        <div class="flex items-start gap-4">
          <div class="w-9 h-9 rounded-xl bg-bg-input flex items-center justify-center flex-shrink-0 text-base leading-none">
            {{ feature.icon }}
          </div>
          <div class="flex-1 min-w-0 pt-0.5">
            <div class="flex items-center gap-2 mb-2">
              <h3 class="font-semibold text-text-primary text-sm">{{ feature.title }}</h3>
              <span v-if="feature.pro" class="pro-badge">PRO</span>
            </div>
            <p class="text-text-secondary text-sm leading-relaxed">{{ feature.desc }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
