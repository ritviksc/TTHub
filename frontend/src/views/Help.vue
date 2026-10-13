<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listHelpArticles } from '@/apis.js'
import HelpExplorer from '@/components/help/HelpExplorer.vue'
import HelpChat from '@/components/help/HelpChat.vue'

// The backend decides which articles each role may read; this page shows them.
const articles = ref([])
const loading = ref(true)
const error = ref('')

const route = useRoute()
const router = useRouter()
// The open article lives in ?article=, so refresh, Back and the chat's source chips work.
const slug = computed(() => (typeof route.query.article === 'string' ? route.query.article : null))

onMounted(async () => {
  try {
    articles.value = await listHelpArticles()
  } catch {
    error.value = 'Could not load the help articles. Please refresh the page.'
  } finally {
    loading.value = false
  }
})

function open(next) {
  if (next !== slug.value) router.push({ query: { article: next } })
}

function close() {
  router.push({ query: {} })
}
</script>

<template>
  <div class="dash-page">
    <main class="content help-page">
      <h1>Help</h1>
      <p class="page-subtitle">Browse the documentation for your role, or ask the help assistant.</p>

      <div class="help-layout">
        <HelpExplorer :articles="articles" :loading="loading" :error="error" :slug="slug"
                      @open="open" @close="close" />
        <HelpChat @open="open" />
      </div>
    </main>
  </div>
</template>

<style scoped>
.help-page { max-width: 1280px; padding-bottom: 24px; }
/* Two equal halves that fill the window, each scrolling inside itself so the
   chat box stays in view. 226px is the nav, page padding, heading and subtitle. */
.help-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 20px;
  height: calc(100vh - 226px);
  min-height: 540px;
}
.help-layout > :deep(.help-panel) {
  display: flex; flex-direction: column; min-height: 0;
  background: var(--surface); border-radius: var(--radius-lg); box-shadow: var(--shadow-card);
  border: 1px solid var(--border); overflow: hidden;
}

@media (max-width: 900px) {
  .help-layout { grid-template-columns: minmax(0, 1fr); height: auto; }
  .help-layout > :deep(.help-panel) { height: 70vh; min-height: 460px; }
}
</style>
