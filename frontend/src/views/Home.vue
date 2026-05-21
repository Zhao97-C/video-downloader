<script setup lang="ts">
import HeroSection from '../components/HeroSection.vue'
import DownloadBox from '../components/DownloadBox.vue'
import PlatformShowcase from '../components/PlatformShowcase.vue'
import FeatureCards from '../components/FeatureCards.vue'
import ProBanner from '../components/ProBanner.vue'
import FooterSection from '../components/FooterSection.vue'
</script>

<template>
  <div class="flex flex-col min-h-screen">
    <main class="flex-1 flex flex-col items-center px-4 sm:px-8 pt-24 md:pt-20">
      <HeroSection />
      <DownloadBox />
      <PlatformShowcase />
      <FeatureCards />
      <ProBanner />
    </main>
    <FooterSection />
  </div>
</template>
