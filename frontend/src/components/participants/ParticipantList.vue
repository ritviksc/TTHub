<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { createParticipant, listParticipants } from '@/apis.js'
import { auth } from '@/stores/auth.js'
import { programmeToday } from '@/utils/sessions.js'

const router = useRouter()

const participants = ref([])
const loading = ref(true)
const error = ref('')
const search = ref('')
const canEnrol = computed(() => ['branch_manager', 'instructor'].includes(auth.user?.role))
const canRecordGpConsent = computed(() => auth.user?.role === 'branch_manager')
const enrolmentDialog = ref(null)
const newParticipant = ref({})
const saving = ref(false)
const createError = ref('')
const fieldErrors = ref({})
const fields = [
  { name: 'first_name', label: 'First name', required: true, max: 150 },
  { name: 'last_name', label: 'Last name', required: true, max: 150 },
  { name: 'preferred_name', label: 'Preferred name', max: 150 },
  { name: 'date_of_birth', label: 'Date of birth', type: 'date' },
  { name: 'email', label: 'Email', type: 'email', max: 254 },
  { name: 'phone', label: 'Phone', type: 'tel', max: 30 },
  { name: 'emergency_contact_name', label: 'Emergency contact name', max: 255 },
  { name: 'emergency_contact_phone', label: 'Emergency contact phone', type: 'tel', max: 30 },
  { name: 'joined_on', label: 'Date joined', type: 'date' },
]

function openEnrolment() {
  newParticipant.value = Object.fromEntries(fields.map(field => [field.name, '']))
  Object.assign(newParticipant.value, { joined_on: programmeToday(), gp_consent_given: false, gp_consent_date: '' })
  createError.value = ''
  fieldErrors.value = {}
  enrolmentDialog.value.showModal()
}

function closeEnrolment() {
  if (!saving.value) enrolmentDialog.value.close()
}

async function submitEnrolment() {
  if (saving.value) return
  createError.value = ''
  fieldErrors.value = {}
  if (!auth.user?.branch?.id) {
    createError.value = 'You must be assigned to a branch to enrol participants.'
    return
  }
  const payload = Object.fromEntries(fields.map(field => [field.name,
    field.type === 'date' ? newParticipant.value[field.name] || null : newParticipant.value[field.name].trim(),
  ]))
  if (canRecordGpConsent.value) {
    payload.gp_consent_given = newParticipant.value.gp_consent_given
    payload.gp_consent_date = payload.gp_consent_given ? newParticipant.value.gp_consent_date || null : null
  }
  saving.value = true
  let participant
  try {
    participant = await createParticipant(payload)
  } catch (e) {
    const data = e.response?.data
    if (data && typeof data === 'object') {
      fieldErrors.value = Object.fromEntries(Object.entries(data).map(([field, messages]) =>
        [field, Array.isArray(messages) ? messages.join(' ') : String(messages)],
      ))
    }
    createError.value = fieldErrors.value.detail || fieldErrors.value.non_field_errors || 'Could not enrol this participant. Check the details and try again.'
    return
  } finally {
    saving.value = false
  }
  participants.value.unshift(participant)
  closeEnrolment()
  await router.push({ name: 'participant-detail', params: { id: participant.id } })
}

const filteredParticipants = computed(() => {
  const query = search.value.toLowerCase().trim()

  if (!query) {
    return participants.value
  }

  return participants.value.filter(p => {
    return [p.preferred_name, p.full_name]
      .filter(Boolean)
      .some(name => name.toLowerCase().includes(query))
  })
})

function getName(participant) {
  return participant.preferred_name || participant.full_name
}

function getInitial(participant) {
  return getName(participant).charAt(0).toUpperCase()
}

async function loadParticipants() {
  loading.value = true
  error.value = ''

  try {
    const data = await listParticipants()

    if (Array.isArray(data)) {
      participants.value = data
    } else if (Array.isArray(data.results)) {
      participants.value = data.results
    } else if (Array.isArray(data.data)) {
      participants.value = data.data
    } else {
      participants.value = []
    }

  } catch (e) {
    error.value = 'Unable to load participants.'
  } finally {
    loading.value = false
  }
}

onMounted(loadParticipants)
</script>

<template>
  <div class="dash-page">
    <dialog ref="enrolmentDialog" class="modal enrolment-dialog" aria-labelledby="enrolment-title" @cancel.prevent="closeEnrolment">
      <form @submit.prevent="submitEnrolment">
        <h2 id="enrolment-title">Enrol participant</h2>
        <p>Branch: {{ auth.user?.branch?.name || 'No branch assigned' }}</p>
        <fieldset :disabled="saving">
          <div class="form-row">
            <div v-for="field in fields" :key="field.name" class="form-group">
              <label :for="`enrol-${field.name}`">{{ field.label }}</label>
              <input :id="`enrol-${field.name}`" v-model="newParticipant[field.name]" :type="field.type || 'text'" :required="field.required" :maxlength="field.max" :max="field.name === 'date_of_birth' ? programmeToday() : undefined" :aria-invalid="!!fieldErrors[field.name]" :aria-describedby="fieldErrors[field.name] ? `enrol-error-${field.name}` : undefined" :autofocus="field.name === 'first_name'" />
              <p v-if="fieldErrors[field.name]" :id="`enrol-error-${field.name}`" class="form-error">{{ fieldErrors[field.name] }}</p>
            </div>
          </div>
          <template v-if="canRecordGpConsent">
            <p><label><input v-model="newParticipant.gp_consent_given" type="checkbox" /> GP consent recorded</label></p>
            <p v-if="fieldErrors.gp_consent_given" class="form-error">{{ fieldErrors.gp_consent_given }}</p>
            <div v-if="newParticipant.gp_consent_given" class="form-group">
              <label for="enrol-gp-date">Date GP consent was given</label>
              <input id="enrol-gp-date" v-model="newParticipant.gp_consent_date" type="date" :max="programmeToday()" required :aria-invalid="!!fieldErrors.gp_consent_date" :aria-describedby="fieldErrors.gp_consent_date ? 'enrol-error-gp-date' : undefined" />
              <p v-if="fieldErrors.gp_consent_date" id="enrol-error-gp-date" class="form-error">{{ fieldErrors.gp_consent_date }}</p>
            </div>
          </template>
          <p>Photos and supporting documents can be added to the participant's record after enrolment.</p>
          <p v-if="createError" class="form-error" role="alert">{{ createError }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closeEnrolment">Cancel</button>
            <button type="submit" class="btn-primary">{{ saving ? 'Enrolling…' : 'Enrol participant' }}</button>
          </div>
        </fieldset>
      </form>
    </dialog>

    <main class="content">

      <div class="page-header">

        <div>
          <h1>Participants</h1>

          <p class="page-subtitle">
            Participants enrolled at your branch.
          </p>
        </div>

        <div class="participant-count">
          {{ participants.length }} participants
        </div>
        <button v-if="canEnrol" class="btn-primary" @click="openEnrolment">+ Enrol participant</button>

      </div>

      <div class="search-box">

        <input
          v-model="search"
          type="text"
          placeholder="Search participants..."
        />

      </div>

      <div
        v-if="loading"
        class="message"
      >
        Loading participants...
      </div>

      <div
        v-else-if="error"
        class="error"
      >
        {{ error }}

        <button
          class="retry"
          @click="loadParticipants"
        >
          Try again
        </button>
      </div>

      <div
        v-else-if="filteredParticipants.length === 0"
        class="message"
      >
        <template v-if="!participants.length">
          <h3>No participants yet</h3>
          <p>There are no participants enrolled at your branch yet.</p>
        </template>
        <template v-else>
          <h3>No participants found</h3>
          <p>No participants match your search term "{{ search.trim() }}".</p>
          <button class="btn-primary" @click="search = ''">Show all participants</button>
        </template>
      </div>

      <div
        v-else
        class="participants-list"
      >

        <div
          v-for="participant in filteredParticipants"
          :key="participant.id"
          class="participant-row"
        >

          <div class="avatar">

            <img
              v-if="
                participant.photo ||
                participant.photo_url
              "
              :src="
                participant.photo ||
                participant.photo_url
              "
              alt=""
            />

            <span v-else>
              {{ getInitial(participant) }}
            </span>

          </div>

          <div class="participant-details">

            <RouterLink :to="{ name: 'participant-detail', params: { id: participant.id } }" class="participant-name">
              {{ getName(participant) }}
            </RouterLink>

            <span v-if="participant.preferred_name && participant.preferred_name !== participant.full_name">
              {{ participant.full_name }}
            </span>

          </div>

          <span
            class="status"
            :class="{
              inactive:
                participant.is_active === false
            }"
          >
            {{
              participant.is_active === false
                ? 'Inactive'
                : 'Active'
            }}
          </span>

        </div>

      </div>

    </main>

  </div>
</template>

<style scoped>
.enrolment-dialog { border: none; max-width: calc(100vw - 32px); max-height: 85vh; overflow-y: auto; color: var(--text); }
.enrolment-dialog::backdrop { background: var(--ink); opacity: 0.6; }
.enrolment-dialog fieldset { border: 0; margin: 0; padding: 0; min-width: 0; }
@media (max-width: 560px) {
  .enrolment-dialog .form-row { grid-template-columns: 1fr; }
}

.participant-count {
  color: var(--text-muted);
  font-size: var(--text-base);
}

.search-box {
  margin: 20px 0;
}

.search-box input {
  width: 100%;
  box-sizing: border-box;
  padding: 11px 18px;
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius-pill);
  background: var(--surface);
  font-size: var(--text-base);
  color: var(--text);
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.search-box input:focus {
  border-color: var(--teal);
  box-shadow: 0 0 0 3px var(--teal-tint);
}

.participants-list {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.participant-row {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-faint);
  transition: background-color 0.15s ease;
}

.participant-row:hover {
  background: var(--surface-sunken);
}

.participant-row:last-child {
  border-bottom: none;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--teal-tint);
  color: var(--teal-dark);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
  border: 1px solid rgba(13, 130, 135, 0.2);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.participant-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.participant-details span {
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.participant-name {
  color: var(--text);
  font-weight: 600;
  text-decoration: none;
  transition: color 0.15s ease;
}

.participant-name:hover {
  color: var(--maroon);
}

.status {
  color: var(--success);
  font-size: var(--text-sm);
  font-weight: 600;
}

.status.inactive {
  color: var(--text-muted);
}

.message {
  background: var(--surface);
  padding: 48px 24px;
  text-align: center;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  color: var(--text-muted);
}

.error {
  padding: 16px 20px;
  background: var(--danger-bg);
  color: var(--danger);
  border: 1px solid rgba(184, 46, 36, 0.2);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.retry {
  padding: 6px 14px;
  cursor: pointer;
  background: var(--surface);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text);
  transition: all 0.15s ease;
}

.retry:hover {
  background: var(--surface-sunken);
  border-color: var(--text-muted);
}
</style>
