<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { getSession, updateAttendance, setAttendanceFinalised } from '@/apis.js'
import { ABSENCE_REASONS, countByStatus, formatSessionDate, initials } from '@/utils/sessions.js'
import { auth } from '@/stores/auth.js'

const route = useRoute()
const router = useRouter()
const sessionId = route.params.id
const detailRoute = computed(() => ({
  name: auth.user?.role === 'branch_manager' ? 'bm-session-detail' : 'in-session-detail',
  params: { id: sessionId },
}))

const session = ref(null)
const loading = ref(true)
const loadError = ref(null)
const saveError = ref(null)
const saving = ref(false)
const reasonDrafts = ref({})
const reviewing = computed(() => route.query.review === '1' && session.value?.attendance_finalised === true)

const counts = computed(() => countByStatus(session.value?.attendance))

/* ---- load ---- */

async function load() {
  try {
    session.value = await getSession(sessionId)
    for (const record of session.value.attendance) resetReason(record)
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

function resetReason(record) {
  reasonDrafts.value[record.id] = {
    absence_reason: record.absence_reason || '',
    absence_reason_other: record.absence_reason_other || '',
  }
}

async function persistReason(record) {
  const draft = reasonDrafts.value[record.id]
  const changes = {
    absence_reason: draft.absence_reason,
    absence_reason_other: draft.absence_reason === 'other' ? draft.absence_reason_other.trim() : '',
  }
  if (changes.absence_reason === 'other' && !changes.absence_reason_other) {
    throw new Error(`Describe the other absence reason for ${participantName(record)}.`)
  }
  if (changes.absence_reason !== (record.absence_reason || '') ||
      changes.absence_reason_other !== (record.absence_reason_other || '')) {
    try {
      Object.assign(record, await updateAttendance(sessionId, record.id, changes))
    } catch {
      throw new Error(`Could not save the absence reason for ${participantName(record)}. Please try again.`)
    }
  }
  resetReason(record)
}

async function saveReason(record) {
  if (saving.value || !reviewing.value || record.status !== 'absent') return
  saving.value = true
  saveError.value = null
  try { await persistReason(record) }
  catch (e) { saveError.value = e.message }
  finally { saving.value = false }
}

// Tapping flips present <-> absent, so a mis-tap is undone by tapping again.
async function toggle(record) {
  if (saving.value || session.value.attendance_finalised) return
  saving.value = true
  const status = record.status === 'present' ? 'absent' : 'present'
  saveError.value = null
  try {
    Object.assign(record, await updateAttendance(sessionId, record.id, { status }))
    resetReason(record)
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
    if (reviewing.value) {
      for (const record of session.value.attendance.filter(r => r.status === 'absent')) {
        await persistReason(record)
      }
    }
    Object.assign(session.value, await setAttendanceFinalised(sessionId, finalised))
    if (finalised) await router.push(detailRoute.value)
  } catch (e) {
    saveError.value = e.message || (finalised
      ? 'Could not finalise attendance. Please try again.'
      : 'Could not reopen attendance. Please try again.')
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
            <h1>{{ reviewing ? 'Review attendance' : 'Attendance mode' }}</h1>
            <p class="page-subtitle">{{ session.activity }} · {{ formatSessionDate(session.date) }}</p>
          </div>
          <div class="attendance-actions">
            <button v-if="session.attendance_finalised" class="btn-cancel" :disabled="saving" @click="setFinalised(false)">
              {{ saving ? 'Reopening…' : 'Reopen attendance' }}
            </button>
            <button v-if="reviewing || !session.attendance_finalised" class="btn-primary" :disabled="saving" @click="setFinalised(true)">
              {{ saving ? 'Saving…' : 'Done' }}
            </button>
          </div>
        </div>

        <p class="page-subtitle">{{ session.attendance_finalised ? 'Attendance finalised' : 'Attendance not finalised' }}</p>
        <p class="counter"><strong>{{ counts.present }}</strong> / {{ counts.total }} present</p>

        <div v-if="saveError" class="form-error">{{ saveError }}</div>

        <div class="person-list">
          <div v-for="record in session.attendance" :key="record.participant_id">
          <button
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
          <form v-if="reviewing && record.status === 'absent'" class="absence-form" @submit.prevent="saveReason(record)">
            <fieldset :disabled="saving">
              <label :for="`reason-${record.id}`">Absence reason for {{ participantName(record) }}</label>
              <select :id="`reason-${record.id}`" v-model="reasonDrafts[record.id].absence_reason">
                <option value="">Select reason</option>
                <option v-for="reason in ABSENCE_REASONS" :key="reason.value" :value="reason.value">{{ reason.label }}</option>
              </select>
              <template v-if="reasonDrafts[record.id].absence_reason === 'other'">
                <label :for="`other-${record.id}`">Describe the reason</label>
                <input :id="`other-${record.id}`" v-model="reasonDrafts[record.id].absence_reason_other" type="text" required />
              </template>
              <button type="submit" class="btn-primary">Save reason</button>
            </fieldset>
          </form>
          </div>
        </div>

        <p v-if="!counts.total" class="loading-note">Nobody was on the roster when this session was created.</p>
      </template>
    </main>
  </div>
</template>

<style scoped>
.attendance-actions { display: flex; flex-wrap: wrap; gap: 10px; }

.counter {
  font-size: var(--text-xl);
  color: var(--text-secondary);
  margin: 0 0 24px;
}
.counter strong { color: var(--text); }

.absence-form {
  padding: 12px 16px;
  background: var(--surface-sunken);
  border-radius: var(--radius-md);
  margin-top: 6px;
}
.absence-form fieldset {
  border: 0;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
.absence-form select,
.absence-form input {
  padding: 8px 12px;
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font: inherit;
  max-width: 100%;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.absence-form select:focus,
.absence-form input:focus {
  border-color: var(--teal);
  box-shadow: 0 0 0 3px var(--teal-tint);
}

.person-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.person-row {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 14px 18px;
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-lg);
  color: var(--text);
  font: inherit;
  text-align: left;
  cursor: pointer;
  box-shadow: var(--shadow-card);
  transition: all 0.15s ease;
}
.person-row:hover {
  border-color: var(--teal);
  transform: translateY(-1px);
  box-shadow: var(--shadow-panel);
}

.person-row.present {
  border-color: var(--success);
  background: var(--success-bg);
  box-shadow: 0 1px 4px rgba(35, 108, 60, 0.15);
}
.participant-photo {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid rgba(13, 130, 135, 0.2);
}

.person-name {
  flex: 1;
  font-weight: 600;
  font-size: var(--text-md);
}
.person-status {
  font-size: var(--text-sm);
  color: var(--text-muted);
}
.person-row.present .person-status {
  color: var(--success);
  font-weight: 600;
}
</style>
