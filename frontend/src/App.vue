<script setup lang="ts">
import NavBar from './components/NavBar.vue'
</script>

<template>
  <div class="flex min-h-screen bg-bg-primary">
    <NavBar />
    <!-- sidebar-offset: plain CSS @media rule to shift content right on md+ -->
    <div class="flex-1 min-w-0 overflow-x-hidden sidebar-offset">
      <router-view />
    </div>
  </div>
</template>
