<script setup>
import { ref } from 'vue'
import ReportNarrative from './ReportNarrative.vue'
import { LABELS } from '@/utils/physicalTests.js'
import { formatReportNumber } from '@/utils/reporting.js'

const props = defineProps({ savedReport: { type: Object, required: true } })
defineEmits(['busy'])
const narrative = ref(props.savedReport.narrative)
const snapshot = props.savedReport.statistics
const attendance = snapshot.aggregates['S-attendance']
const physical = snapshot.aggregates['S-physical']
</script>

<template>
  <div>
    <h1>ACC report draft</h1>
    <p class="page-subtitle">{{ snapshot.scope_label }} · {{ snapshot.scope.start_date }} to {{ snapshot.scope.end_date }}</p>
    <p class="loading-note">Review the evidence, source references, and wording before using this draft. Saving edits does not approve it for submission.</p>
    <section id="acc-source-S-attendance" class="card report-section">
      <h2>Recorded participation</h2>
      <div class="stat-grid">
        <div v-for="[label, value] in [['Recorded sessions', attendance.total_sessions], ['Finalised registers', attendance.finalised_sessions], ['Incomplete registers', attendance.incomplete_sessions], ['Total attendances', attendance.total_attendances], ['Distinct attendees', attendance.distinct_attendees]]" :key="label" class="stat-tile">
          <div class="stat-tile-value">{{ value }}</div><div class="stat-tile-label">{{ label }}</div>
        </div>
      </div>
      <p>Source: S-attendance. Attendance counts use finalised registers.</p>
      <div id="acc-source-S-enrolments">
        <p><strong>New enrolments: {{ snapshot.aggregates['S-enrolments'].new_enrolments }}</strong></p>
        <p>Source: S-enrolments. {{ snapshot.aggregates['S-enrolments'].limitations }}</p>
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
      <p>Source: S-physical. Recorded changes do not establish programme causation.</p>
      <details><summary>Testing definitions and limitations</summary><ul><li v-for="item in physical.limitations" :key="item">{{ item }}</li></ul></details>
    </section>
    <section class="card report-section">
      <h2>Feedback and delivery narrative</h2>
      <p v-if="savedReport.model" class="loading-note">Model: {{ savedReport.model }}</p>
      <ReportNarrative :text="narrative" :job-id="savedReport.job_id" report-type="acc" @saved="narrative = $event" @busy="$emit('busy', $event)" />
    </section>
    <section class="card report-section">
      <h2>Saved feedback sources</h2>
      <p>Reporting copies approved for this draft. Source IDs connect the narrative to this saved evidence.</p>
      <article v-for="source in snapshot.sources" :id="`acc-source-${source.id}`" :key="source.id" class="source">
        <h3>{{ source.branch }} · {{ source.date }} · {{ source.speaker }}</h3>
        <p class="source-id">{{ source.id }}</p>
        <p class="source-text">{{ source.text }}</p>
        <details v-if="source.original_text !== source.text"><summary>Original recorded feedback (not sent to AI)</summary><p class="source-text">{{ source.original_text }}</p></details>
      </article>
    </section>
    <section class="card report-section"><h2>Report limitations</h2><ul><li v-for="item in snapshot.limitations" :key="item">{{ item }}</li></ul></section>
  </div>
</template>

<style scoped>
.report-section { margin-bottom: 24px; }
.table-scroll { overflow-x: auto; }
.source { border-top: 1px solid var(--border); padding: 16px 0; scroll-margin-top: 24px; }
.source-text { white-space: pre-wrap; }
.source-id { overflow-wrap: anywhere; font-size: var(--text-sm); }
</style>
