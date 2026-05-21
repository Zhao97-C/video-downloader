<script setup lang="ts">
import { ref } from 'vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const menuOpen = ref(false)

store.fetchProfile()
</script>

<template>
  <nav class="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-bg-primary/80 border-b border-border">
    <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
      <router-link to="/" class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg gradient-btn flex items-center justify-center">
          <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </div>
        <span class="text-xl font-bold gradient-text">SaveAny</span>
      </router-link>

      <div class="hidden md:flex items-center gap-6">
        <router-link to="/" class="text-text-secondary hover:text-text-primary transition-colors text-sm">Home</router-link>
        <router-link to="/pricing" class="text-text-secondary hover:text-text-primary transition-colors text-sm">Pricing</router-link>

        <template v-if="store.isLoggedIn">
          <div class="flex items-center gap-2">
            <span v-if="store.user?.isPro" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-brand-purple/20 text-brand-purple">PRO</span>
            <span class="text-text-secondary text-sm">{{ store.user?.email }}</span>
            <button @click="store.logout()" class="text-text-secondary hover:text-text-primary text-sm ml-2">Logout</button>
          </div>
        </template>
        <template v-else>
          <router-link to="/auth" class="text-text-secondary hover:text-text-primary transition-colors text-sm">Sign In</router-link>
          <router-link to="/pricing" class="gradient-btn text-white px-4 py-2 rounded-lg text-sm font-medium">
            Get PRO
          </router-link>
        </template>
      </div>

      <button @click="menuOpen = !menuOpen" class="md:hidden text-text-secondary">
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path v-if="!menuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <div v-if="menuOpen" class="md:hidden border-t border-border bg-bg-primary/95 backdrop-blur-xl">
      <div class="px-4 py-4 flex flex-col gap-3">
        <router-link to="/" class="text-text-secondary hover:text-text-primary transition-colors" @click="menuOpen = false">Home</router-link>
        <router-link to="/pricing" class="text-text-secondary hover:text-text-primary transition-colors" @click="menuOpen = false">Pricing</router-link>
        <template v-if="store.isLoggedIn">
          <span class="text-text-secondary text-sm">{{ store.user?.email }}</span>
          <button @click="store.logout(); menuOpen = false" class="text-left text-text-secondary hover:text-text-primary">Logout</button>
        </template>
        <template v-else>
          <router-link to="/auth" class="text-text-secondary hover:text-text-primary transition-colors" @click="menuOpen = false">Sign In</router-link>
          <router-link to="/pricing" class="gradient-btn text-white px-4 py-2 rounded-lg text-sm font-medium text-center" @click="menuOpen = false">
            Get PRO
          </router-link>
        </template>
      </div>
    </div>
  </nav>
</template>
