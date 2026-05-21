<script setup lang="ts">
import { ref } from 'vue'
import NavBar from '../components/NavBar.vue'
import HeroSection from '../components/HeroSection.vue'
import DownloadBox from '../components/DownloadBox.vue'
import PlatformShowcase from '../components/PlatformShowcase.vue'
import FeatureCards from '../components/FeatureCards.vue'
import ProBanner from '../components/ProBanner.vue'
import FooterSection from '../components/FooterSection.vue'
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <NavBar />
    <main class="flex-1 flex flex-col items-center justify-start px-4 pt-16 md:pt-24">
      <HeroSection />
      <DownloadBox />
      <PlatformShowcase />
      <FeatureCards />
      <ProBanner />
    </main>
    <FooterSection />
  </div>
</template>
