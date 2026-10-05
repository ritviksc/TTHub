<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { listAuditEvents, listBranches } from '@/apis.js'

const props = defineProps({ showBranchFilter: Boolean, backRoute: String, branchName: String, branchId: String })

const filters = ref({ q: '', category: '', branch_id: '', outcome: '', start_date: '', end_date: '' })
const applied = ref({})
const entries = ref([]), branches = ref([])
const loading = ref(false), error = ref(''), branchError = ref('')
const page = ref(1), count = ref(0), hasNext = ref(false)
let generation = 0
onBeforeUnmount(() => { generation++ })
const categories = [
  ['staff', 'Staff changes'], ['branches', 'Branch settings'], ['reports', 'Reports'],
  ['records', 'Record updates'], ['signins', 'Sign-ins'],
]

function formatTime(value) {
  return new Intl.DateTimeFormat('en-NZ', {
    dateStyle: 'medium', timeStyle: 'short', timeZone: 'Pacific/Auckland',
  }).format(new Date(value))
}
async function load(nextPage = 1) {
  const current = ++generation
  loading.value = true; error.value = ''; entries.value = []
  try {
    const result = await listAuditEvents({ ...applied.value, page: nextPage })
    if (generation !== current) return
    entries.value = result.results
    count.value = result.count
    hasNext.value = Boolean(result.next)
    page.value = nextPage
  } catch (e) {
    if (generation === current) error.value = e.response?.data?.non_field_errors?.[0]
      || e.response?.data?.detail || 'Could not load the audit log. Check your filters and try again.'
  } finally {
    if (generation === current) loading.value = false
  }
}
function applyFilters() {
  // Paging retains the submitted filters, even while a user edits the form.
  applied.value = Object.fromEntries(Object.entries(filters.value).filter(([, value]) => value !== ''))
  load(1)
}
onMounted(async () => {
  load()
  if (!props.showBranchFilter) return
  try { branches.value = await listBranches() }
  catch { branchError.value = 'Branch options could not be loaded. Other filters are still available.' }
})
</script>

<template>
  <div class="dash-page"><main class="content">
    <RouterLink class="back-link" :to="{ name: backRoute }">← Administration</RouterLink>
    <div class="page-header"><h1>Audit log</h1></div>
    <p class="page-subtitle">{{ showBranchFilter ? 'All branches' : branchName }} · Recent activity · New Zealand time</p>
    <form @submit.prevent="applyFilters">
      <fieldset :disabled="loading">
        <legend>Filter activity</legend>
        <div class="form-row">
          <div class="form-group"><label for="audit-search">Search staff email</label><input id="audit-search" v-model.trim="filters.q" type="search" maxlength="254" /></div>
          <div class="form-group"><label for="audit-action">Activity</label><select id="audit-action" v-model="filters.category"><option value="">All activity</option><option v-for="[value, label] in categories" :key="value" :value="value">{{ label }}</option></select></div>
        </div>
        <div class="form-row">
          <div v-if="showBranchFilter" class="form-group"><label for="audit-branch">Branch</label><select id="audit-branch" v-model="filters.branch_id"><option value="">All branches</option><option v-for="branch in branches" :key="branch.id" :value="branch.id">{{ branch.name }}</option></select></div>
          <div class="form-group"><label for="audit-outcome">Result</label><select id="audit-outcome" v-model="filters.outcome"><option value="">All results</option><option value="success">Successful</option><option value="failed">Could not complete</option><option value="denied">Not permitted</option></select></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label for="audit-from">From (inclusive)</label><input id="audit-from" v-model="filters.start_date" type="date" /></div>
          <div class="form-group"><label for="audit-to">To (inclusive)</label><input id="audit-to" v-model="filters.end_date" type="date" /></div>
        </div>
        <button class="btn-primary" type="submit">Show activity</button>
      </fieldset>
    </form>
    <p v-if="branchError" class="form-error" role="alert">{{ branchError }}</p>
    <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    <p v-if="loading" class="loading-note" role="status">Loading activity…</p>
    <template v-else-if="!error">
      <p v-if="!entries.length" class="loading-note">No activity matches these filters.</p>
      <template v-else>
        <p>{{ count }} entries · Page {{ page }}</p>
        <div class="table-scroll"><table class="data-table">
          <thead><tr><th>When</th><th>Staff member</th><th>What happened</th><th v-if="showBranchFilter">Branch</th><th>Result</th></tr></thead>
          <tbody><tr v-for="entry in entries" :key="entry.id">
            <td>{{ formatTime(entry.created_at) }}</td>
            <td>{{ entry.person }}</td>
            <td>{{ entry.description }}</td>
            <td v-if="showBranchFilter">{{ entry.branch }}</td>
            <td><span class="status-badge">{{ entry.result }}</span></td>
          </tr></tbody>
        </table></div>
        <div class="pagination">
          <button class="btn-cancel" :disabled="page <= 1" @click="load(page - 1)">Previous</button>
          <button class="btn-cancel" :disabled="!hasNext" @click="load(page + 1)">Next</button>
        </div>
      </template>
    </template>
  </main></div>
</template>

<style scoped>
fieldset { border: 0; padding: 0; margin-bottom: 24px; }
legend { color: var(--text-muted); margin-bottom: 12px; }
.table-scroll { overflow-x: auto; }
td { vertical-align: top; }
.pagination { display: flex; gap: 12px; margin-top: 20px; }
</style>
