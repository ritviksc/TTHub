<script setup>
import { ref } from 'vue'
import { createSession } from '@/apis.js'

const emit = defineEmits(['close', 'created'])

const form = ref({ name: '', date: '', time: '', activity: '' })
const error = ref('')
const saving = ref(false)

// Blank fields are caught by the inputs' `required`, so this only handles save failures.
async function submit() {
  saving.value = true
  error.value = ''
  try {
    emit('created', await createSession(form.value))
  } catch (e) {
    error.value = e.response?.data?.detail
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

      <div class="form-group">
        <label for="session-name">Session name</label>
        <input id="session-name" v-model.trim="form.name" placeholder="Thursday morning class" required />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="session-date">Date</label>
          <input id="session-date" v-model="form.date" type="date" required />
        </div>
        <div class="form-group">
          <label for="session-time">Time</label>
          <input id="session-time" v-model="form.time" type="time" required />
        </div>
      </div>

      <div class="form-group">
        <label for="session-activity">Activity</label>
        <input id="session-activity" v-model.trim="form.activity" placeholder="Strength and mobility" required />
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
