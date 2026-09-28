<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { groupBranchesByRegion } from '@/utils/documents.js'

// The dropdown for jumping between branches: search, recently opened
// branches, then every branch grouped by region. Branches are the explorer's
// scopes, { key, label, region }.
const props = defineProps({
  branches: { type: Array, required: true },
  selectedKey: { type: String, default: null },
  recentKeys: { type: Array, default: () => [] },
})
const emit = defineEmits(['select', 'close'])

const query = ref('')
const highlighted = ref(0)
const panel = ref(null)
const searchInput = ref(null)

// Sections of options, each option numbered in display order so the arrow
// keys can walk the whole list. Recents only show while not searching.
const sections = computed(() => {
  const q = query.value.trim().toLowerCase()
  const matches = q
    ? props.branches.filter(b => b.label.toLowerCase().includes(q) || (b.region ?? '').toLowerCase().includes(q))
    : props.branches
  const list = []
  if (!q) {
    const byKey = new Map(props.branches.map(b => [b.key, b]))
    const recent = props.recentKeys.map(k => byKey.get(k)).filter(Boolean)
    if (recent.length) list.push({ title: 'Recent', branches: recent })
  }
  list.push(...groupBranchesByRegion(matches))

  let index = 0
  return list.map(section => ({
    title: section.title,
    options: section.branches.map(branch => ({ branch, index: index++ })),
  }))
})
const options = computed(() => sections.value.flatMap(s => s.options))

watch(query, () => { highlighted.value = 0 })

function move(step) {
  if (!options.value.length) return
  highlighted.value = (highlighted.value + step + options.value.length) % options.value.length
  nextTick(() => panel.value?.querySelector('.highlighted')?.scrollIntoView({ block: 'nearest' }))
}

function onKeydown(event) {
  if (event.key === 'ArrowDown') { event.preventDefault(); move(1) }
  else if (event.key === 'ArrowUp') { event.preventDefault(); move(-1) }
  else if (event.key === 'Enter') {
    event.preventDefault()
    const option = options.value[highlighted.value]
    if (option) emit('select', option.branch.key)
  } else if (event.key === 'Escape') {
    event.stopPropagation()
    emit('close')
  }
}

// Close on any press outside the panel. The button that opens the switcher
// stops its own mousedown, so pressing it toggles rather than close-then-reopen.
function onOutsidePress(event) {
  if (!panel.value?.contains(event.target)) emit('close')
}

onMounted(() => {
  document.addEventListener('mousedown', onOutsidePress)
  nextTick(() => searchInput.value?.focus())
})
onBeforeUnmount(() => document.removeEventListener('mousedown', onOutsidePress))
</script>

<template>
  <div ref="panel" class="switcher" role="dialog" aria-label="Switch branch">
    <input
      ref="searchInput"
      v-model="query"
      type="search"
      class="switcher-search"
      placeholder="Search branches or regions…"
      aria-label="Search branches or regions"
      @keydown="onKeydown"
    />
    <div class="switcher-list" role="listbox">
      <template v-for="section in sections" :key="section.title">
        <p class="switcher-heading">{{ section.title }}</p>
        <button
          v-for="option in section.options"
          :key="`${section.title}:${option.branch.key}`"
          type="button"
          role="option"
          class="switcher-option"
          :class="{ highlighted: option.index === highlighted, current: option.branch.key === selectedKey }"
          :aria-selected="option.branch.key === selectedKey"
          @mouseenter="highlighted = option.index"
          @click="emit('select', option.branch.key)"
        >
          <span class="option-label">{{ option.branch.label }}</span>
          <span v-if="option.branch.key === selectedKey" class="option-check" aria-hidden="true">✓</span>
        </button>
      </template>
      <p v-if="!options.length" class="switcher-empty">No branches match “{{ query }}”.</p>
    </div>
  </div>
</template>

<style scoped>
.switcher {
  position: absolute; left: 0; top: calc(100% + 4px); z-index: 30;
  width: 280px; max-width: calc(100vw - 32px);
  padding: 8px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-panel);
}
.switcher-search {
  width: 100%; box-sizing: border-box;
  padding: 7px 10px; margin-bottom: 6px;
  border: 1.5px solid var(--border-strong); border-radius: var(--radius-sm);
  font-size: var(--text-base); background: var(--surface);
}
.switcher-search:focus { outline: none; border-color: var(--teal); }
.switcher-list { max-height: 320px; overflow-y: auto; }
.switcher-heading {
  margin: 8px 0 2px; padding: 0 8px;
  font-size: var(--text-xs); font-weight: 700; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--text-muted);
}
.switcher-option {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  width: 100%; text-align: left;
  background: none; border: none; border-radius: var(--radius-sm);
  padding: 7px 8px;
  font-size: var(--text-base); color: var(--text);
}
.switcher-option.highlighted { background: var(--surface-sunken); }
.switcher-option.current { font-weight: 600; color: var(--teal-dark); }
.option-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.option-check { color: var(--teal-dark); }
.switcher-empty { margin: 8px; font-size: var(--text-sm); color: var(--text-faint); }
</style>
