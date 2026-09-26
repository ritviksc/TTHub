<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { savePhysicalResults } from '@/apis.js'
import { LABELS, OUTCOMES, emptyResult, balanceBlocked, resultPayload, physicalError } from '@/utils/physicalTests.js'

const props = defineProps({ group: Object, assessment: Object })
const emit = defineEmits(['close', 'saved'])
const dialog = ref(null)
const saving = ref(false)
const error = ref('')
const rows = ref(props.group.exercises.map(exercise => ({
  ...emptyResult(exercise), ...props.assessment.results.find(row => row.exercise === exercise),
})))
const previousFocus = document.activeElement
onMounted(() => dialog.value.showModal())
onBeforeUnmount(() => previousFocus?.focus())
function close() { if (!saving.value) emit('close') }
function blocked(index) { return props.group.key === 'balance' && balanceBlocked(rows.value, index) }
function options(row) {
  return ['measured', 'unable', 'not_attempted', ...(row.exercise === 'chair' ? ['arms_used'] : [])]
}
async function save() {
  saving.value = true
  error.value = ''
  try {
    emit('saved', await savePhysicalResults(props.assessment.id, props.group.key,
      resultPayload(rows.value, props.group.key), props.assessment.version))
  } catch (e) { error.value = physicalError(e) }
  finally { saving.value = false }
}
</script>

<template>
  <dialog ref="dialog" class="modal exercise-dialog" aria-labelledby="exercise-title" @cancel.prevent="close">
    <form @submit.prevent="save">
      <h2 id="exercise-title">{{ group.title }}</h2>
      <p>{{ group.setup }}</p>
      <ol><li v-for="step in group.steps" :key="step">{{ step }}</li></ol>
      <p class="safety-note"><strong>Safety:</strong> {{ group.safety }}</p>
      <p><a :href="`/testing-guides/${group.guide}`" target="_blank" rel="noopener">Read the full testing guide (PDF)</a></p>
      <fieldset :disabled="saving">
        <legend>Record results</legend>
        <section v-for="(row, index) in rows" :key="row.exercise" class="exercise-result">
          <h3>{{ LABELS[row.exercise] }}</h3>
          <p v-if="blocked(index)">Not attempted — earlier balance stage has not reached 10 seconds.</p>
          <template v-else>
            <div class="form-group">
              <label :for="`${row.exercise}-outcome`">Outcome</label>
              <select :id="`${row.exercise}-outcome`" v-model="row.outcome" required>
                <option value="skipped" disabled v-if="row.outcome === 'skipped'">Choose an outcome for this stage</option>
                <option v-for="outcome in options(row)" :key="outcome" :value="outcome">{{ OUTCOMES[outcome] }}</option>
              </select>
            </div>
            <div v-if="row.outcome === 'measured'" class="form-group">
              <label :for="`${row.exercise}-value`">{{ row.exercise === 'chair' ? 'Number of stands in 30 seconds' : 'Time (seconds)' }}</label>
              <input :id="`${row.exercise}-value`" v-model="row.value" type="number" required
                :min="row.exercise === 'tug' ? 0.01 : 0" :max="group.key === 'balance' ? 10 : undefined"
                :step="row.exercise === 'chair' ? 1 : 0.01" />
            </div>
            <p v-if="row.outcome === 'arms_used'">The recorded score will be 0 stands, with “Arms needed to stand” saved as the reason.</p>
            <div v-if="row.exercise === 'tug'" class="form-group">
              <label for="walking-aid">Walking aid used (optional)</label>
              <input id="walking-aid" v-model="row.walking_aid" maxlength="150" />
            </div>
            <div class="form-group">
              <label :for="`${row.exercise}-notes`">{{ ['unable', 'not_attempted'].includes(row.outcome) ? 'Reason (required)' : 'Observations (optional)' }}</label>
              <textarea :id="`${row.exercise}-notes`" v-model="row.notes" maxlength="2000" :required="['unable', 'not_attempted'].includes(row.outcome)" rows="2" />
            </div>
          </template>
        </section>
      </fieldset>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <div class="modal-actions">
        <button type="button" class="btn-cancel" :disabled="saving" @click="close">Cancel</button>
        <button class="btn-primary" :disabled="saving">{{ saving ? 'Saving…' : 'Save results' }}</button>
      </div>
      <p class="loading-note">Cancel discards changes in this popup. Previously saved results stay saved.</p>
    </form>
  </dialog>
</template>

<style scoped>
.exercise-dialog { border: none; max-width: calc(100vw - 48px); max-height: 85vh; overflow-y: auto; color: var(--text); }
.exercise-dialog::backdrop { background: var(--ink); opacity: 0.6; }
.exercise-dialog li { margin-bottom: 8px; }
.exercise-result { margin-bottom: 20px; }
.exercise-result h3 { margin-bottom: 12px; }
.safety-note { background: var(--teal-tint); padding: 12px; border-radius: var(--radius-sm); }
textarea { border: 1px solid var(--border-strong); border-radius: var(--radius-sm); padding: 8px; background: var(--surface); color: var(--text); font: inherit; }
fieldset { border: 0; padding: 0; }
legend { margin-bottom: 12px; font-weight: 600; }
</style>
