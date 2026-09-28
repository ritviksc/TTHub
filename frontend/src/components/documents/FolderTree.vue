<script setup>
import { ref, computed, watch } from 'vue'
import { childrenOf, folderTrail } from '@/utils/documents.js'

// An expandable folder tree over one scope's flat folder list. Used by the
// explorer sidebar and by the move dialog. With `rootLabel` set, a root row is
// shown above the folders so "move to the top level" can be picked.
const props = defineProps({
  folders: { type: Array, required: true },
  selectedId: { type: String, default: null },
  rootLabel: { type: String, default: '' },
  // Folders hidden from the tree, e.g. a folder and its subfolders when moving it.
  excluded: { type: Set, default: () => new Set() },
})
const emit = defineEmits(['select'])

const expanded = ref(new Set())

// Keep the selected folder visible by opening every folder above it.
watch(() => [props.selectedId, props.folders], () => {
  for (const folder of folderTrail(props.folders, props.selectedId).slice(0, -1)) {
    expanded.value.add(folder.id)
  }
}, { immediate: true })

function toggle(id) {
  if (expanded.value.has(id)) expanded.value.delete(id)
  else expanded.value.add(id)
}

// The tree flattened into the rows currently visible, with their depth, so it
// renders as a plain list rather than recursive components.
const rows = computed(() => {
  const visible = props.folders.filter(f => !props.excluded.has(f.id))
  const out = []
  function walk(parentId, depth) {
    for (const folder of childrenOf(visible, parentId)) {
      const hasChildren = visible.some(f => f.parent === folder.id)
      out.push({ folder, depth, hasChildren })
      if (hasChildren && expanded.value.has(folder.id)) walk(folder.id, depth + 1)
    }
  }
  walk(null, props.rootLabel ? 1 : 0)
  return out
})

const indent = depth => ({ paddingLeft: `${depth * 16}px` })
</script>

<template>
  <ul class="folder-tree" role="tree">
    <li v-if="rootLabel" role="treeitem" :aria-selected="selectedId === null">
      <div class="tree-row" :class="{ selected: selectedId === null }">
        <span class="twisty" aria-hidden="true"></span>
        <button type="button" class="tree-label" @click="emit('select', null)">
          <span aria-hidden="true">🗂</span> {{ rootLabel }}
        </button>
      </div>
    </li>
    <li
      v-for="row in rows"
      :key="row.folder.id"
      role="treeitem"
      :aria-selected="selectedId === row.folder.id"
      :aria-expanded="row.hasChildren ? expanded.has(row.folder.id) : undefined"
    >
      <div class="tree-row" :class="{ selected: selectedId === row.folder.id }" :style="indent(row.depth)">
        <button
          v-if="row.hasChildren"
          type="button"
          class="twisty"
          :aria-label="expanded.has(row.folder.id) ? `Collapse ${row.folder.name}` : `Expand ${row.folder.name}`"
          @click="toggle(row.folder.id)"
        >
          {{ expanded.has(row.folder.id) ? '▾' : '▸' }}
        </button>
        <span v-else class="twisty" aria-hidden="true"></span>
        <button type="button" class="tree-label" @click="emit('select', row.folder.id)">
          <span aria-hidden="true">📁</span> {{ row.folder.name }}
        </button>
      </div>
    </li>
  </ul>
</template>

<style scoped>
.folder-tree { list-style: none; margin: 0; padding: 0; }
.tree-row {
  display: flex; align-items: center; gap: 2px;
  border-radius: var(--radius-sm);
}
.tree-row:hover { background: var(--surface-sunken); }
.tree-row.selected { background: var(--teal-tint); }
.twisty {
  flex: 0 0 20px; height: 28px;
  display: inline-flex; align-items: center; justify-content: center;
  background: none; border: none; padding: 0;
  font-size: var(--text-sm); color: var(--text-muted);
}
.tree-label {
  flex: 1; min-width: 0; text-align: left;
  background: none; border: none; padding: 6px 6px 6px 0;
  font-size: var(--text-base); color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.tree-row.selected .tree-label { font-weight: 600; color: var(--teal-dark); }
</style>
