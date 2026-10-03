<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { getPhysicalReport, analysePhysicalReport, getPhysicalAnalysisJob, listBranches } from '@/apis.js'
import { recentReportPeriod, formatReportNumber } from '@/utils/reporting.js'
import { LABELS, physicalError } from '@/utils/physicalTests.js'
import MeasurementChart from '@/components/charts/MeasurementChart.vue'
import AssessmentTrend from '@/components/physicalTests/AssessmentTrend.vue'
import ReportAnalysis from './ReportAnalysis.vue'

const props = defineProps({ showBranchFilter: Boolean, branchName: String })
const dates = recentReportPeriod()
const startDate = ref(dates.start_date), endDate = ref(dates.end_date), branchId = ref('')
const branches = ref([]), branchError = ref(''), error = ref('')
const report = ref(null), loading = ref(false), analysing = ref(false)
const selectedId = ref(''), exercise = ref('tug'), search = ref('')
const generation = ref(0)
const busy = computed(() => loading.value || analysing.value)
const scope = computed(() => ({ start_date: startDate.value, end_date: endDate.value,
  ...(props.showBranchFilter && branchId.value ? { branch_id: branchId.value } : {}) }))
const selected = computed(() => report.value?.participants.find(p => p.id === selectedId.value))
const people = computed(() => report.value?.participants.filter(p => `${p.name} ${p.branch}`.toLowerCase().includes(search.value.trim().toLowerCase())) || [])
const points = computed(() => report.value?.monthly.map(month => ({ date: `${month.month}-01`,
  value: month.metrics.find(metric => metric.exercise === exercise.value)?.mean ?? null,
  note: `${month.metrics.find(metric => metric.exercise === exercise.value)?.count || 0} scored assessments`,
})) || [])
const tiles = computed(() => {
  const t = report.value?.totals
  return t ? [['Eligible participants', t.eligible_participants], ['Testing completed — Yes', t.tested_participants],
    ['Testing completed — No', t.untested_participants], ['Completion', formatReportNumber(t.completion_percent, '%')],
    ['Completed assessments', t.completed_assessments], ['Draft assessments', t.draft_assessments]] : []
})
watch([startDate, endDate, branchId], () => { report.value = null; error.value = ''; selectedId.value = ''; generation.value++ })
async function load() {
  if (busy.value) return
  report.value = null
  error.value = ''
  selectedId.value = ''
  generation.value++
  if (!startDate.value || !endDate.value || startDate.value > endDate.value) { error.value = 'Choose a valid date range.'; return }
  loading.value = true
  try { report.value = await getPhysicalReport(scope.value) }
  catch (e) { error.value = physicalError(e) }
  finally { loading.value = false }
}
onMounted(async () => {
  load()
  if (props.showBranchFilter) {
    try { branches.value = await listBranches() }
    catch { branchError.value = 'Could not load branches. You can still report across all branches.' }
  }
})
function analysed(result) {
  // Replace displayed data with the worker's exact snapshot, not a later live query.
  report.value = result.statistics
}
</script>

<template>
  <div class="page-header"><h1>Physical-testing reporting</h1></div>
  <p class="page-subtitle">{{ showBranchFilter ? 'National or selected branch' : branchName }} · Testing completion, measurements and recorded changes.</p>
  <form @submit.prevent="load"><fieldset :disabled="busy">
    <legend>Inclusive reporting dates</legend>
    <p class="loading-note">Defaults to the last three months through today. Adjust the dates to include older assessments.</p>
    <div class="form-row">
      <div class="form-group"><label for="physical-from">From</label><input id="physical-from" v-model="startDate" type="date" required /></div>
      <div class="form-group"><label for="physical-to">To</label><input id="physical-to" v-model="endDate" type="date" required /></div>
    </div>
    <div v-if="showBranchFilter" class="form-group"><label for="physical-branch">Branch</label>
      <select id="physical-branch" v-model="branchId"><option value="">All branches</option><option v-for="branch in branches" :key="branch.id" :value="branch.id">{{ branch.name }}</option></select>
    </div>
    <button class="btn-primary">Refresh statistics</button>
  </fieldset></form>
  <p v-if="branchError" class="form-error" role="alert">{{ branchError }}</p>
  <p v-if="error" class="form-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="loading-note">Loading physical-testing statistics…</p>
  <p v-else-if="!report && !error" class="loading-note">Select dates and refresh statistics.</p>
  <template v-if="report">
    <p class="page-subtitle">{{ report.scope.start_date }} to {{ report.scope.end_date }}</p>
    <div class="stat-grid"><div v-for="[label, value] in tiles" :key="label" class="stat-tile"><div class="stat-tile-value">{{ value }}</div><div class="stat-tile-label">{{ label }}</div></div></div>
    <p v-if="!report.totals.eligible_participants" class="loading-note">No eligible participants in this selection.</p>
    <p v-else-if="!report.totals.completed_assessments" class="loading-note">No completed assessments in this selection. Participants without testing are listed below.</p>
    <section class="card report-section">
      <h2>Testing by participant</h2>
      <p>Yes means at least one completed assessment in the selected dates. It does not mean every exercise was successfully performed.</p>
      <div class="form-group"><label for="physical-search">Find a participant</label><input id="physical-search" v-model="search" type="search" /></div>
      <div class="table-scroll"><table class="data-table">
        <thead><tr><th>Participant</th><th>Branch</th><th>Completed testing?</th><th>Assessments</th><th>Drafts</th><th>Results</th></tr></thead>
        <tbody><tr v-if="!people.length"><td colspan="6">No participants match.</td></tr>
          <tr v-for="person in people" :key="person.id">
            <td><RouterLink :to="{ name: 'participant-detail', params: { id: person.id } }">{{ person.name }}</RouterLink></td>
            <td>{{ person.branch }}</td><td>{{ person.testing_completed ? 'Yes' : 'No' }}</td><td>{{ person.completed_assessments }}</td><td>{{ person.draft_assessments }}</td>
            <td><button class="btn-cancel" @click="selectedId = person.id">View results</button></td>
          </tr>
        </tbody>
      </table></div>
    </section>
    <section v-if="selected" class="card report-section" aria-live="polite">
      <h2>{{ selected.name }} — results in this period</h2>
      <AssessmentTrend :assessments="selected.history" />
      <div class="table-scroll"><table class="data-table"><thead><tr><th>Exercise</th><th>First date / value</th><th>Last date / value</th><th>Change</th></tr></thead>
        <tbody><tr v-for="change in selected.changes" :key="change.exercise">
          <td>{{ LABELS[change.exercise] }}</td><td>{{ change.first_date || '—' }} / {{ formatReportNumber(change.first) }}</td>
          <td>{{ change.last_date || '—' }} / {{ formatReportNumber(change.last) }}</td><td>{{ formatReportNumber(change.change, change.exercise === 'chair' ? ' stands' : ' s') }}</td>
        </tr></tbody></table></div>
      <p>Change is last minus first. A dash means no comparable pair on different dates within this selection. TUG comparisons also require matching walking-aid descriptions.</p>
    </section>
    <section class="card report-section">
      <h2>Exercise summary</h2>
      <div class="table-scroll"><table class="data-table"><thead><tr><th>Exercise</th><th>Scored results</th><th>Mean</th><th>Unable</th><th>Skipped</th><th>Arms needed (zero)</th><th>Paired people</th><th>Mean paired change</th></tr></thead>
        <tbody><tr v-for="metric in report.metrics" :key="metric.exercise">
          <td>{{ LABELS[metric.exercise] }}</td><td>{{ metric.count }}</td><td>{{ formatReportNumber(metric.mean, metric.exercise === 'chair' ? ' stands' : ' s') }}</td>
          <td>{{ metric.outcomes.unable }}</td><td>{{ metric.outcomes.skipped }}</td><td>{{ metric.outcomes.arms_used }}</td>
          <td>{{ report.paired_changes.find(p => p.exercise === metric.exercise).participants }}</td>
          <td>{{ formatReportNumber(report.paired_changes.find(p => p.exercise === metric.exercise).mean_change, metric.exercise === 'chair' ? ' stands' : ' s') }}</td>
        </tr></tbody></table></div>
      <p>Paired changes compare each person's first and last comparable scores. Means include repeated assessments; they are not clinical ratings.</p>
    </section>
    <section class="card report-section">
      <h2>Monthly recorded measurements</h2>
      <div class="form-group"><label for="physical-metric">Exercise</label><select id="physical-metric" v-model="exercise"><option v-for="(label, key) in LABELS" :key="key" :value="key">{{ label }}</option></select></div>
      <MeasurementChart :points="points" :title="`Monthly mean — ${LABELS[exercise]}`" :unit="exercise === 'chair' ? 'stands' : 'seconds'" />
      <p>Each point represents a month's available scored assessments. The people and number of assessments may differ between months; missing months are gaps.</p>
    </section>
    <ReportAnalysis :key="generation" class="report-section" :scope="scope" :start="analysePhysicalReport" :get-status="getPhysicalAnalysisJob" :has-data="!!report.totals.completed_assessments" :disabled="loading" @busy="analysing = $event" @complete="analysed" />
    <section class="card report-section"><h2>How to read this report</h2><ul><li v-for="item in report.limitations" :key="item">{{ item }}</li></ul></section>
  </template>
</template>

<style scoped>
fieldset { border: 0; margin: 0 0 24px; padding: 0; }
legend { color: var(--text-muted); margin-bottom: 12px; }
.report-section { margin-bottom: 24px; }
.table-scroll { overflow-x: auto; }
li { margin-bottom: 8px; color: var(--text-secondary); }
</style>
