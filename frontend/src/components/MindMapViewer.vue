<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'

const props = withDefaults(
  defineProps<{
    markdown: string
    loading?: boolean
    interactive?: boolean
  }>(),
  {
    loading: false,
    interactive: true,
  },
)

const svgRef = ref<SVGSVGElement | null>(null)
let markmapInstance: { destroy: () => void; fit: () => void } | null = null
let renderToken = 0

async function renderMap() {
  const md = props.markdown.trim()
  if (!md || !svgRef.value) return

  const token = ++renderToken
  markmapInstance?.destroy()
  markmapInstance = null

  const [{ Transformer }, markmapView] = await Promise.all([
    import('markmap-lib'),
    import('markmap-view'),
  ])
  if (token !== renderToken) return

  const { Markmap } = markmapView
  const transformer = new Transformer()
  const { root, features } = transformer.transform(md)
  const { styles, scripts } = transformer.getUsedAssets(features)

  if (styles) await markmapView.loadCSS(styles)
  if (scripts) {
    await markmapView.loadJS(scripts, { getMarkmap: () => markmapView })
  }
  if (token !== renderToken) return

  const svg = svgRef.value
  svg.innerHTML = ''
  markmapInstance = Markmap.create(
    svg,
    {
      zoom: props.interactive,
      pan: props.interactive,
    },
    root,
  )
  await nextTick()
  markmapInstance?.fit()
}

function handleFit() {
  markmapInstance?.fit()
}

defineExpose({ fit: handleFit })

watch(
  () => props.markdown,
  () => {
    if (!props.loading) void renderMap()
  },
)

watch(
  () => props.loading,
  (loading) => {
    if (!loading && props.markdown) void renderMap()
  },
)

onMounted(() => {
  if (props.markdown && !props.loading) void renderMap()
})

onUnmounted(() => {
  renderToken++
  markmapInstance?.destroy()
  markmapInstance = null
})
</script>

<template>
  <div class="relative w-full h-full min-h-[280px] bg-bg-input rounded-xl overflow-hidden">
    <svg
      ref="svgRef"
      class="w-full h-full min-h-[280px] block"
      :class="{ 'pointer-events-none': !interactive }"
    />
    <div
      v-if="loading"
      class="absolute inset-0 flex items-center justify-center bg-bg-card/70 text-sm text-text-secondary"
    >
      Generating mind map...
    </div>
    <button
      v-if="interactive && !loading && markdown"
      type="button"
      class="absolute bottom-3 right-3 px-3 py-1.5 rounded-lg text-xs border border-border bg-bg-card/90 text-text-primary hover:border-border-strong transition-all"
      @click="handleFit"
    >
      Fit view
    </button>
  </div>
</template>
