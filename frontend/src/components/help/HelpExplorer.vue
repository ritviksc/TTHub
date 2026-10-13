<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { getHelpArticle } from '@/apis.js'
import { buildHelpTree, siblings } from '@/utils/help.js'
import MarkdownResponse from '@/components/MarkdownResponse.vue'
import HelpTree from './HelpTree.vue'

// The left half of the Help page: a file-explorer tree of the articles this
// role may read, which turns into a reader when an article is opened.
const props = defineProps({
  articles: { type: Array, required: true },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  slug: { type: String, default: null },
})
const emit = defineEmits(['open', 'close'])

const query = ref('')
const tree = computed(() => buildHelpTree(props.articles))
// Every folder starts collapsed; the user opens the ones they need.
const expanded = ref(new Set())

function toggle(id) {
  const next = new Set(expanded.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expanded.value = next
}

/* ---- reader ---- */
const article = ref(null)
const articleError = ref('')
const loadingArticle = ref(false)
const reader = ref(null)
const listing = computed(() => props.articles.find(item => item.slug === props.slug))
const around = computed(() => siblings(props.articles, props.slug))

let requestId = 0
watch(() => props.slug, async slug => {
  const id = ++requestId
  articleError.value = ''
  if (!slug) { article.value = null; return }
  loadingArticle.value = true
  try {
    const data = await getHelpArticle(slug)
    if (id !== requestId) return
    article.value = data
    await nextTick()
    reader.value?.scrollTo({ top: 0 })
  } catch (error) {
    if (id !== requestId) return
    article.value = null
    articleError.value = error.response?.status === 404
      ? 'That help article is not available for your role.'
      : 'Could not load this article. Please try again.'
  } finally {
    if (id === requestId) loadingArticle.value = false
  }
}, { immediate: true })
</script>

<template>
  <section class="help-panel explorer" aria-label="Help articles">
    <template v-if="slug">
      <header class="panel-head reader-head">
        <button type="button" class="back-button" @click="emit('close')">← All articles</button>
        <nav v-if="listing" class="crumbs" aria-label="Breadcrumb">
          <span>{{ listing.audience_label }}</span><span aria-hidden="true">›</span><span>{{ listing.section }}</span>
        </nav>
      </header>
      <div ref="reader" class="panel-body reader" aria-live="polite">
        <p v-if="articleError" class="form-error" role="alert">{{ articleError }}</p>
        <article v-else-if="article" :class="{ stale: loadingArticle }">
          <h2>{{ article.title }}</h2>
          <MarkdownResponse :text="article.body" />
        </article>
        <p v-else class="loading-note">Loading…</p>
      </div>
      <footer v-if="around.previous || around.next" class="panel-foot pager">
        <button v-if="around.previous" type="button" class="pager-link" @click="emit('open', around.previous.slug)">
          <small>Previous</small>‹ {{ around.previous.title }}
        </button>
        <span v-else></span>
        <button v-if="around.next" type="button" class="pager-link next" @click="emit('open', around.next.slug)">
          <small>Next</small>{{ around.next.title }} ›
        </button>
      </footer>
    </template>

    <template v-else>
      <header class="panel-head">
        <h2>Documentation</h2>
        <input v-model="query" type="search" class="search" placeholder="Search articles"
               aria-label="Search help articles by title" />
      </header>
      <div class="panel-body">
        <p v-if="loading" class="loading-note">Loading…</p>
        <p v-else-if="error" class="form-error" role="alert">{{ error }}</p>
        <HelpTree v-else :tree="tree" :expanded="expanded" :query="query"
                  @toggle="toggle" @open="slug => emit('open', slug)" />
      </div>
    </template>
  </section>
</template>

<style scoped>
.panel-head { display: flex; flex-direction: column; gap: 10px; padding: 16px 20px 12px; border-bottom: 1px solid var(--border); }
.panel-head h2 { margin: 0; font-size: var(--text-lg); }
.reader-head { flex-direction: row; align-items: center; gap: 12px; flex-wrap: wrap; }
.search {
  border: 1px solid var(--border-strong); border-radius: var(--radius); font: inherit;
  padding: 8px 10px; width: 100%; box-sizing: border-box; background: var(--surface);
}
.search:focus { outline: 2px solid var(--teal); outline-offset: -1px; }
.panel-body { flex: 1; min-height: 0; overflow-y: auto; padding: 12px 16px; }
.reader { padding: 20px 24px; }
.reader h2 { margin: 0 0 4px; font-size: var(--text-xl); }
.reader :deep(.markdown-response) { font-size: var(--text-base); }
.reader .stale { opacity: 0.5; }
.back-button {
  background: none; border: 1px solid var(--border-strong); border-radius: var(--radius-pill);
  color: var(--text); cursor: pointer; font: inherit; font-size: var(--text-sm); padding: 4px 12px;
}
.back-button:hover { background: var(--surface-sunken); }
.crumbs { display: flex; gap: 6px; color: var(--text-muted); font-size: var(--text-sm); }
.pager { display: flex; justify-content: space-between; gap: 12px; padding: 12px 20px; border-top: 1px solid var(--border); }
.pager-link {
  display: flex; flex-direction: column; align-items: flex-start; max-width: 48%;
  background: none; border: none; cursor: pointer; color: var(--teal-dark); font: inherit; font-size: var(--text-base); text-align: left;
}
.pager-link.next { align-items: flex-end; text-align: right; }
.pager-link small { color: var(--text-muted); font-size: var(--text-xs); }
.pager-link:hover { text-decoration: underline; }
</style>
