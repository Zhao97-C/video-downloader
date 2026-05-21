<script setup lang="ts">
import NavBar from './components/NavBar.vue'
</script>

<template>
  <div class="flex min-h-screen bg-bg-primary">
    <NavBar />
    <!-- offset for sidebar on desktop -->
    <div class="flex-1 md:pl-[220px] flex flex-col min-w-0">
      <router-view />
    </div>
  </div>
</template>
