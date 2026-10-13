<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listPhysicalAssessments, startPhysicalAssessment } from '@/apis.js'
import { assessmentRoute, assessmentComparison, LABELS, resultText, physicalError } from '@/utils/physicalTests.js'
import AssessmentTrend from './AssessmentTrend.vue'
import { auth } from '@/stores/auth.js'

const props = defineProps({ participant: Object })
const router = useRouter()
const assessments = ref([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const draft = computed(() => assessments.value.find(row => row.status === 'draft'))
const comparison = computed(() => assessmentComparison(assessments.value))
const routeFor = id => ({ name: assessmentRoute(auth.user.role), params: { id } })
async function load() {
  loading.value = true
  error.value = ''
  try { assessments.value = await listPhysicalAssessments(props.participant.id) }
  catch (e) { error.value = physicalError(e) }
  finally { loading.value = false }
}
watch(() => props.participant.id, load, { immediate: true })
async function start() {
  saving.value = true
  error.value = ''
  try {
    const assessment = await startPhysicalAssessment(props.participant.id)
    await router.push(routeFor(assessment.id))
  } catch (e) { error.value = physicalError(e) }
  finally { saving.value = false }
}
</script>

<template>
  <section class="assessment-history">
    <h2>Physical assessments</h2>
    <p v-if="loading" class="loading-note">Loading assessments…</p>
    <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    <button v-if="error" class="btn-cancel" @click="load">Retry</button>
    <template v-if="!loading && !error">
      <RouterLink v-if="draft" class="btn-primary" :to="routeFor(draft.id)">Continue assessment</RouterLink>
      <button v-else-if="participant.is_active" class="btn-primary" :disabled="saving" @click="start">{{ saving ? 'Starting…' : 'Start physical assessment' }}</button>
      <p v-else class="loading-note">Inactive participant — existing results remain available.</p>
      <p v-if="!assessments.length" class="loading-note">No physical assessments recorded yet.</p>
      <div v-if="comparison.baseline" class="history-scroll">
        <p v-if="!comparison.latest" class="loading-note">One completed assessment. Complete a follow-up assessment to compare results.</p>
        <table class="data-table">
          <caption>Baseline and latest completed assessments</caption>
          <thead><tr>
            <th scope="col">Exercise</th>
            <th scope="col">Baseline<br /><RouterLink :to="routeFor(comparison.baseline.id)">{{ comparison.baseline.assessed_on }}</RouterLink></th>
            <th scope="col">Latest<br /><RouterLink v-if="comparison.latest" :to="routeFor(comparison.latest.id)">{{ comparison.latest.assessed_on }}</RouterLink></th>
            <th scope="col">Change (latest − baseline)</th>
          </tr></thead>
          <tbody><tr v-for="row in comparison.rows" :key="row.exercise">
            <th scope="row">{{ LABELS[row.exercise] }}</th>
            <td>{{ resultText(row.baseline) }}</td>
            <td>{{ comparison.latest ? resultText(row.latest) : '—' }}</td>
            <td>
              <template v-if="row.change !== null">{{ row.change > 0 ? '+' : '' }}{{ row.change }} {{ row.exercise === 'chair' ? 'stands' : 'seconds' }}</template>
              <template v-else>{{ comparison.latest ? 'Not comparable' : '—' }}</template>
            </td>
          </tr></tbody>
        </table>
        <p class="loading-note">Baseline is the earliest completed assessment by assessment date. Different testing conditions can affect comparisons.</p>
      </div>
      <p v-else-if="assessments.length" class="loading-note">Complete an assessment to establish a baseline.</p>
      <AssessmentTrend v-if="comparison.baseline" :assessments="assessments" />
      <div v-if="assessments.length" class="history-scroll">
        <table class="data-table">
          <caption>Assessment history — raw measurements, not clinical risk ratings</caption>
          <thead><tr><th>Date</th><th>Status</th><th v-for="label in LABELS" :key="label">{{ label }}</th></tr></thead>
          <tbody><tr v-for="assessment in assessments" :key="assessment.id">
            <td><RouterLink :to="routeFor(assessment.id)">{{ assessment.assessed_on }}</RouterLink></td>
            <td>{{ assessment.status }}</td>
            <td v-for="(_, key) in LABELS" :key="key">{{ resultText(assessment.results.find(row => row.exercise === key)) }}</td>
          </tr></tbody>
        </table>
      </div>
    </template>
  </section>
</template>

<style scoped>
.assessment-history { margin: 24px 0; padding: 20px 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.assessment-history h2 { margin-bottom: 16px; }
.history-scroll { overflow-x: auto; margin-top: 20px; }
caption { text-align: left; padding: 12px 0; font-size: var(--text-sm); color: var(--text-muted); }
</style>
