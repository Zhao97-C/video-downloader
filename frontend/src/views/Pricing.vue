<script setup lang="ts">
import { computed } from 'vue'
import FooterSection from '../components/FooterSection.vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()

const plans = computed(() => {
  const cfg = store.siteConfig
  return [
    {
      id: 'free',
      name: 'Free',
      price: '$0',
      period: 'forever',
      features: [
        `${cfg.free_daily_limit} downloads per day`,
        `Up to ${cfg.free_max_resolution}p quality`,
        'Single video only',
        'Standard speed',
      ],
      cta: 'Current Plan',
      highlighted: false,
      badge: null,
    },
    {
      id: 'monthly',
      name: 'PRO Monthly',
      price: cfg.pro_monthly_price,
      period: cfg.pro_monthly_period,
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
      badge: null,
    },
    {
      id: 'yearly',
      name: 'PRO Yearly',
      price: cfg.pro_yearly_price,
      period: cfg.pro_yearly_period,
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
      badge: cfg.pro_yearly_savings,
    },
  ]
})

async function handleCheckout(planId: string) {
  if (planId === 'free') return
  if (!store.siteConfig.payment_enabled) {
    alert('Payment is not configured yet.')
    return
  }
  if (!store.isLoggedIn) {
    alert('Please sign in first.')
    return
  }
  try {
    const { createCheckout } = await import('../api')
    const { checkout_url } = await createCheckout(planId)
    window.location.href = checkout_url
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Failed to start checkout.')
  }
}
</script>

<template>
  <div class="flex flex-col min-h-screen">
    <main class="flex-1 pt-24 md:pt-16 pb-20">
      <div class="max-w-4xl mx-auto px-6 sm:px-10">
        <div class="text-center pt-8 md:pt-12 mb-14 md:mb-16">
          <h1 class="text-3xl md:text-4xl font-bold mb-4 text-text-primary tracking-tight">
            Simple Pricing
          </h1>
          <p class="text-text-secondary text-base leading-relaxed">
            Start free, upgrade when you need more power.
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-5 md:gap-6">
          <div
            v-for="plan in plans"
            :key="plan.id"
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
            <div class="mb-8">
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
                :class="['flex items-start gap-3 text-sm', plan.highlighted ? 'text-white/80' : 'text-text-secondary']"
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
              @click="handleCheckout(plan.id)"
              :disabled="plan.id === 'free'"
              :class="[
                'w-full py-3 rounded-xl font-medium text-sm transition-all disabled:cursor-default',
                plan.highlighted
                  ? 'bg-white text-accent hover:bg-gray-100'
                  : plan.id === 'free'
                    ? 'bg-bg-input border border-border text-text-secondary'
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
