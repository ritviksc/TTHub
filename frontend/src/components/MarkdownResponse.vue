<script setup>
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown.js'

const props = defineProps({ text: { type: String, default: '' } })
const rendered = computed(() => renderMarkdown(props.text))
</script>

<template>
  <!-- Only HTML produced by our configured Markdown renderer reaches v-html. -->
  <div class="markdown-response" v-html="rendered"></div>
</template>

<style scoped>
.markdown-response { color: var(--text-secondary); line-height: 1.6; overflow-wrap: anywhere; overflow-x: auto; }
.markdown-response :deep(h1),
.markdown-response :deep(h2),
.markdown-response :deep(h3),
.markdown-response :deep(h4),
.markdown-response :deep(h5),
.markdown-response :deep(h6) { color: var(--text); font-size: var(--text-lg); margin: 20px 0 10px; }
.markdown-response :deep(p) { margin: 10px 0; }
.markdown-response :deep(ul),
.markdown-response :deep(ol) { padding-left: 24px; margin: 12px 0; }
.markdown-response :deep(li) { margin: 6px 0; }
.markdown-response :deep(table) { border-collapse: collapse; width: 100%; margin: 16px 0; }
.markdown-response :deep(th),
.markdown-response :deep(td) { border: 1px solid var(--border); padding: 10px 12px; text-align: left; }
.markdown-response :deep(th) { background: var(--surface-sunken); color: var(--text); }
.markdown-response :deep(blockquote) { border-left: 3px solid var(--teal); padding-left: 16px; margin: 16px 0; }
.markdown-response :deep(pre) { overflow-x: auto; background: var(--surface-sunken); padding: 12px; border-radius: var(--radius-sm); }
.markdown-response :deep(code) { background: var(--surface-sunken); font-size: var(--text-sm); }
.markdown-response :deep(a) { color: var(--maroon); text-decoration: underline; }
.markdown-response :deep(hr) { border: 0; border-top: 1px solid var(--border); margin: 20px 0; }
</style>
