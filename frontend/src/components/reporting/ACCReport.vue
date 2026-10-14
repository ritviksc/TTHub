<script setup>
import { computed, ref } from 'vue'
import ReportNarrative from './ReportNarrative.vue'
import { LABELS } from '@/utils/physicalTests.js'
import { formatReportNumber } from '@/utils/reporting.js'
import { printReport } from '@/utils/printReport.js'
import { feedbackSpeakerLabel } from '@/utils/feedback.js'

const props = defineProps({ savedReport: { type: Object, required: true } })
defineEmits(['busy'])
const narrative = ref(props.savedReport.narrative)
const reportElement = ref(null), editing = ref(false), exportError = ref('')
// Saved drafts retain evidence references internally; omit their generated citation lines in the report and editor.
const displayNarrative = computed(() => narrative.value.replace(
  /^(?:Sources: )?\[[^\]\n]+\]\(#acc-source-[^)\n]+\)(?:, \[[^\]\n]+\]\(#acc-source-[^)\n]+\))*\r?$/gm, '',
))
const snapshot = props.savedReport.statistics
const engagement = snapshot.aggregates['S-engagement']
const attendance = snapshot.aggregates['S-attendance']
const physical = snapshot.aggregates['S-physical']

function downloadPDF() {
  if (editing.value) return
  exportError.value = ''
  try {
    printReport(reportElement.value, `ACC report - ${snapshot.scope_label} - ${snapshot.scope.start_date} to ${snapshot.scope.end_date}`)
  } catch (e) { exportError.value = e.message }
}
</script>

<template>
  <div ref="reportElement">
    <h1>ACC report draft</h1>
    <p class="page-subtitle">{{ snapshot.scope_label }} · {{ snapshot.scope.start_date }} to {{ snapshot.scope.end_date }}</p>
    <div class="pdf-actions" data-print-exclude>
      <button type="button" class="btn-primary" :disabled="editing" @click="downloadPDF">Download PDF</button>
      <p class="loading-note">Choose Save as PDF in the print dialog. Save or cancel any edits first.</p>
      <p v-if="exportError" class="form-error" role="alert">{{ exportError }}</p>
    </div>
    <p class="loading-note">Review the evidence and wording before using this draft. Saving edits does not approve it for submission.</p>
    <section v-if="engagement" id="acc-source-S-engagement" class="card report-section">
      <h2>Engagement</h2>
      <h3>Participation</h3>
      <div class="table-scroll"><table class="data-table engagement-table">
        <colgroup><col style="width:44%" /><col style="width:15%" /><col style="width:13%" /><col style="width:15%" /><col style="width:13%" /></colgroup>
        <thead><tr><th scope="col">Entity</th><th scope="col">Location</th><th scope="col"># Participants</th><th scope="col"># New Participants</th><th scope="col">% Engagement</th></tr></thead>
        <tbody><tr v-for="branch in engagement.branches" :key="branch.branch_id">
          <th scope="row">{{ branch.entity }}</th><td>{{ branch.location || 'Not recorded' }}</td>
          <td>{{ branch.participants }}</td><td>{{ branch.new_participants }}</td>
          <td>{{ formatReportNumber(branch.engagement_percent == null ? null : Math.round(branch.engagement_percent / 5) * 5, '%') }}</td>
        </tr></tbody>
      </table></div>
      <p v-if="!engagement.branches.length">No branches were recorded for this scope when the report was generated.</p>
      <p>Engagement is attendance rate: attendances ÷ roster places across finalised sessions × 100, rounded to the nearest 5%.</p>
      <details><summary>Participation definitions and limitations</summary><ul><li v-for="item in engagement.limitations" :key="item">{{ item }}</li></ul></details>
    </section>
    <section v-else id="acc-source-S-attendance" class="card report-section">
      <h2>Engagement</h2>
      <p>Branch participation was not saved with this draft. Generate a new report to include the branch table.</p>
      <div class="stat-grid">
        <div v-for="[label, value] in [['Recorded sessions', attendance.total_sessions], ['Finalised registers', attendance.finalised_sessions], ['Incomplete registers', attendance.incomplete_sessions], ['Total attendances', attendance.total_attendances], ['Distinct attendees', attendance.distinct_attendees]]" :key="label" class="stat-tile">
          <div class="stat-tile-value">{{ value }}</div><div class="stat-tile-label">{{ label }}</div>
        </div>
      </div>
      <p>Attendance counts use finalised registers.</p>
      <div id="acc-source-S-enrolments">
        <p><strong>New enrolments: {{ snapshot.aggregates['S-enrolments'].new_enrolments }}</strong></p>
        <p>{{ snapshot.aggregates['S-enrolments'].limitations }}</p>
      </div>
    </section>
    <section id="acc-source-S-physical" class="card report-section">
      <h2>Recorded physical testing</h2>
      <p>{{ physical.totals.tested_participants }} of {{ physical.totals.eligible_participants }} eligible participants have a completed assessment; {{ physical.totals.completed_assessments }} completed assessments in total.</p>
      <div class="table-scroll"><table class="data-table">
        <thead><tr><th>Exercise</th><th>People with comparable results</th><th>Mean change (last − first)</th></tr></thead>
        <tbody><tr v-for="change in physical.paired_changes" :key="change.exercise">
          <td>{{ LABELS[change.exercise] }}</td><td>{{ change.participants }}</td>
          <td>{{ formatReportNumber(change.mean_change, change.exercise === 'chair' ? ' stands' : ' s') }}</td>
        </tr></tbody>
      </table></div>
      <p>Recorded changes do not establish programme causation.</p>
      <details><summary>Testing definitions and limitations</summary><ul><li v-for="item in physical.limitations" :key="item">{{ item }}</li></ul></details>
    </section>
    <section class="card report-section">
      <h2>Feedback and delivery narrative</h2>
      <p v-if="savedReport.model" class="loading-note">Model: {{ savedReport.model }}</p>
      <ReportNarrative :text="displayNarrative" :job-id="savedReport.job_id" report-type="acc" @saved="narrative = $event" @busy="editing = $event; $emit('busy', $event)" />
    </section>
    <section class="card report-section">
      <h2>Saved feedback sources</h2>
      <p>Reporting copies approved for this draft.</p>
      <article v-for="source in snapshot.sources" :id="`acc-source-${source.id}`" :key="source.id" class="source">
        <h3>{{ source.branch }} · {{ source.date }} · {{ feedbackSpeakerLabel(source.speaker) }}</h3>
        <p class="source-text">{{ source.text }}</p>
        <details v-if="source.original_text !== source.text" data-print-exclude><summary>Original recorded feedback (not sent to AI)</summary><p class="source-text">{{ source.original_text }}</p></details>
      </article>
    </section>
    <section class="card report-section"><h2>Report limitations</h2><ul><li v-for="item in snapshot.limitations" :key="item">{{ item }}</li></ul></section>
  </div>
</template>

<style scoped>
.report-section { margin-bottom: 24px; }
.pdf-actions { margin-bottom: 20px; }
.pdf-actions .loading-note { margin-top: 8px; }
.table-scroll { overflow-x: auto; }
.engagement-table { margin: 12px 0; table-layout: fixed; min-width: 720px; }
.engagement-table tbody th { font-weight: normal; background: var(--surface); color: var(--text-secondary); }
.source { border-top: 1px solid var(--border); padding: 16px 0; scroll-margin-top: 24px; }
.source-text { white-space: pre-wrap; }
</style>
