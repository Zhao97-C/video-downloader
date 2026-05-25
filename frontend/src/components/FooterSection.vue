<script setup lang="ts">
</script>

<template>
  <footer class="border-t border-border py-8 px-6 sm:px-8">
    <div class="page-content flex flex-col sm:flex-row items-center justify-between gap-4">
      <div class="flex items-center gap-2">
        <div class="w-5 h-5 bg-accent rounded flex items-center justify-center">
          <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
        </div>
        <span class="text-sm font-semibold text-text-primary">SaveAny</span>
      </div>
      <p class="text-text-muted text-xs text-center">
        &copy; 2026 SaveAny · For personal use only · Respect creators' rights.
      </p>
      <div class="flex items-center gap-4 text-text-secondary text-xs">
        <a href="#" class="hover:text-text-primary transition-colors">Terms</a>
        <a href="#" class="hover:text-text-primary transition-colors">Privacy</a>
        <a href="#" class="hover:text-text-primary transition-colors">Contact</a>
      </div>
    </div>
  </footer>
</template>
