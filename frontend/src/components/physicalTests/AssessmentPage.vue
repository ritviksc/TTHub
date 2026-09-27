<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getPhysicalAssessment, updatePhysicalAssessmentDate, completePhysicalAssessment } from '@/apis.js'
import { GROUPS, LABELS, resultText, assessmentReady, physicalError } from '@/utils/physicalTests.js'
import ExerciseModal from './ExerciseModal.vue'

const route = useRoute()
const assessment = ref(null)
const date = ref('')
const loading = ref(true)
const error = ref('')
const success = ref('')
const saving = ref(false)
const selected = ref(null)
const ready = computed(() => assessment.value && assessmentReady(assessment.value.results))
const dateChanged = computed(() => date.value !== assessment.value?.assessed_on)
const readOnly = computed(() => assessment.value?.status === 'completed')
let loadSequence = 0
async function load() {
  const sequence = ++loadSequence
  loading.value = true
  error.value = ''
  success.value = ''
  selected.value = null
  assessment.value = null
  try {
    const data = await getPhysicalAssessment(route.params.id)
    if (sequence === loadSequence) { assessment.value = data; date.value = data.assessed_on }
  } catch (e) { if (sequence === loadSequence) error.value = physicalError(e) }
  finally { if (sequence === loadSequence) loading.value = false }
}
watch(() => route.params.id, load, { immediate: true })
async function changeDate() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    assessment.value = await updatePhysicalAssessmentDate(assessment.value.id, date.value, assessment.value.version)
    success.value = 'Assessment date saved.'
  } catch (e) { error.value = physicalError(e) }
  finally { saving.value = false }
}
async function complete() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    assessment.value = await completePhysicalAssessment(assessment.value.id, assessment.value.version)
    success.value = 'Assessment completed. Results are now read-only.'
  } catch (e) { error.value = physicalError(e) }
  finally { saving.value = false }
}
function saved(data) {
  assessment.value = data
  selected.value = null
  success.value = 'Exercise results saved to the draft.'
}
</script>

<template>
  <div class="dash-page"><main class="content">
    <p v-if="loading" class="loading-note">Loading assessment…</p>
    <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    <button v-if="error" class="btn-cancel" :disabled="saving" @click="load">Reload saved assessment</button>
    <template v-if="assessment">
      <RouterLink class="back-link" :to="{ name: 'participant-detail', params: { id: assessment.participant } }">← Participant profile</RouterLink>
      <div class="page-header"><div>
        <h1>{{ assessment.participant_name }} — Physical assessment</h1>
        <p class="page-subtitle">{{ readOnly ? 'Completed assessment' : 'Draft — save each exercise group, then complete the assessment.' }}</p>
      </div></div>
      <p v-if="success" class="form-success" role="status">{{ success }}</p>
      <form class="date-form" @submit.prevent="changeDate">
        <div class="form-group"><label for="assessment-date">Assessment date</label>
          <input id="assessment-date" v-model="date" type="date" required :disabled="readOnly || saving" />
        </div>
        <button v-if="!readOnly" class="btn-cancel" :disabled="saving || !dateChanged">Save date</button>
      </form>
      <p v-if="dateChanged" class="loading-note">Save the date before recording results or completing.</p>
      <div class="exercise-grid">
        <section v-for="group in GROUPS" :key="group.key" class="card">
          <h2>{{ group.title }}</h2>
          <p v-for="exercise in group.exercises" :key="exercise">
            <strong>{{ LABELS[exercise] }}:</strong> {{ resultText(assessment.results.find(row => row.exercise === exercise)) }}
          </p>
          <button v-if="!readOnly" class="btn-primary" :disabled="saving || dateChanged" @click="selected = group">Record / edit results</button>
          <a v-else :href="`/testing-guides/${group.guide}`" target="_blank" rel="noopener">Testing guide (PDF)</a>
        </section>
      </div>
      <section v-if="!readOnly" class="card">
        <h2>Complete assessment</h2>
        <p>Check the date and all results before completing. Valid stopped-test outcomes count as recorded; “not attempted” leaves the assessment incomplete. Later balance stages skipped under the stopping rule are allowed. Completion does not mean the participant passed every exercise.</p>
        <p>Completed assessments cannot be edited.</p>
        <button class="btn-primary" :disabled="saving || !ready || dateChanged" @click="complete">{{ saving ? 'Saving…' : 'Complete assessment' }}</button>
      </section>
      <section v-if="assessment.results.length" class="card observations">
        <h2>Saved observations</h2>
        <div v-for="row in assessment.results" :key="row.exercise">
          <p v-if="row.notes || row.walking_aid"><strong>{{ LABELS[row.exercise] }}:</strong> {{ row.notes }} <span v-if="row.walking_aid">Walking aid: {{ row.walking_aid }}</span></p>
        </div>
        <p>Started by {{ assessment.recorded_by_name || 'staff member' }}.</p>
      </section>
      <ExerciseModal v-if="selected" :key="selected.key" :group="selected" :assessment="assessment" @close="selected = null" @saved="saved" />
    </template>
  </main></div>
</template>

<style scoped>
.exercise-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 24px 0; }
.date-form { display: flex; flex-wrap: wrap; gap: 16px; align-items: center; }
.observations { margin-top: 20px; }
</style>
