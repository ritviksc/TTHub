<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { getSession, updateAttendance, deleteSession } from '@/apis.js'
import {
  ATTENDANCE_STATUSES,
  ABSENCE_REASONS,
  countByStatus,
  formatSessionDate,
  initials,
} from '@/utils/sessions.js'
import { auth } from '@/stores/auth.js'

const route = useRoute()
const router = useRouter()
const sessionId = route.params.id

const session = ref(null)
const loading = ref(true)
const loadError = ref(null)
const saveError = ref(null)
const statusFilter = ref('all')
const isInstructor = computed(() => auth.user?.role === 'instructor')
const listRouteName = computed(() => isInstructor.value ? 'in-sessions' : 'bm-sessions')

const counts = computed(() => countByStatus(session.value?.attendance))

const stats = computed(() => [
  { label: 'Present', value: counts.value.present },
  { label: 'Absent', value: counts.value.absent },
  { label: 'Attendance rate', value: `${counts.value.rate}%` },
])

const filterOptions = computed(() => [
  { value: 'all', label: `All (${counts.value.total})` },
  ...ATTENDANCE_STATUSES.map(s => ({ value: s.value, label: `${s.label} (${counts.value[s.value]})` })),
])

const visibleAttendance = computed(() => {
  const records = session.value?.attendance ?? []
  return statusFilter.value === 'all'
    ? records
    : records.filter(r => r.status === statusFilter.value)
})

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

/* ---- attendance ---- */

// Copy back the saved record so the table shows what was stored (e.g. a cleared reason).
async function saveRecord(record, changes) {
  saveError.value = null
  try {
    Object.assign(record, await updateAttendance(sessionId, record.id, changes))
  } catch (e) {
    saveError.value = `Could not update ${record.name}.`
  }
}

function changeAbsenceReason(record, absenceReason) {
  if (absenceReason === 'other') {
    // Wait for the explanation before saving: the API requires both together.
    record.absence_reason = absenceReason
    record.absence_reason_other = ''
    return
  }
  saveRecord(record, { absence_reason: absenceReason, absence_reason_other: '' })
}

function absenceReasonLabel(record) {
  if (!record.absence_reason) return '—'
  if (record.absence_reason === 'other') return record.absence_reason_other || 'Other'
  return ABSENCE_REASONS.find(reason => reason.value === record.absence_reason)?.label ?? '—'
}

/* ---- delete ---- */

async function handleDelete() {
  if (!confirm('Delete this session? This cannot be undone.')) return

  try {
    await deleteSession(sessionId)
    router.push({ name: listRouteName.value })
  } catch (e) {
    saveError.value = 'Could not delete this session.'
  }
}
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <RouterLink :to="{ name: listRouteName }" class="back-link">&lsaquo; All sessions</RouterLink>

      <div v-if="loadError" class="form-error">{{ loadError }}</div>
      <p v-else-if="loading" class="loading-note">Loading session…</p>

      <template v-else>
        <div class="page-header">
          <div>
            <h1>{{ session.activity }}</h1>
            <p class="page-subtitle">
              {{ formatSessionDate(session.date) }} · {{ session.time }} · {{ session.activity }}
            </p>
          </div>
          <button
            v-if="isInstructor"
            class="btn-primary"
            @click="router.push({ name: 'in-attendance-mode', params: { id: sessionId } })"
          >
            Attendance mode
          </button>
        </div>

        <div class="stat-grid">
          <div v-for="stat in stats" :key="stat.label" class="stat-tile">
            <div class="stat-tile-value">{{ stat.value }}</div>
            <div class="stat-tile-label">{{ stat.label }}</div>
          </div>
        </div>

        <div class="pills">
          <button
            v-for="option in filterOptions"
            :key="option.value"
            :class="['pill', { active: statusFilter === option.value }]"
            @click="statusFilter = option.value"
          >
            {{ option.label }}
          </button>
        </div>

        <div v-if="saveError" class="form-error">{{ saveError }}</div>

        <table class="data-table">
          <thead>
            <tr>
              <th>Participant</th>
              <th>Status</th>
              <th>Absence reason</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in visibleAttendance" :key="record.participant_id">
              <td v-if="isInstructor">
                <span class="participant">
                  <span class="initials-avatar">{{ initials(record.name) }}</span>
                  {{ record.name }}
                </span>
              </td>
              <td v-else>{{ record.status === 'present' ? 'Present' : 'Absent' }}</td>
              <td>
                <select
                  :value="record.status"
                  :class="['status-select', record.status]"
                  :aria-label="`Status for ${record.name}`"
                  @change="saveRecord(record, { status: $event.target.value })"
                >
                  <option v-for="s in ATTENDANCE_STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
                </select>
              </td>
              <td>
                <select
                  v-if="record.status === 'absent' && isInstructor"
                  :value="record.absence_reason"
                  :aria-label="`Absence reason for ${record.name}`"
                  @change="changeAbsenceReason(record, $event.target.value)"
                >
                  <option value="">Select reason</option>
                  <option v-for="reason in ABSENCE_REASONS" :key="reason.value" :value="reason.value">{{ reason.label }}</option>
                </select>
                <input
                  v-if="record.absence_reason === 'other'"
                  :value="record.absence_reason_other"
                  class="other-reason"
                  type="text"
                  placeholder="Describe the reason"
                  :aria-label="`Other absence reason for ${record.name}`"
                  @change="saveRecord(record, { absence_reason: 'other', absence_reason_other: $event.target.value })"
                />
                <span v-else class="not-applicable">{{ absenceReasonLabel(record) }}</span>
              </td>
            </tr>
            <tr v-if="!visibleAttendance.length">
              <td colspan="3" class="empty-row">
                {{ counts.total ? 'Nobody matches this filter.' : 'Nobody was on the roster when this session was created.' }}
              </td>
            </tr>
          </tbody>
        </table>

        <button v-if="isInstructor" type="button" class="link-danger" @click="handleDelete">Delete session</button>
      </template>
    </main>
  </div>
</template>

<style scoped>
.participant {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: var(--text);
}

.data-table select {
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  font-size: var(--text-base);
  background: var(--surface);
  color: var(--text);
}

/* Colour the status so the table can be scanned at a glance. */
.status-select.present { border-color: var(--success); color: var(--success); }

.not-applicable { color: var(--text-faint); }
.other-reason { display: block; width: 100%; margin-top: 6px; }

.empty-row { text-align: center; color: var(--text-faint); padding: 32px 16px; }

.link-danger {
  display: block;
  margin: 24px 0 0 auto;
  background: none;
  border: none;
  padding: 0;
  color: var(--danger);
  font-size: var(--text-sm);
  font-weight: 600;
}
.link-danger:hover { text-decoration: underline; }
</style>
