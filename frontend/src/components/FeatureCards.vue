<script setup lang="ts">
const features = [
  {
    title: 'Lightning Fast',
    desc: 'Direct link detection & smart routing for maximum speed',
    icon: '⚡',
  },
  {
    title: 'Highest Quality',
    desc: 'Up to 4K resolution with original audio quality',
    icon: '💎',
    pro: true,
  },
  {
    title: 'AI Summary',
    desc: 'Get instant AI-powered video summaries & translations',
    icon: '🧠',
    pro: true,
  },
  {
    title: 'Batch Download',
    desc: 'Download entire playlists and channels at once',
    icon: '📦',
    pro: true,
  },
]
</script>

<template>
  <div class="w-full max-w-4xl mx-auto mb-16">
    <h2 class="text-2xl md:text-3xl font-bold text-center mb-8">
      Why <span class="gradient-text">SaveAny</span>?
    </h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="feature in features"
        :key="feature.title"
        class="p-6 rounded-xl bg-bg-card border border-border hover:border-brand-purple/40 transition-all group"
      >
        <div class="flex items-start gap-4">
          <div class="text-2xl">{{ feature.icon }}</div>
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <h3 class="font-semibold text-text-primary">{{ feature.title }}</h3>
              <span
                v-if="feature.pro"
                class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-brand-purple/20 text-brand-purple uppercase"
              >
                PRO
              </span>
            </div>
            <p class="text-text-secondary text-sm leading-relaxed">{{ feature.desc }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
