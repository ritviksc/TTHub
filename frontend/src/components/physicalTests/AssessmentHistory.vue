<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listPhysicalAssessments, startPhysicalAssessment } from '@/apis.js'
import { assessmentRoute, LABELS, resultText, physicalError } from '@/utils/physicalTests.js'
import AssessmentTrend from './AssessmentTrend.vue'
import { auth } from '@/stores/auth.js'

const props = defineProps({ participant: Object })
const router = useRouter()
const assessments = ref([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const draft = computed(() => assessments.value.find(row => row.status === 'draft'))
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
      <AssessmentTrend v-if="assessments.some(row => row.status === 'completed')" :assessments="assessments" />
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
