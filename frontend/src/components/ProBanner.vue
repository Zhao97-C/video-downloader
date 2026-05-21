<script setup lang="ts">
</script>

<template>
  <div class="w-full max-w-3xl mx-auto mb-16">
    <div class="relative overflow-hidden rounded-2xl p-8 md:p-12 bg-gradient-to-br from-brand-purple/20 via-bg-card to-brand-blue/20 border border-brand-purple/30">
      <div class="absolute top-0 right-0 w-64 h-64 bg-brand-purple/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
      <div class="absolute bottom-0 left-0 w-48 h-48 bg-brand-blue/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2"></div>

      <div class="relative z-10 text-center">
        <div class="inline-block px-3 py-1 rounded-full bg-brand-purple/20 text-brand-purple text-xs font-bold uppercase tracking-wider mb-4">
          Limited Offer
        </div>
        <h2 class="text-2xl md:text-3xl font-bold mb-3">
          Unlock <span class="gradient-text">Unlimited Downloads</span>
        </h2>
        <p class="text-text-secondary mb-6 max-w-lg mx-auto">
          Get 4K quality, batch downloads, AI summaries, subtitle translation and zero limits.
          Starting at just <span class="text-text-primary font-semibold">$9.9/month</span>.
        </p>
        <div class="flex flex-col sm:flex-row items-center justify-center gap-3">
          <router-link
            to="/pricing"
            class="gradient-btn text-white px-8 py-3 rounded-xl font-semibold text-base animate-pulse-glow"
          >
            Upgrade to PRO →
          </router-link>
          <span class="text-text-secondary text-sm">Cancel anytime · 7-day money back</span>
        </div>
      </div>
    </div>
  </div>
</template>
