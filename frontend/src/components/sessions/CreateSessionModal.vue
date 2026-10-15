<script setup>
import { ref, computed, watch } from 'vue'
import { createSession } from '@/apis.js'
import { programmeToday } from '@/utils/sessions.js'
import { auth } from '@/stores/auth.js'

const props = defineProps({
  initialDate: {
    type: String,
    default: '',
  },
  initialBranch: { type: String, default: '' },
  branches: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'created'])

const form = ref({
  branch: props.initialBranch,
  date: props.initialDate || '',
  time: '',
  activity: '',
})
const error = ref('')
const saving = ref(false)
const minimumDate = ref(programmeToday())
const isSuperAdmin = computed(() => auth.user?.role === 'super_admin')
const ACTIVITIES = ['Standard strength and mobility training', 'Fitness test']

watch(() => props.initialDate, (newDate) => {
  if (newDate) {
    form.value.date = newDate
  }
})

// Recheck at submission in case the modal has stayed open across midnight.
async function submit() {
  if (saving.value) return
  error.value = ''
  minimumDate.value = programmeToday()
  if (form.value.date < minimumDate.value) {
    error.value = 'Session date cannot be in the past.'
    return
  }
  if (isSuperAdmin.value && !props.branches.some(branch => branch.id === form.value.branch)) {
    error.value = 'Choose a branch for this session.'
    return
  }
  saving.value = true
  try {
    const { date, time, activity } = form.value
    const payload = { date, time, activity }
    if (isSuperAdmin.value) payload.branch = form.value.branch
    emit('created', await createSession(payload))
  } catch (e) {
    error.value = e.response?.data?.branch?.[0] ?? e.response?.data?.date?.[0] ?? e.response?.data?.detail
      ?? 'Could not create this session. Check the server is running and try again.'
  } finally {
    saving.value = false
  }
}

function close() {
  if (!saving.value) emit('close')
}
</script>

<template>
  <div class="modal-backdrop" @click.self="close">
    <form class="modal" @submit.prevent="submit">
      <h2>Create new session</h2>

      <fieldset :disabled="saving">
      <div v-if="isSuperAdmin" class="form-group">
        <label for="session-branch">Branch</label>
        <select id="session-branch" v-model="form.branch" required>
          <option value="" disabled>Choose a branch</option>
          <option v-for="branch in branches" :key="branch.id" :value="branch.id">{{ branch.name }}</option>
        </select>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="session-date">Date</label>
          <input id="session-date" v-model="form.date" type="date" :min="minimumDate" required @focus="minimumDate = programmeToday()" />
        </div>
        <div class="form-group">
          <label for="session-time">Time</label>
          <input id="session-time" v-model="form.time" type="time" required />
        </div>
      </div>

      <div class="form-group">
        <label for="session-activity">Activity</label>
        <select id="session-activity" v-model="form.activity" required>
          <option value="" disabled>Select an activity</option>
          <option v-for="activity in ACTIVITIES" :key="activity" :value="activity">{{ activity }}</option>
        </select>
      </div>

      <div v-if="error" class="form-error" role="alert">{{ error }}</div>

      <div class="modal-actions">
        <button type="button" class="btn-cancel" @click="close">Cancel</button>
        <button type="submit" class="btn-primary" :disabled="saving">
          {{ saving ? 'Creating…' : 'Create session' }}
        </button>
      </div>
      </fieldset>
    </form>
  </div>
</template>

<style scoped>
/* dashboard.css fixes the modal at 480px; keep it inside the screen on phones. */
.modal { max-width: calc(100% - 32px); }
fieldset { border: 0; padding: 0; margin: 0; min-width: 0; }

@media (max-width: 560px) {
  .form-row { grid-template-columns: 1fr; }
}
</style>
