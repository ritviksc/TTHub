<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  getAttendanceReport, analyseAttendanceReport, listBranches, withRetry,
} from '@/apis.js'
import {
  currentQuarter, demoAttendanceReport, DEMO_NARRATIVE, formatReportNumber,
} from '@/utils/reporting.js'

const props = defineProps({ showBranchFilter: Boolean, branchName: { type: String, default: '' } })
const dates = currentQuarter()
const startDate = ref(dates.start_date)
const endDate = ref(dates.end_date)
const branchId = ref('')
const branches = ref([])
const branchError = ref(null)
const report = ref(null)
const narrative = ref(null)
const loading = ref(false)
const analysing = ref(false)
const error = ref(null)
const analysisError = ref(null)
const demo = ref(false)
const busy = computed(() => loading.value || analysing.value)
const scope = () => ({
  start_date: startDate.value, end_date: endDate.value,
  ...(props.showBranchFilter && branchId.value ? { branch_id: branchId.value } : {}),
})
const scopeLabel = computed(() => demo.value ? 'Fictional demo branch' :
  props.showBranchFilter ? branches.value.find(b => b.id === branchId.value)?.name ?? 'All branches' : props.branchName)
const tiles = computed(() => {
  const t = report.value?.totals
  if (!t) return []
  return [
    ['Finalised sessions', t.finalised_sessions], ['Incomplete sessions', t.incomplete_sessions],
    ['Empty finalised sessions', t.empty_sessions], ['Total attendances', t.total_attendances],
    ['Distinct attendees', t.distinct_attendees], ['Attendance rate', formatReportNumber(t.attendance_rate_percent, '%')],
    ['Average per finalised session', formatReportNumber(t.average_attendance)],
  ]
})

function messageFor(e, fallback) {
  const data = e.response?.data
  return data?.detail ?? data?.start_date?.[0] ?? data?.end_date?.[0] ?? data?.non_field_errors?.[0] ?? fallback
}

// Never leave a narrative visible under filters that describe a different report.
watch([startDate, endDate, branchId], () => {
  report.value = null
  narrative.value = null
  error.value = null
  analysisError.value = null
})

async function loadReport() {
  if (busy.value) return
  error.value = null
  analysisError.value = null
  narrative.value = null
  report.value = null
  if (!startDate.value || !endDate.value || startDate.value > endDate.value) {
    error.value = 'Choose valid start and end dates in chronological order.'
    return
  }
  loading.value = true
  try {
    report.value = await withRetry(null, getAttendanceReport, scope())
  } catch (e) {
    error.value = messageFor(e, 'Could not load attendance statistics. Please try again.')
  } finally {
    loading.value = false
  }
}

async function analyse() {
  if (busy.value || !report.value?.totals.finalised_sessions) return
  analysisError.value = null
  narrative.value = null
  if (demo.value) {
    narrative.value = DEMO_NARRATIVE
    return
  }
  analysing.value = true
  try {
    const result = await analyseAttendanceReport(scope())
    // Display the exact statistics used for this narrative if records changed since loading.
    report.value = result.statistics
    narrative.value = result.narrative
  } catch (e) {
    analysisError.value = messageFor(e, 'Analysis could not be completed. Your statistics are still available.')
  } finally {
    analysing.value = false
  }
}

function toggleDemo() {
  if (busy.value) return
  demo.value = !demo.value
  narrative.value = null
  analysisError.value = null
  error.value = null
  if (demo.value) report.value = demoAttendanceReport()
  else loadReport()
}

async function loadBranches() {
  if (!props.showBranchFilter) return
  try {
    branches.value = await withRetry(null, listBranches)
  } catch {
    branchError.value = 'Branch options could not be loaded. You can still view all branches.'
  }
}

onMounted(() => {
  loadReport()
  loadBranches()
})
</script>

<template>
  <div class="page-header">
    <div>
      <h1>Attendance reporting</h1>
      <p class="page-subtitle">{{ scopeLabel }} · Statistics load automatically. Request an AI explanation when needed.</p>
    </div>
    <button class="btn-cancel" :disabled="busy" @click="toggleDemo">
      {{ demo ? 'Return to live data' : 'Show demo data' }}
    </button>
  </div>

  <p v-if="demo" class="demo-banner" role="status">Demo preview — fictional January–March 2026 data. It is not saved or sent to the AI provider.</p>
  <form @submit.prevent="loadReport">
    <fieldset :disabled="busy || demo">
      <legend>Report period and scope</legend>
      <div class="form-row">
        <div class="form-group"><label for="report-start">From (inclusive)</label><input id="report-start" v-model="startDate" type="date" required /></div>
        <div class="form-group"><label for="report-end">To (inclusive)</label><input id="report-end" v-model="endDate" type="date" required /></div>
      </div>
      <div v-if="showBranchFilter" class="form-group">
        <label for="report-branch">Branch</label>
        <select id="report-branch" v-model="branchId">
          <option value="">All branches</option>
          <option v-for="branch in branches" :key="branch.id" :value="branch.id">{{ branch.name }}</option>
        </select>
      </div>
      <button class="btn-primary" type="submit">Refresh statistics</button>
    </fieldset>
  </form>
  <p v-if="branchError && !demo" class="form-error" role="alert">{{ branchError }}</p>
  <p v-if="error" class="form-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="loading-note" role="status">Loading attendance statistics…</p>
  <p v-else-if="!report && !error" class="loading-note">Select your filters, then refresh statistics.</p>

  <template v-if="report">
    <p class="page-subtitle">{{ report.scope.start_date }} to {{ report.scope.end_date }} · {{ report.totals.total_sessions }} sessions recorded</p>
    <p v-if="!report.totals.total_sessions" class="loading-note">No sessions were recorded for this period and scope.</p>
    <p v-else-if="!report.totals.finalised_sessions" class="loading-note">All registers are incomplete. Finalise attendance before analysing this period.</p>
    <div class="stat-grid">
      <div v-for="[label, value] in tiles" :key="label" class="stat-tile">
        <div class="stat-tile-value">{{ value }}</div><div class="stat-tile-label">{{ label }}</div>
      </div>
    </div>
    <section class="card report-section">
      <h2>Monthly attendance</h2>
      <p>Rates include finalised empty sessions. Incomplete registers are excluded. Changes compare adjacent months within the selected dates.</p>
      <div class="table-scroll">
        <table class="data-table">
          <thead><tr><th>Month</th><th>Finalised</th><th>Incomplete</th><th>Empty</th><th>Attendances</th><th>Rate</th><th>Rate change</th></tr></thead>
          <tbody>
            <tr v-for="month in report.monthly" :key="month.month">
              <td>{{ month.month }}</td><td>{{ month.finalised_sessions }}</td><td>{{ month.incomplete_sessions }}</td>
              <td>{{ month.empty_sessions }}</td><td>{{ month.total_attendances }}</td>
              <td>{{ formatReportNumber(month.attendance_rate_percent, '%') }}</td>
              <td>{{ formatReportNumber(month.attendance_rate_change_percentage_points, ' pp') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <section class="card report-section" aria-live="polite">
      <div class="page-header">
        <h2>{{ demo ? 'Example explanation' : 'AI attendance explanation' }}</h2>
        <button class="btn-primary" :disabled="busy || !report.totals.finalised_sessions" @click="analyse">
          {{ analysing ? 'Analysing…' : demo ? 'Show example explanation' : 'Analyse attendance' }}
        </button>
      </div>
      <p v-if="analysisError" class="form-error" role="alert">{{ analysisError }}</p>
      <p v-if="analysing" class="loading-note">Generating an explanation. This may take a few minutes.</p>
      <p v-else-if="narrative" class="narrative">{{ narrative }}</p>
      <p v-else>Use the button to explain the recorded trends. Statistics are available without AI.</p>
      <p v-if="narrative && !demo" class="analysis-note">This explanation is AI-generated and may vary between requests, even with the same data. Check its accuracy before using it in a formal report. Statistics are calculated from recorded attendance.</p>
    </section>
    <section class="card report-section">
      <h2>How to read this report</h2>
      <ul><li v-for="limitation in report.limitations" :key="limitation">{{ limitation }}</li></ul>
    </section>
  </template>
</template>

<style scoped>
fieldset { border: 0; padding: 0; margin: 0 0 24px; }
legend { font-size: var(--text-sm); color: var(--text-muted); margin-bottom: 12px; }
.report-section { margin-bottom: 24px; }
.table-scroll { overflow-x: auto; }
.narrative { white-space: pre-wrap; overflow-wrap: anywhere; }
.card p.analysis-note { font-size: var(--text-sm); color: var(--text-muted); }
.demo-banner { padding: 16px; background: var(--teal-tint); color: var(--teal-dark); border-radius: var(--radius-sm); }
li { margin-bottom: 8px; color: var(--text-secondary); }
button:disabled { opacity: 0.6; cursor: not-allowed; }
@media (max-width: 640px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 12px; }
  .form-row { grid-template-columns: 1fr; }
}
</style>
