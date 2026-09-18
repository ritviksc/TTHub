<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getParticipant, updateParticipant } from '@/apis.js'
import { auth } from '@/stores/auth.js'

const route = useRoute()
const router = useRouter()
const participantId = route.params.id

const participant = ref(null)
const photoFile = ref(null)
const photoConsentGiven = ref(false)
const photoConsentDate = ref('')
const gpConsentGiven = ref(false)
const gpConsentDate = ref('')
const loading = ref(true)
const loadError = ref('')
const error = ref('')
const success = ref('')

const canRecordGpConsent = computed(() => auth.user?.role !== 'instructor')

onMounted(async () => {
  try {
    participant.value = await getParticipant(participantId)
    photoConsentGiven.value = participant.value.photo_consent_given
    photoConsentDate.value = participant.value.photo_consent_date ?? ''
    gpConsentGiven.value = participant.value.gp_consent_given
    gpConsentDate.value = participant.value.gp_consent_date ?? ''
  } catch (e) {
    loadError.value = 'Could not load this participant.'
  } finally {
    loading.value = false
  }
})

function onFileChange(e) {
  photoFile.value = e.target.files[0] ?? null
}

async function submit() {
  error.value = ''
  success.value = ''

  const formData = new FormData()
  formData.append('photo_consent_given', photoConsentGiven.value)
  if (photoConsentGiven.value) formData.append('photo_consent_date', photoConsentDate.value)
  if (canRecordGpConsent.value) {
    formData.append('gp_consent_given', gpConsentGiven.value)
    if (gpConsentGiven.value) formData.append('gp_consent_date', gpConsentDate.value)
  }
  if (photoFile.value) formData.append('photo', photoFile.value)

  try {
    participant.value = await updateParticipant(participantId, formData)
    photoConsentDate.value = participant.value.photo_consent_date ?? ''
    gpConsentDate.value = participant.value.gp_consent_date ?? ''
    success.value = 'Saved.'
    photoFile.value = null
  } catch (e) {
    const data = e.response?.data
    error.value = data ? Object.values(data).flat().join(' ') : 'Could not save changes.'
  }
}
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <!--backk button: router.back() works regardless of which role is viewing-->
      <a class=""back-link" href="#" @click.prevent="router.back()">&lsaquo; Back</a>
      <p v-if="loading" class="loading-note">Loading participant…</p>
      <p v-else-if="loadError" class="form-error">{{ loadError }}</p>

      <div v-else-if="participant" class="consent-card">
        <div class="consent-header">
          <!--show photo if uploaded and consent given, otherwise show first initialas fallback-->
          <img v-if="participant.photo" :src="participant.photo" class="participant-photo" alt="" />
          <div v-else class="initials-avatar lg">{{ (participant.full_name || '?')[0] }}</div>
          <div>
            <h1>{{ participant.full_name }}</h1>
            <p v-if="participant.preferred_name" class="page-subtitle">Goes by {{ participant.preferred_name }}</p>
            <span :class="['status-badge', participant.is_active ? 'active' : 'inactive']">
              {{ participant.is_active ? 'Active' : 'Inactive' }}
            </span>          </div>
        </div>

        <!--profile info:all fields return by getParticipant() from backend
        v-if hides it cleanly if data is missing-->
        <section class="info-section">
          <h2>Details</h2>
          <dl class="info-grid">
          <div v-if="participant.date_of_birth"><dt>Date of birth</dt><dd>{{ participant.date_of_birth }}</dd></div>
          <div v-if="participant.phone"><dt>Phone</dt><dd>{{ participant.phone }}</dd></div>
          <div v-if="participant.email"><dt>Email</dt><dd>{{ participant.email }}</dd></div>
          <div><dt>Branch</dt><dd>{{ participant.branch_name }}</dd></div>
         </dl>
        </section>
        <!-- Only shown if an emergency contact name has been recorded -->
        <section v-if="participant.emergency_contact_name" class="info-section">
          <h2>Emergency contact</h2>
          <dl class="info-grid">
            <div><dt>Name</dt><dd>{{ participant.emergency_contact_name }}</dd></div>
            <div v-if="participant.emergency_contact_phone"><dt>Phone</dt><dd>{{ participant.emergency_contact_phone }}</dd></div>
          </dl>
        </section>

        <!-- Consent form: Instructors cannot record GP consent (enforced by canRecordGpConsent below) -->
        <section class="info-section">
          <h2>Consents</h2>
        
        <form @submit.prevent="submit">
          <fieldset v-if="canRecordGpConsent" class="consent-group">
            <legend>GP consent</legend>
            <label><input type="checkbox" v-model="gpConsentGiven" /> Consent given</label>
            <label v-if="gpConsentGiven" class="date-field">
              Date given
              <input v-model="gpConsentDate" type="date" required />
            </label>
          </fieldset>

          <fieldset class="consent-group">
            <legend>Photo consent</legend>
            <label><input type="checkbox" v-model="photoConsentGiven" /> Consent given</label>
            <label v-if="photoConsentGiven" class="date-field">
              Date given
              <input v-model="photoConsentDate" type="date" required />
            </label>
            <label class="file-field">
              Photo
              <input type="file" accept="image/*" @change="onFileChange" />
            </label>
          </fieldset>

          <p v-if="error" class="form-error">{{ error }}</p>
          <p v-if="success" class="form-success">{{ success }}</p>
          <button type="submit" class="btn-primary">Save</button>
        </form>
        </section>section>
      </div>
    </main>
  </div>
</template>

    <!-- This is just css for the participant card, showing fields for consent and the photo. Can't inherit from main css since nowhere else has used a card -->
<style scoped>
/* Particpant detail sections:
info-grid uses autofit columns so it wraps nicely on smaller screens.
all colors come from theme.css tokens: nothing hardcoded.*/
.info-section { margin-bottom: 24px; }
.info-section h2 { font-size: var(--text-md); margin-bottom: 12px; }
.info-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px 24px; margin: 0;
}
.info-grid dt { font-size: var(--text-sm); font-weight: 600; color: var(--text-muted); margin-bottom: 2px; }
.info-grid dd { margin: 0; font-size: var(--text-base); color: var(--text); }
.consent-card {
  max-width: 620px;
  margin: 0 auto;
  padding: 28px;
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.consent-header { display: flex; align-items: center; gap: 18px; margin-bottom: 24px; }
.consent-header .page-subtitle { margin: 6px 0 0; }
.participant-photo { width: 96px; height: 96px; border-radius: 50%; object-fit: cover; }
.consent-group { margin: 0 0 20px; padding: 16px; border: 1px solid var(--border); border-radius: var(--radius-sm); }
.consent-group legend { padding: 0 6px; font-weight: 600; color: var(--text); }
.consent-group label { display: block; color: var(--text-secondary); margin: 8px 0; }
.date-field input, .file-field input { display: block; margin-top: 6px; }

@media (max-width: 560px) {
  .consent-card { padding: 20px; }
  .consent-header { align-items: flex-start; }
  .participant-photo { width: 64px; height: 64px; }
}
</style>
