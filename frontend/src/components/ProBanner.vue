<script setup lang="ts">
import { useAppStore } from '../stores/app'
const store = useAppStore()
</script>

<template>
  <div class="mb-24 md:mb-32">
    <div class="rounded-2xl bg-accent p-8 sm:p-10 md:p-12 text-white">
      <div class="inline-block px-2.5 py-1 rounded-md bg-white/15 text-white text-xs font-semibold uppercase tracking-wider mb-5">
        Limited Offer
      </div>
      <h2 class="text-2xl md:text-3xl font-bold mb-3 leading-snug">
        Unlock PRO power tools
      </h2>
      <p class="text-white/65 mb-8 leading-relaxed text-sm max-w-sm">
        4K quality, batch downloads, unlimited AI summaries, mind maps, Q&A, and subtitle translation.
        Starting at just
        <span class="text-white font-semibold">
          {{ store.siteConfig.pro_monthly_price }}{{ store.siteConfig.pro_monthly_period }}
        </span>.
      </p>
      <div class="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <router-link
          to="/pricing"
          class="inline-flex items-center gap-2 bg-white text-accent px-7 py-3 rounded-xl font-semibold text-sm hover:bg-gray-100 transition-colors"
        >
          Upgrade to PRO →
        </router-link>
        <span class="text-white/45 text-xs">Cancel anytime · 7-day money back</span>
      </div>
    </div>
  </div>
</template>
