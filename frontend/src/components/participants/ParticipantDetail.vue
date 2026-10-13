<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { getParticipant, updateParticipant, deactivateParticipant, reactivateParticipant, downloadGpDocument } from '@/apis.js'
import { initials, programmeToday } from '@/utils/sessions.js'
import ParticipantAttendance from './ParticipantAttendance.vue'
import AssessmentHistory from '@/components/physicalTests/AssessmentHistory.vue'
import DocumentList from '@/components/documents/DocumentList.vue'

const props = defineProps({
  participantId: { type: String, required: true },
  canRecordGpConsent: { type: Boolean, default: false },
  page: { type: String, default: 'combined' },
  routePrefix: { type: String, default: 'sa' },
})
const participant = ref(null)
const photoRevision = ref(0)
const form = ref({})
const loading = ref(true)
const loadError = ref('')
const error = ref('')
const success = ref('')
const saving = ref(false)
const maximumConsentDate = ref(programmeToday())
const downloading = ref(false)
const photoInput = ref(null)
const documentInput = ref(null)
const confirmStatusChange = ref(false)
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

function setParticipant(value) {
  participant.value = value
  form.value = { ...value }
  // The protected URL stays the same when a new photo replaces the old one.
  photoRevision.value++
}

onMounted(async () => {
  try {
    setParticipant(await getParticipant(props.participantId))
  } catch (e) {
    loadError.value = e.response?.data?.detail ?? 'Could not load this participant.'
  } finally {
    loading.value = false
  }
})

async function save() {
  error.value = success.value = ''
  maximumConsentDate.value = programmeToday()
  for (const consent of props.canRecordGpConsent ? ['gp', 'photo'] : ['photo']) {
    if (form.value[`${consent}_consent_given`] && form.value[`${consent}_consent_date`] > maximumConsentDate.value) {
      error.value = `${consent === 'gp' ? 'GP' : 'Photo'} consent date cannot be in the future.`
      return
    }
  }
  saving.value = true
  const payload = new FormData()
  for (const field of fields) payload.append(field.name, form.value[field.name] ?? '')
  payload.append('notes', form.value.notes ?? '')
  payload.append('photo_consent_given', form.value.photo_consent_given)
  payload.append('photo_consent_date', form.value.photo_consent_given ? form.value.photo_consent_date ?? '' : '')
  if (form.value.photo_consent_given && photoInput.value?.files[0]) payload.append('photo', photoInput.value.files[0])
  if (props.canRecordGpConsent) {
    payload.append('gp_consent_given', form.value.gp_consent_given)
    payload.append('gp_consent_date', form.value.gp_consent_given ? form.value.gp_consent_date ?? '' : '')
    if (documentInput.value?.files[0]) payload.append('gp_consent_document', documentInput.value.files[0])
  }
  try {
    setParticipant(await updateParticipant(props.participantId, payload))
    if (photoInput.value) photoInput.value.value = ''
    if (documentInput.value) documentInput.value.value = ''
    success.value = 'Participant saved.'
  } catch (e) {
    error.value = e.response?.data ? Object.values(e.response.data).flat().join(' ') : 'Could not save this participant.'
  } finally {
    saving.value = false
  }
}

async function download() {
  downloading.value = true
  error.value = ''
  try {
    const blob = await downloadGpDocument(props.participantId)
    const extension = { 'application/pdf': 'pdf', 'image/png': 'png', 'image/jpeg': 'jpg' }[blob.type] ?? 'bin'
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `gp-consent.${extension}`
    link.click()
    // Give the browser time to start the download before releasing its blob.
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch {
    error.value = 'Could not download the GP consent document.'
  } finally {
    downloading.value = false
  }
}

async function changeStatus() {
  if (saving.value) return
  const active = participant.value.is_active
  saving.value = true
  error.value = success.value = ''
  try {
    const result = await (active ? deactivateParticipant : reactivateParticipant)(props.participantId)
    participant.value.is_active = result.is_active
    confirmStatusChange.value = false
    success.value = active
      ? 'Participant deactivated. Their attendance history is retained.'
      : 'Participant reactivated. They can be included in new sessions.'
  } catch (e) {
    error.value = e.response?.data?.detail ?? `Could not ${active ? 'deactivate' : 'reactivate'} this participant.`
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="participant-detail">
    <p v-if="loading" class="loading-note">Loading participant…</p>
    <p v-else-if="loadError" class="form-error" role="alert">{{ loadError }}</p>
    <template v-else-if="participant">
      <header class="page-header">
        <div class="identity">
          <img v-if="participant.photo" :key="photoRevision" :src="participant.photo" class="participant-photo" alt="Participant photo" />
          <span v-else class="initials-avatar lg">{{ initials(participant.full_name) }}</span>
          <div>
            <h1>{{ participant.preferred_name || participant.full_name }}</h1>
            <p v-if="participant.preferred_name">{{ participant.full_name }}</p>
            <p>{{ participant.branch_name }}</p>
            <span :class="['status-badge', participant.is_active ? 'active' : 'inactive']">{{ participant.is_active ? 'Active' : 'Inactive' }}</span>
          </div>
        </div>
        <nav v-if="page !== 'combined'" class="participant-navigation" aria-label="Participant pages">
          <RouterLink :to="{ name: `${routePrefix}-participant-detail`, params: { id: participantId } }" :class="page === 'details' ? 'btn-primary' : 'btn-cancel'" :aria-current="page === 'details' ? 'page' : undefined">Details</RouterLink>
          <RouterLink :to="{ name: `${routePrefix}-participant-attendance`, params: { id: participantId } }" :class="page === 'attendance' ? 'btn-primary' : 'btn-cancel'" :aria-current="page === 'attendance' ? 'page' : undefined">Attendance history</RouterLink>
        </nav>
      </header>
      <AssessmentHistory v-if="page !== 'attendance'" :participant="participant" />
      <form v-if="page !== 'attendance'" class="card" @submit.prevent="save">
        <fieldset :disabled="saving">
          <legend><h2>Participant details</h2></legend>
          <div class="form-row">
            <div v-for="field in fields" :key="field.name" class="form-group">
              <label :for="field.name">{{ field.label }}</label>
              <input :id="field.name" v-model="form[field.name]" :type="field.type || 'text'" :required="field.required" :maxlength="field.max" />
            </div>
          </div>
          <div class="form-group">
            <label for="notes">General notes (not a clinical record)</label>
            <textarea id="notes" v-model="form.notes" rows="3" />
          </div>
          <section class="consent-section">
            <h2>GP consent</h2>
            <template v-if="canRecordGpConsent">
              <p><label><input v-model="form.gp_consent_given" type="checkbox" /> Consent recorded</label></p>
              <div v-if="form.gp_consent_given" class="form-group">
                <label for="gp-date">Date given</label>
                <input id="gp-date" v-model="form.gp_consent_date" type="date" :max="maximumConsentDate" required @focus="maximumConsentDate = programmeToday()" />
              </div>
              <div class="form-group">
                <label for="gp-document">{{ participant.gp_document_available ? 'Replace supporting document' : 'Supporting document (optional)' }}</label>
                <input id="gp-document" ref="documentInput" type="file" accept=".pdf,.jpg,.jpeg,.png" aria-describedby="gp-help" />
                <p id="gp-help">PDF, JPG or PNG, up to 10 MB. Attaching a file does not record consent automatically.</p>
              </div>
              <template v-if="participant.gp_document_available">
                <button type="button" class="btn-cancel" :disabled="downloading" @click="download">{{ downloading ? 'Downloading…' : 'Download GP document' }}</button>
                <p v-if="participant.gp_document_uploaded_at">Uploaded {{ new Date(participant.gp_document_uploaded_at).toLocaleString('en-NZ') }}<template v-if="participant.gp_document_uploader"> by {{ participant.gp_document_uploader }}</template>.</p>
              </template>
              <p v-else>No supporting document attached.</p>
            </template>
            <p v-else>{{ participant.gp_consent_given ? 'Consent recorded' : 'Consent not recorded' }}<template v-if="participant.gp_consent_given && participant.gp_consent_date"> — {{ participant.gp_consent_date }}</template>.</p>
          </section>
          <section class="consent-section">
            <h2>Photo consent</h2>
            <p><label><input v-model="form.photo_consent_given" type="checkbox" /> Consent recorded</label></p>
            <div v-if="form.photo_consent_given" class="form-group">
              <label for="photo-date">Date given</label>
              <input id="photo-date" v-model="form.photo_consent_date" type="date" :max="maximumConsentDate" required @focus="maximumConsentDate = programmeToday()" />
            </div>
            <div class="form-group">
              <label for="photo">Participant photo</label>
              <input id="photo" ref="photoInput" type="file" accept="image/*" :disabled="!form.photo_consent_given" />
            </div>
            <p>The photo is shown only while photo consent is recorded.</p>
          </section>
          <button type="submit" class="btn-primary">{{ saving ? 'Saving…' : 'Save participant' }}</button>
        </fieldset>
      </form>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <p v-if="success" class="form-success" role="status">{{ success }}</p>
      <section v-if="page !== 'attendance'" class="card">
        <h2>Documents</h2>
        <DocumentList :participant-id="participantId" can-upload />
      </section>
      <ParticipantAttendance v-if="page !== 'details'" :participant-id="participantId" />
      <section v-if="page !== 'attendance'" class="card">
        <h2>Participant status</h2>
        <p v-if="participant.is_active">Deactivating prevents inclusion in new sessions and preserves existing attendance history.</p>
        <p v-else>Reactivating allows this participant to be included in new sessions. Their attendance history is retained.</p>
        <template v-if="confirmStatusChange">
          <p>{{ participant.is_active ? 'Deactivate' : 'Reactivate' }} {{ participant.full_name }}?</p>
          <button class="btn-primary" :disabled="saving" @click="changeStatus">{{ saving ? 'Saving…' : participant.is_active ? 'Confirm deactivation' : 'Confirm reactivation' }}</button>
          <button class="btn-cancel" :disabled="saving" @click="confirmStatusChange = false">Cancel</button>
        </template>
        <button v-else :class="participant.is_active ? 'btn-cancel' : 'btn-primary'" :disabled="saving" @click="confirmStatusChange = true">{{ participant.is_active ? 'Deactivate participant' : 'Reactivate participant' }}</button>
      </section>
    </template>
  </div>
</template>

<style scoped>
.participant-detail { max-width: 900px; margin: 0 auto; }
.page-header { flex-wrap: wrap; gap: 20px; }
.participant-navigation { display: flex; flex-wrap: wrap; gap: 8px; }
.participant-navigation a { text-decoration: none; }
.identity { display: flex; align-items: center; gap: 20px; }
.identity p { margin: 6px 0; color: var(--text-secondary); }
.participant-photo { width: 96px; height: 96px; border-radius: 50%; object-fit: cover; }
.card { margin-bottom: 24px; }
fieldset { border: 0; margin: 0; padding: 0; min-width: 0; }
legend { margin-bottom: 20px; }
.consent-section { margin: 24px 0; padding-top: 20px; border-top: 1px solid var(--border); }
textarea { padding: 10px; border: 1px solid var(--border-strong); border-radius: var(--radius-sm); font: inherit; color: var(--text); background: var(--surface); }
button:disabled { opacity: 0.6; cursor: wait; }
@media (max-width: 560px) {
  .form-row { grid-template-columns: 1fr; }
  .identity { align-items: flex-start; }
}
</style>
