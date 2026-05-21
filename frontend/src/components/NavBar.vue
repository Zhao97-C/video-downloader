<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const router = useRouter()
const route = useRoute()
const mobileOpen = ref(false)

store.fetchProfile()

function isActive(path: string) {
  return route.path === path
}
</script>

<template>
  <!-- ─── Desktop Sidebar ─── -->
  <aside class="hidden md:flex flex-col fixed inset-y-0 left-0 w-[220px] bg-bg-card border-r border-border z-40">
    <!-- Logo -->
    <div class="px-6 h-16 flex items-center border-b border-border flex-shrink-0">
      <router-link to="/" class="flex items-center gap-2.5">
        <div class="w-7 h-7 bg-accent rounded-md flex items-center justify-center flex-shrink-0">
          <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </div>
        <span class="text-base font-bold text-text-primary tracking-tight">SaveAny</span>
      </router-link>
    </div>

    <!-- Nav links -->
    <nav class="flex-1 px-3 py-5 flex flex-col gap-1 overflow-y-auto">
      <router-link
        to="/"
        :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
          isActive('/') ? 'bg-bg-input text-text-primary font-medium' : 'nav-link hover:bg-bg-primary']"
      >
        <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Download
      </router-link>

      <router-link
        to="/pricing"
        :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
          isActive('/pricing') ? 'bg-bg-input text-text-primary font-medium' : 'nav-link hover:bg-bg-primary']"
      >
        <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Pricing
      </router-link>
    </nav>

    <!-- Bottom auth section -->
    <div class="px-3 py-4 border-t border-border flex-shrink-0">
      <template v-if="store.isLoggedIn">
        <div class="px-3 py-2 mb-1">
          <div class="flex items-center gap-2 mb-1">
            <span v-if="store.user?.isPro" class="pro-badge">PRO</span>
            <span class="text-text-secondary text-xs truncate">{{ store.user?.email }}</span>
          </div>
        </div>
        <button
          @click="store.logout()"
          class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm nav-link hover:bg-bg-primary transition-colors"
        >
          <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Sign Out
        </button>
      </template>
      <template v-else>
        <router-link
          to="/auth"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm nav-link hover:bg-bg-primary transition-colors mb-1"
        >
          <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          Sign In
        </router-link>
        <router-link
          to="/pricing"
          class="accent-btn flex items-center justify-center gap-2 w-full px-3 py-2.5 rounded-lg text-sm font-medium"
        >
          Get PRO
        </router-link>
      </template>
    </div>
  </aside>

  <!-- ─── Mobile Top Bar ─── -->
  <header class="md:hidden fixed top-0 left-0 right-0 z-40 bg-bg-card border-b border-border h-14 flex items-center justify-between px-4">
    <router-link to="/" class="flex items-center gap-2">
      <div class="w-7 h-7 bg-accent rounded-md flex items-center justify-center">
        <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      </div>
      <span class="text-base font-bold text-text-primary tracking-tight">SaveAny</span>
    </router-link>

    <button @click="mobileOpen = !mobileOpen" class="p-2 text-text-secondary hover:text-text-primary transition-colors">
      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path v-if="!mobileOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </header>

  <!-- Mobile Menu Overlay -->
  <div
    v-if="mobileOpen"
    class="md:hidden fixed inset-0 z-30 bg-black/20 backdrop-blur-sm"
    @click="mobileOpen = false"
  />
  <div
    v-if="mobileOpen"
    class="md:hidden fixed top-14 left-0 right-0 z-40 bg-bg-card border-b border-border shadow-lg"
  >
    <nav class="px-4 py-3 flex flex-col gap-1">
      <router-link
        to="/"
        @click="mobileOpen = false"
        class="flex items-center gap-3 px-3 py-3 rounded-lg text-sm nav-link hover:bg-bg-primary"
      >
        Download
      </router-link>
      <router-link
        to="/pricing"
        @click="mobileOpen = false"
        class="flex items-center gap-3 px-3 py-3 rounded-lg text-sm nav-link hover:bg-bg-primary"
      >
        Pricing
      </router-link>

      <div class="border-t border-border my-2" />

      <template v-if="store.isLoggedIn">
        <span class="px-3 py-1.5 text-xs text-text-secondary truncate">{{ store.user?.email }}</span>
        <button @click="store.logout(); mobileOpen = false" class="flex items-center gap-3 px-3 py-3 rounded-lg text-sm nav-link hover:bg-bg-primary text-left">
          Sign Out
        </button>
      </template>
      <template v-else>
        <router-link to="/auth" @click="mobileOpen = false" class="flex items-center gap-3 px-3 py-3 rounded-lg text-sm nav-link hover:bg-bg-primary">
          Sign In
        </router-link>
        <router-link
          to="/pricing"
          @click="mobileOpen = false"
          class="accent-btn flex items-center justify-center px-3 py-3 rounded-lg text-sm font-medium mt-1"
        >
          Get PRO
        </router-link>
      </template>
    </nav>
  </div>
</template>
