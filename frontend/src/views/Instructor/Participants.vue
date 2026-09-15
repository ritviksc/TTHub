<script setup>
import { ref, computed, onMounted } from 'vue'
import { listParticipants } from '@/apis.js'

const participants = ref([])
const loading = ref(true)
const error = ref('')
const search = ref('')

const filteredParticipants = computed(() => {
  const query = search.value.toLowerCase().trim()

  if (!query) {
    return participants.value
  }

  return participants.value.filter(p => {
    const name =
      p.preferred_name ||
      p.preferredName ||
      p.name ||
      `${p.first_name || ''} ${p.last_name || ''}`

    return name.toLowerCase().includes(query)
  })
})

function getName(participant) {
  return (
    participant.preferred_name ||
    participant.preferredName ||
    participant.name ||
    `${participant.first_name || ''} ${participant.last_name || ''}`
  ).trim()
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

    console.log('Participants:', participants.value)
  } catch (e) {
    console.error(e)
    error.value = 'Unable to load participants.'
  } finally {
    loading.value = false
  }
}

onMounted(loadParticipants)
</script>

<template>
  <div class="dash-page">

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
        No participants found.
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

            <strong>
              {{ getName(participant) }}
            </strong>

            <span>
              ID: {{ participant.id }}
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

.participant-count {
  color: var(--text-muted);
  font-size: 14px;
}

.search-box {
  margin: 20px 0;
}

.search-box input {
  width: 100%;
  box-sizing: border-box;
  padding: 13px 15px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  font-size: 14px;
}

.participants-list {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.participant-row {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-faint);
}

.participant-row:last-child {
  border-bottom: none;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--teal-tint);
  color: var(--teal-dark);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
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
  font-size: 12px;
}

.status {
  color: var(--success);
  font-size: 13px;
  font-weight: 600;
}

.status.inactive {
  color: var(--text-muted);
}

.message {
  background: var(--surface);
  padding: 40px;
  text-align: center;
  border-radius: var(--radius-lg);
}

.error {
  padding: 20px;
  background: var(--error-bg);
  color: var(--error);
  border-radius: 8px;
}

.retry {
  margin-left: 10px;
  padding: 7px 12px;
  cursor: pointer;
}

</style>