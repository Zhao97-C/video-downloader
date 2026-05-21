<script setup lang="ts">
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
  <div class="flex flex-col min-h-screen">
    <main class="flex-1 flex flex-col items-center px-4 sm:px-8 pt-24 md:pt-16 pb-20">
      <div class="w-full max-w-5xl">
        <div class="text-center mb-14 md:mb-16">
          <h1 class="text-3xl md:text-4xl font-bold mb-3 text-text-primary tracking-tight">
            Simple Pricing
          </h1>
          <p class="text-text-secondary text-base max-w-md mx-auto leading-relaxed">
            Start free, upgrade when you need more power.
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div
            v-for="plan in plans"
            :key="plan.name"
            :class="[
              'rounded-2xl p-8 border flex flex-col relative',
              plan.highlighted
                ? 'bg-accent text-white border-accent'
                : 'bg-bg-card border-border card-hover'
            ]"
          >
            <div
              v-if="plan.badge"
              class="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-pro text-white text-xs font-bold whitespace-nowrap"
            >
              {{ plan.badge }}
            </div>

            <h3 :class="['text-base font-semibold mb-3', plan.highlighted ? 'text-white' : 'text-text-primary']">
              {{ plan.name }}
            </h3>
            <div class="mb-7">
              <span :class="['text-4xl font-bold', plan.highlighted ? 'text-white' : 'text-text-primary']">
                {{ plan.price }}
              </span>
              <span :class="['text-sm ml-1', plan.highlighted ? 'text-white/60' : 'text-text-secondary']">
                {{ plan.period }}
              </span>
            </div>

            <ul class="flex-1 space-y-3.5 mb-9">
              <li
                v-for="feature in plan.features"
                :key="feature"
                :class="['flex items-start gap-2.5 text-sm', plan.highlighted ? 'text-white/80' : 'text-text-secondary']"
              >
                <svg
                  :class="['w-4 h-4 flex-shrink-0 mt-0.5', plan.highlighted ? 'text-white' : 'text-accent']"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                </svg>
                {{ feature }}
              </li>
            </ul>

            <button
              :class="[
                'w-full py-3 rounded-xl font-medium text-sm transition-all',
                plan.highlighted
                  ? 'bg-white text-accent hover:bg-gray-100'
                  : 'accent-btn'
              ]"
            >
              {{ plan.cta }}
            </button>
          </div>
        </div>
      </div>
    </main>
    <FooterSection />
  </div>
</template>
