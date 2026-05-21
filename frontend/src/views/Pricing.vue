<script setup lang="ts">
import NavBar from '../components/NavBar.vue'
import FooterSection from '../components/FooterSection.vue'

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    features: [
      '3 downloads per day',
      'Up to 720p quality',
      'Single video only',
      'Standard speed',
    ],
    cta: 'Current Plan',
    highlighted: false,
  },
  {
    name: 'PRO Monthly',
    price: '$9.9',
    period: '/month',
    features: [
      'Unlimited downloads',
      'Up to 4K quality',
      'Batch & playlist downloads',
      'AI video summaries',
      'Subtitle translation',
      'Priority processing',
    ],
    cta: 'Get PRO',
    highlighted: true,
  },
  {
    name: 'PRO Yearly',
    price: '$99',
    period: '/year',
    badge: 'Save 17%',
    features: [
      'Everything in Monthly',
      'Up to 4K quality',
      'Batch & playlist downloads',
      'AI video summaries',
      'Subtitle translation',
      'Priority processing',
    ],
    cta: 'Get PRO Yearly',
    highlighted: false,
  },
]
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <NavBar />
    <main class="flex-1 flex flex-col items-center justify-start px-4 pt-24 pb-16">
      <h1 class="text-3xl md:text-5xl font-bold mb-3 text-center">
        Simple <span class="gradient-text">Pricing</span>
      </h1>
      <p class="text-text-secondary text-lg mb-12 text-center max-w-lg">
        Start free, upgrade when you need more power.
      </p>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full">
        <div
          v-for="plan in plans"
          :key="plan.name"
          :class="[
            'rounded-2xl p-8 border flex flex-col',
            plan.highlighted
              ? 'bg-bg-card border-brand-purple/50 glow relative'
              : 'bg-bg-secondary border-border'
          ]"
        >
          <div v-if="plan.badge" class="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-brand-purple text-white text-xs font-bold">
            {{ plan.badge }}
          </div>
          <h3 class="text-lg font-semibold mb-2">{{ plan.name }}</h3>
          <div class="mb-6">
            <span class="text-4xl font-bold">{{ plan.price }}</span>
            <span class="text-text-secondary text-sm">{{ plan.period }}</span>
          </div>
          <ul class="flex-1 space-y-3 mb-8">
            <li v-for="feature in plan.features" :key="feature" class="flex items-center gap-2 text-sm text-text-secondary">
              <svg class="w-4 h-4 text-brand-purple flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              {{ feature }}
            </li>
          </ul>
          <button
            :class="[
              'w-full py-3 rounded-xl font-medium text-sm transition-all',
              plan.highlighted
                ? 'gradient-btn text-white'
                : 'bg-bg-card border border-border text-text-primary hover:border-brand-purple/50'
            ]"
          >
            {{ plan.cta }}
          </button>
        </div>
      </div>
    </main>
    <FooterSection />
  </div>
</template>
