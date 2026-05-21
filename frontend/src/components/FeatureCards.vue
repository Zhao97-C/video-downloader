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
    desc: 'Get instant AI-powered video summaries and subtitle translations.',
    icon: '◎',
    pro: true,
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
  <div class="w-full max-w-2xl mx-auto mb-24 md:mb-32">
    <h2 class="text-xl font-bold text-text-primary mb-8 md:mb-10">
      Why SaveAny?
    </h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div
        v-for="feature in features"
        :key="feature.title"
        class="p-6 rounded-xl bg-bg-card border border-border card-hover"
      >
        <div class="flex items-start gap-4">
          <div class="w-9 h-9 rounded-lg bg-bg-input flex items-center justify-center flex-shrink-0 font-mono text-text-secondary">
            {{ feature.icon }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1.5">
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
