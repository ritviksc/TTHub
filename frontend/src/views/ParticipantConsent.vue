<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getParticipant, updateParticipant } from '@/apis.js'

const route = useRoute()
const participantId = route.params.id

const participant = ref(null)
const photoFile = ref(null)
const photoConsentGiven = ref(false)
const gpConsentGiven = ref(false)
const gpConsentDate = ref('')
const error = ref('')
const success = ref('')

onMounted(async () => {
  participant.value = await getParticipant(participantId)
  photoConsentGiven.value = participant.value.photo_consent_given
  gpConsentGiven.value = participant.value.gp_consent_given
  gpConsentDate.value = participant.value.gp_consent_date ?? ''
})

function onFileChange(e) {
  photoFile.value = e.target.files[0] ?? null
}

async function submit() {
  error.value = ''
  success.value = ''

  const formData = new FormData()
  formData.append('photo_consent_given', photoConsentGiven.value)
  formData.append('gp_consent_given', gpConsentGiven.value)
  if (gpConsentDate.value) formData.append('gp_consent_date', gpConsentDate.value)
  if (photoFile.value) formData.append('photo', photoFile.value)

  try {
    participant.value = await updateParticipant(participantId, formData)
    success.value = 'Saved.'
    photoFile.value = null
  } catch (e) {
    const data = e.response?.data
    error.value = data ? Object.values(data).flat().join(' ') : 'Could not save changes.'
  }
}
</script>

<template>
  <div v-if="participant">
    <h2>{{ participant.full_name }}</h2>

    <img v-if="participant.photo" :src="participant.photo" alt="" style="max-width: 150px" />

    <form @submit.prevent="submit">
      <fieldset>
        <legend>GP consent</legend>
        <label><input type="checkbox" v-model="gpConsentGiven" /> Consent given</label>
        <label>Date: <input type="date" v-model="gpConsentDate" /></label>
      </fieldset>

      <fieldset>
        <legend>Photo consent</legend>
        <label><input type="checkbox" v-model="photoConsentGiven" /> Consent given</label>
        <input type="file" accept="image/*" @change="onFileChange" />
      </fieldset>

      <p v-if="error">{{ error }}</p>
      <p v-if="success">{{ success }}</p>
      <button type="submit">Save</button>
    </form>
  </div>
</template>