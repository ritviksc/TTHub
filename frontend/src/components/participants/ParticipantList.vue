<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
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
