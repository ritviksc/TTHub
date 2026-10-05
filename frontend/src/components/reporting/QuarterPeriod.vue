<script setup>
import { ref, watch, computed, onBeforeUnmount } from 'vue'
import { getBranchQuarters, saveBranchQuarters } from '@/apis.js'
import { calendarQuarters } from '@/utils/quarters.js'
import { programmeToday } from '@/utils/sessions.js'

const props = defineProps({ branchId: { type: String, default: '' } })
const emit = defineEmits(['select'])
const year = ref(Number(programmeToday().slice(0, 4)))
const quarter = ref(1)
const rows = ref([]), drafts = ref([])
const loading = ref(false), saving = ref(false), error = ref(''), notice = ref('')
const isDefault = ref(true)
const selected = computed(() => rows.value.find(row => row.quarter === Number(quarter.value)))
let generation = 0
onBeforeUnmount(() => { generation++ })

watch([() => props.branchId, year], load, { immediate: true })
async function load() {
  const current = ++generation
  rows.value = []; drafts.value = []; error.value = ''; notice.value = ''
  if (!Number.isInteger(year.value) || year.value < 1900 || year.value > 9998) {
    loading.value = false
    error.value = 'Choose a year from 1900 to 9998.'
    return
  }
  loading.value = true
  try {
    const result = props.branchId ? await getBranchQuarters(props.branchId, year.value)
      : { quarters: calendarQuarters(year.value), is_default: true }
    // A slow response for a previous branch/year must not replace this selection.
    if (current !== generation) return
    rows.value = result.quarters
    drafts.value = result.quarters.map(row => ({ ...row }))
    isDefault.value = result.is_default
  } catch {
    if (current === generation) error.value = 'Could not load quarter dates. You can still use the date range above.'
  } finally {
    if (current === generation) loading.value = false
  }
}
async function save() {
  if (saving.value || loading.value || !props.branchId) return
  const current = generation
  saving.value = true; error.value = ''; notice.value = ''
  try {
    const result = await saveBranchQuarters(props.branchId, year.value, drafts.value)
    if (current !== generation) return
    rows.value = result.quarters
    drafts.value = result.quarters.map(row => ({ ...row }))
    isDefault.value = result.is_default
    notice.value = 'Quarter dates saved. Use a quarter below to update your report dates.'
  } catch (e) {
    if (current === generation) {
      const data = e.response?.data
      error.value = data?.detail || (typeof data?.quarters?.[0] === 'string' ? data.quarters[0] : null)
        || (data ? 'Check all four quarters have valid start and end dates.' : 'Could not save quarter dates. Please try again.')
    }
  } finally { saving.value = false }
}
</script>

<template>
  <section class="card quarter-period">
    <h2>Reporting quarters</h2>
    <p>{{ branchId ? 'Choose a branch quarter, or edit its dates for this year.' : 'All branches uses standard calendar quarters. Select a branch to use or configure its own dates.' }}</p>
    <div class="form-row">
      <div class="form-group"><label for="quarter-year">Year</label><input id="quarter-year" v-model.number="year" type="number" min="1900" max="9998" :disabled="saving" /></div>
      <div class="form-group"><label for="quarter-number">Quarter</label><select id="quarter-number" v-model.number="quarter"><option v-for="q in 4" :key="q" :value="q">Q{{ q }}</option></select></div>
    </div>
    <p v-if="loading" class="loading-note" role="status">Loading quarter dates…</p>
    <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    <p v-if="notice" role="status">{{ notice }}</p>
    <template v-if="selected">
      <p>{{ selected.start_date }} to {{ selected.end_date }} (inclusive) · {{ isDefault ? 'Calendar defaults' : 'Branch settings' }}</p>
      <button class="btn-cancel" type="button" :disabled="loading || saving" @click="emit('select', { ...selected })">Use Q{{ quarter }} dates</button>
    </template>
    <details v-if="branchId && rows.length">
      <summary>Edit this branch’s quarter dates</summary>
      <p>All dates must be in {{ year }}. Quarters must be ordered without overlap; gaps are allowed. Saving changes future report selections, including for past years. Existing AI snapshots retain their original dates.</p>
      <fieldset :disabled="saving || loading">
        <legend>Dates for {{ year }}</legend>
        <div v-for="row in drafts" :key="row.quarter" class="form-row">
          <div class="form-group"><label :for="`q${row.quarter}-start`">Q{{ row.quarter }} from</label><input :id="`q${row.quarter}-start`" v-model="row.start_date" type="date" /></div>
          <div class="form-group"><label :for="`q${row.quarter}-end`">Q{{ row.quarter }} to</label><input :id="`q${row.quarter}-end`" v-model="row.end_date" type="date" /></div>
        </div>
        <button class="btn-cancel" type="button" @click="drafts = calendarQuarters(year)">Fill calendar defaults</button>
        <button class="btn-primary" type="button" @click="save">{{ saving ? 'Saving…' : 'Save quarter dates' }}</button>
      </fieldset>
    </details>
  </section>
</template>

<style scoped>
.quarter-period { margin-bottom: 24px; }
details { margin-top: 16px; }
summary { cursor: pointer; }
fieldset { border: 0; padding: 0; }
</style>
