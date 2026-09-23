<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { getSession, updateAttendance, setAttendanceFinalised } from '@/apis.js'
import { countByStatus, formatSessionDate, initials } from '@/utils/sessions.js'

const route = useRoute()
const router = useRouter()
const sessionId = route.params.id
const detailRoute = { name: 'in-session-detail', params: { id: sessionId } }

const session = ref(null)
const loading = ref(true)
const loadError = ref(null)
const saveError = ref(null)
const saving = ref(false)

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
  if (saving.value || session.value.attendance_finalised) return
  saving.value = true
  const status = record.status === 'present' ? 'absent' : 'present'
  saveError.value = null
  try {
    Object.assign(record, await updateAttendance(sessionId, record.id, { status }))
  } catch (e) {
    saveError.value = `Could not update ${record.name}.`
  } finally {
    saving.value = false
  }
}

async function setFinalised(finalised) {
  if (saving.value) return
  if (finalised && !counts.value.present &&
      !confirm('Nobody is marked present. Finalise this as an empty session?')) return
  saving.value = true
  saveError.value = null
  try {
    Object.assign(session.value, await setAttendanceFinalised(sessionId, finalised))
    if (finalised) await router.push(detailRoute)
  } catch {
    saveError.value = finalised
      ? 'Could not finalise attendance. Please try again.'
      : 'Could not reopen attendance. Please try again.'
  } finally {
    saving.value = false
  }
}

function cardLabel(record) {
  if (record.status === 'present') return '✓ Present'
  return session.value.attendance_finalised ? 'Absent' : 'Tap to mark present'
}

function participantName(record) {
  return `${record.first_name ?? ''} ${record.last_name ?? ''}`.trim() || record.name
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
            <p class="page-subtitle">{{ session.activity }} · {{ formatSessionDate(session.date) }}</p>
          </div>
          <button v-if="session.attendance_finalised" class="btn-primary" :disabled="saving" @click="setFinalised(false)">
            {{ saving ? 'Reopening…' : 'Reopen attendance' }}
          </button>
          <button v-else class="btn-primary" :disabled="saving" @click="setFinalised(true)">
            {{ saving ? 'Saving…' : 'Done' }}
          </button>
        </div>

        <p class="page-subtitle">{{ session.attendance_finalised ? 'Attendance finalised' : 'Attendance not finalised' }}</p>
        <p class="counter"><strong>{{ counts.present }}</strong> / {{ counts.total }} present</p>

        <div v-if="saveError" class="form-error">{{ saveError }}</div>

        <div class="person-list">
          <button
            v-for="record in session.attendance"
            :key="record.participant_id"
            type="button"
            :class="['person-row', record.status]"
            :aria-pressed="record.status === 'present'"
            :disabled="saving || session.attendance_finalised"
            @click="toggle(record)"
          >
            <img v-if="record.photo" :src="record.photo" class="participant-photo" alt="" />
            <span v-else class="initials-avatar">{{ initials(participantName(record)) }}</span>
            <span class="person-name">{{ participantName(record) }}</span>
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

.person-list { display: flex; flex-direction: column; gap: 10px; }

.person-row {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 12px 16px;
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-lg);
  color: var(--text);
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.person-row:hover { border-color: var(--maroon); }

.person-row.present { border-color: var(--success); background: var(--success-bg); }
.participant-photo { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; }

.person-name { flex: 1; font-weight: 600; }
.person-status { font-size: var(--text-sm); color: var(--text-muted); }
.person-row.present .person-status { color: var(--success); font-weight: 600; }
</style>
