<script setup lang="ts">
</script>

<template>
  <div class="mb-24 md:mb-32">
    <div class="rounded-2xl bg-accent p-8 sm:p-10 md:p-12 text-white">
      <div class="inline-block px-2.5 py-1 rounded-md bg-white/15 text-white text-xs font-semibold uppercase tracking-wider mb-5">
        Limited Offer
      </div>
      <h2 class="text-2xl md:text-3xl font-bold mb-3 leading-snug">
        Unlock unlimited downloads
      </h2>
      <p class="text-white/65 mb-8 leading-relaxed text-sm max-w-sm">
        4K quality, batch downloads, AI summaries, subtitle translation and zero limits.
        Starting at just <span class="text-white font-semibold">$9.9/month</span>.
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
