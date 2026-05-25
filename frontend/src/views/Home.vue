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
    <main class="flex-1 pt-24 md:pt-16">
      <!-- Single centered column – mx-auto handles centering correctly
           inside the sidebar-offset content area -->
      <div class="page-content">
        <HeroSection />
        <DownloadBox />
        <PlatformShowcase />
        <FeatureCards />
        <ProBanner />
      </div>
    </main>
    <FooterSection />
  </div>
</template>
