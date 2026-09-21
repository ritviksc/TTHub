<script setup>
import { ref } from 'vue'
import { createSession } from '@/apis.js'
import { programmeToday } from '@/utils/sessions.js'

const emit = defineEmits(['close', 'created'])

const form = ref({ date: '', time: '', activity: '' })
const error = ref('')
const saving = ref(false)
const minimumDate = ref(programmeToday())
const ACTIVITIES = ['Standard strength and mobility training', 'Fitness test']

// Recheck at submission in case the modal has stayed open across midnight.
async function submit() {
  error.value = ''
  minimumDate.value = programmeToday()
  if (form.value.date < minimumDate.value) {
    error.value = 'Session date cannot be in the past.'
    return
  }
  saving.value = true
  try {
    emit('created', await createSession(form.value))
  } catch (e) {
    error.value = e.response?.data?.date?.[0] ?? e.response?.data?.detail
      ?? 'Could not create this session. Check the server is running and try again.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <form class="modal" @submit.prevent="submit">
      <h2>Create new session</h2>

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

      <div v-if="error" class="form-error">{{ error }}</div>

      <div class="modal-actions">
        <button type="button" class="btn-cancel" @click="emit('close')">Cancel</button>
        <button type="submit" class="btn-primary" :disabled="saving">
          {{ saving ? 'Creating…' : 'Create session' }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
/* dashboard.css fixes the modal at 480px; keep it inside the screen on phones. */
.modal { max-width: calc(100% - 32px); }

@media (max-width: 560px) {
  .form-row { grid-template-columns: 1fr; }
}
</style>
