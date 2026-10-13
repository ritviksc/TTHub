<script setup>
import { computed } from 'vue'
import { treeRows } from '@/utils/help.js'

// Audience folders › section folders › articles, drawn as a flat list of rows
// like the Documents folder tree (components/documents/FolderTree.vue).
const props = defineProps({
  tree: { type: Array, required: true },
  expanded: { type: Set, required: true },
  query: { type: String, default: '' },
})
const emit = defineEmits(['toggle', 'open'])

const rows = computed(() => treeRows(props.tree, props.expanded, props.query))
const indent = depth => ({ paddingLeft: `${depth * 18}px` })
const searching = computed(() => props.query.trim().length > 0)
</script>

<template>
  <ul v-if="rows.length" class="help-tree" role="tree" aria-label="Help articles">
    <li v-for="row in rows" :key="row.node.id" role="treeitem"
        :aria-expanded="row.node.kind === 'article' ? undefined : row.open"
        :aria-level="row.depth + 1">
      <div class="tree-row" :class="row.node.kind" :style="indent(row.depth)">
        <template v-if="row.node.kind === 'article'">
          <span class="twisty" aria-hidden="true"></span>
          <button type="button" class="tree-label" @click="emit('open', row.node.slug)">
            <span class="icon" aria-hidden="true">📄</span>{{ row.node.label }}
          </button>
        </template>
        <button v-else type="button" class="tree-label folder" :disabled="searching"
                :aria-label="`${row.open ? 'Collapse' : 'Expand'} ${row.node.label}`"
                @click="emit('toggle', row.node.id)">
          <span class="twisty" aria-hidden="true">{{ row.open ? '▾' : '▸' }}</span>
          <span class="icon" aria-hidden="true">{{ row.open ? '📂' : '📁' }}</span>{{ row.node.label }}
        </button>
      </div>
    </li>
  </ul>
  <p v-else class="tree-empty">{{ searching ? 'No articles match your search.' : 'No help articles yet.' }}</p>
</template>

<style scoped>
.help-tree { list-style: none; margin: 0; padding: 0; }
.tree-row { display: flex; align-items: center; border-radius: var(--radius-sm); }
.tree-row:hover { background: var(--surface-sunken); }
.twisty {
  flex: 0 0 20px; display: inline-flex; justify-content: center;
  font-size: var(--text-sm); color: var(--text-muted);
}
.tree-label {
  flex: 1; min-width: 0; display: flex; align-items: center; gap: 6px;
  background: none; border: none; cursor: pointer; padding: 7px 8px 7px 0;
  font: inherit; font-size: var(--text-base); color: var(--text); text-align: left;
}
.tree-label:disabled { cursor: default; }
.tree-label:focus-visible { outline: 2px solid var(--teal); outline-offset: -2px; border-radius: var(--radius-sm); }
.tree-label.folder { padding-left: 0; }
.tree-row.audience .tree-label { font-weight: 600; }
.tree-row.section .tree-label { color: var(--text-secondary); }
.tree-row.article .tree-label { color: var(--text-secondary); }
.tree-row.article:hover .tree-label { color: var(--teal-dark); }
.icon { flex: 0 0 auto; }
.tree-empty { color: var(--text-muted); font-size: var(--text-sm); padding: 8px; }
</style>
