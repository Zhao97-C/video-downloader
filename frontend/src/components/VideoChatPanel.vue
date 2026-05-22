<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { chatStream } from '../api'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

const props = defineProps<{
  taskId: string
  title: string
  outputLanguage: string
  isPro: boolean
  isLoggedIn: boolean
}>()

const router = useRouter()
const expanded = ref(false)
const messages = ref<ChatMessage[]>([])
const input = ref('')
const loading = ref(false)
const error = ref('')
const fromMetadata = ref(false)
const questionsUsed = ref(0)
const maxQuestions = 10
let chatAbort: AbortController | null = null

const suggestions = [
  '视频主要讲了什么？',
  '有哪些关键步骤？',
  '结论或要点是什么？',
]

const questionsRemaining = computed(() =>
  Math.max(0, maxQuestions - questionsUsed.value),
)

const previewMessages = computed<ChatMessage[]>(() => {
  const t = props.title.replace(/\n/g, ' ').trim() || 'Video'
  return [
    { role: 'user', content: '这段视频的核心内容是什么？' },
    {
      role: 'assistant',
      content: `根据「${t}」的字幕与转录，核心内容包括：主题概述、关键论点与步骤，以及结尾的总结要点。（PRO 用户可基于真实字幕获得回答）`,
    },
    { role: 'user', content: '有没有提到具体的工具或方法？' },
    {
      role: 'assistant',
      content: '升级 PRO 后，可针对当前视频字幕进行多轮追问，答案仅依据视频内容生成。',
    },
  ]
})

const displayMessages = computed(() =>
  props.isPro ? messages.value : previewMessages.value,
)

function toggleExpanded() {
  expanded.value = !expanded.value
}

function promptLogin() {
  const go = confirm('Sign in to use Video Q&A.')
  if (go) router.push('/auth')
}

function applySuggestion(text: string) {
  if (!props.isPro) return
  input.value = text
}

async function handleSend() {
  if (!props.isLoggedIn) {
    promptLogin()
    return
  }
  if (!props.isPro) return

  const text = input.value.trim()
  if (!text || loading.value) return
  if (questionsRemaining.value <= 0) {
    error.value = `已达本视频 ${maxQuestions} 次提问上限，请重新解析链接后开始新会话。`
    return
  }

  chatAbort?.abort()
  chatAbort = new AbortController()
  loading.value = true
  error.value = ''
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  const assistantIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '' })

  try {
    await chatStream(
      props.taskId,
      text,
      props.outputLanguage,
      {
        onChunk: (chunk) => {
          messages.value[assistantIdx].content += chunk
        },
        onDone: (meta) => {
          fromMetadata.value = !!meta?.from_metadata_only
          if (typeof meta?.questions_used === 'number') {
            questionsUsed.value = meta.questions_used
          }
        },
        onError: (message) => {
          error.value = message
          if (!messages.value[assistantIdx].content) {
            messages.value.splice(assistantIdx, 1)
          }
        },
      },
      chatAbort.signal,
    )
  } catch (e: unknown) {
    if (e instanceof DOMException && e.name === 'AbortError') return
    const msg = e instanceof Error ? e.message : 'Failed to get answer'
    error.value = msg
    if (!messages.value[assistantIdx].content) {
      messages.value.splice(assistantIdx, 1)
      const last = messages.value[messages.value.length - 1]
      if (last?.role === 'user' && last.content === text) {
        messages.value.pop()
      }
    }
  } finally {
    loading.value = false
    chatAbort = null
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="mt-5 rounded-xl border border-border overflow-hidden">
    <button
      type="button"
      class="w-full flex items-center justify-between gap-2 px-4 py-3 bg-bg-input hover:bg-bg-secondary/80 transition-colors text-left"
      @click="toggleExpanded"
    >
      <span class="font-medium text-text-primary text-xs uppercase tracking-wider flex items-center gap-2">
        Video Q&A <span class="pro-badge">PRO</span>
      </span>
      <span class="text-text-secondary text-xs shrink-0">
        {{ expanded ? 'Collapse' : 'Expand' }}
        <span v-if="isPro && questionsUsed > 0" class="ml-1 text-text-muted">
          · {{ questionsUsed }}/{{ maxQuestions }}
        </span>
      </span>
    </button>

    <div v-show="expanded" class="border-t border-border p-4">
      <div
        v-if="fromMetadata && isPro && messages.length"
        class="mb-3 px-3 py-2 rounded-lg text-xs text-amber-700 bg-amber-50 border border-amber-200"
      >
        Based on limited metadata (no timed subtitles).
      </div>

      <div v-if="error" class="mb-3 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm">
        {{ error }}
      </div>

      <div class="relative rounded-xl border border-border overflow-hidden min-h-[200px]">
        <div
          class="p-3 max-h-[36vh] overflow-y-auto space-y-3"
          :class="{ 'blur-[6px] select-none pointer-events-none': !isPro }"
        >
          <div
            v-for="(msg, i) in displayMessages"
            :key="i"
            :class="[
              'text-sm leading-relaxed whitespace-pre-wrap rounded-xl px-3 py-2 max-w-[92%]',
              msg.role === 'user'
                ? 'ml-auto bg-gradient-to-r from-[#7c3aed]/15 to-[#3b82f6]/15 text-text-primary border border-border'
                : 'mr-auto bg-bg-input text-text-secondary border border-border',
            ]"
          >
            {{ msg.content }}
            <span
              v-if="isPro && loading && i === displayMessages.length - 1 && msg.role === 'assistant' && !msg.content"
              class="inline-block w-0.5 h-3.5 ml-0.5 bg-text-secondary animate-pulse align-middle"
            />
            <span
              v-else-if="isPro && loading && i === displayMessages.length - 1 && msg.role === 'assistant'"
              class="inline-block w-0.5 h-3.5 ml-0.5 bg-text-secondary animate-pulse align-middle"
            />
          </div>
        </div>

        <div
          v-if="!isPro"
          class="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-bg-card/55 backdrop-blur-[2px] px-6 text-center"
        >
          <p class="text-sm text-text-primary font-medium">Ask anything about this video</p>
          <p class="text-xs text-text-secondary max-w-sm">
            Multi-turn Q&A grounded in subtitles. Up to {{ maxQuestions }} questions per video.
          </p>
          <router-link
            to="/pricing"
            class="px-5 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-[#7c3aed] to-[#3b82f6] text-white shadow-sm hover:opacity-95 transition-opacity"
          >
            Upgrade to PRO
          </router-link>
        </div>
      </div>

      <div v-if="isPro" class="mt-3 flex flex-wrap gap-2">
        <button
          v-for="chip in suggestions"
          :key="chip"
          type="button"
          :disabled="loading || questionsRemaining <= 0"
          class="px-3 py-1.5 rounded-lg text-xs border border-border bg-bg-input hover:border-border-strong text-text-secondary transition-all disabled:opacity-50"
          @click="applySuggestion(chip)"
        >
          {{ chip }}
        </button>
      </div>

      <div v-if="isPro" class="mt-3 flex gap-2">
        <textarea
          v-model="input"
          :disabled="loading || questionsRemaining <= 0"
          rows="2"
          placeholder="Ask about this video..."
          class="flex-1 px-3 py-2 rounded-xl text-sm border border-border bg-bg-input text-text-primary resize-none disabled:opacity-50"
          @keydown="onKeydown"
        />
        <button
          type="button"
          :disabled="loading || !input.trim() || questionsRemaining <= 0"
          class="px-4 py-2 rounded-xl text-sm font-medium bg-gradient-to-r from-[#7c3aed] to-[#3b82f6] text-white shrink-0 self-end disabled:opacity-50 transition-opacity"
          @click="handleSend"
        >
          {{ loading ? '...' : 'Send' }}
        </button>
      </div>

      <p v-if="isPro" class="mt-2 text-xs text-text-muted">
        <template v-if="questionsRemaining > 0">
          {{ questionsRemaining }} question(s) left for this video.
        </template>
        <template v-else>
          Limit reached. Re-parse the URL for a new session.
        </template>
      </p>

      <button
        v-if="!isPro && !isLoggedIn"
        type="button"
        class="mt-3 w-full py-2 rounded-lg text-sm border border-border text-text-primary hover:border-border-strong transition-all"
        @click="promptLogin"
      >
        Sign in
      </button>
    </div>
  </div>
</template>
