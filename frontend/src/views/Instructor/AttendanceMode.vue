<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { getSession, updateAttendance } from '@/apis.js'
import { countByStatus, formatSessionDate, initials } from '@/utils/sessions.js'

const route = useRoute()
const router = useRouter()
const sessionId = route.params.id
const detailRoute = { name: 'in-session-detail', params: { id: sessionId } }

const session = ref(null)
const loading = ref(true)
const loadError = ref(null)
const saveError = ref(null)

const counts = computed(() => countByStatus(session.value?.attendance))

/* ---- load ---- */

async function load() {
  try {
    session.value = await getSession(sessionId)
  } catch (e) {
    loadError.value = e.response?.status === 404
      ? 'That session does not exist, or it has been deleted.'
      : 'Could not load this session.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

/* ---- marking ---- */

// Tapping flips present <-> absent, so a mis-tap is undone by tapping again.
async function toggle(record) {
  const status = record.status === 'present' ? 'absent' : 'present'
  saveError.value = null
  try {
    Object.assign(record, await updateAttendance(sessionId, record.participant_id, { status }))
  } catch (e) {
    saveError.value = `Could not update ${record.name}.`
  }
}

function cardLabel(record) {
  if (record.status === 'present') return '✓ Present'
  if (record.status === 'excused') return 'Excused'
  return 'Tap to mark present'
}
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <RouterLink :to="detailRoute" class="back-link">&lsaquo; Back to session</RouterLink>

      <div v-if="loadError" class="form-error">{{ loadError }}</div>
      <p v-else-if="loading" class="loading-note">Loading session…</p>

      <template v-else>
        <div class="page-header">
          <div>
            <h1>Attendance mode</h1>
            <p class="page-subtitle">{{ session.name }} · {{ formatSessionDate(session.date) }}</p>
          </div>
          <button class="btn-primary" @click="router.push(detailRoute)">Done</button>
        </div>

        <p class="counter"><strong>{{ counts.present }}</strong> / {{ counts.total }} present</p>

        <div v-if="saveError" class="form-error">{{ saveError }}</div>

        <div class="person-grid">
          <!-- Excused is set on purpose from the detail page, so it can't be tapped away here. -->
          <button
            v-for="record in session.attendance"
            :key="record.participant_id"
            type="button"
            :class="['person-card', record.status]"
            :disabled="record.status === 'excused'"
            @click="toggle(record)"
          >
            <span class="initials-avatar lg">{{ initials(record.name) }}</span>
            <span class="person-name">{{ record.name }}</span>
            <span class="person-status">{{ cardLabel(record) }}</span>
          </button>
        </div>

        <p v-if="!counts.total" class="loading-note">Nobody was on the roster when this session was created.</p>
      </template>
    </main>
  </div>
</template>

<style scoped>
.counter {
  font-size: var(--text-xl);
  color: var(--text-secondary);
  margin: 0 0 24px;
}
.counter strong { color: var(--text); }

.person-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.person-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 24px 16px;
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: var(--radius-xl);
  color: var(--text);
  font: inherit;
  cursor: pointer;
}
.person-card:hover:not(:disabled) { border-color: var(--maroon); }

.person-card.present { border-color: var(--success); background: var(--success-bg); }
.person-card.excused { opacity: 0.6; cursor: default; }

.person-name { font-weight: 600; }
.person-status { font-size: var(--text-sm); color: var(--text-muted); }
.person-card.present .person-status { color: var(--success); font-weight: 600; }
</style>
