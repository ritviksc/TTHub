<script setup>
import { ref, computed, onMounted } from 'vue'
import { listParticipants } from '@/apis.js'

const sessionFilter = ref('All')

const sessionFilters = [
  'This month',
  'This quarter',
  'All'
]

const sessions = ref([])

const participants = ref([])

const showCreateModal = ref(false)
const showAttendanceModal = ref(false)
const showAttendanceMode = ref(false)

const selectedSession = ref(null)

const error = ref('')

const form = ref({
  name: '',
  date: '',
  time: '',
  activity: ''
})

const attendanceStatuses = ref([
  'Present',
  'Absent',
  'Excused'
])

const absenceReasons = ref([
  'Sick',
  'Family commitment',
  'Transport issue',
  'Work commitment',
  'Other'
])

const filteredSessions = computed(() => {
  if (sessionFilter.value === 'All') {
    return sessions.value
  }

  const today = new Date()

  return sessions.value.filter(session => {
    const date = new Date(session.date)

    if (sessionFilter.value === 'This month') {
      return (
        date.getMonth() === today.getMonth() &&
        date.getFullYear() === today.getFullYear()
      )
    }

    if (sessionFilter.value === 'This quarter') {
      const currentQuarter = Math.floor(
        today.getMonth() / 3
      )

      const sessionQuarter = Math.floor(
        date.getMonth() / 3
      )

      return (
        currentQuarter === sessionQuarter &&
        date.getFullYear() === today.getFullYear()
      )
    }

    return true
  })
})

function loadSessions() {
  const saved = localStorage.getItem(
    'taurite_sessions'
  )

  if (saved) {
    sessions.value = JSON.parse(saved)
  } else {
    sessions.value = []
  }
}

function saveSessions() {
  localStorage.setItem(
    'taurite_sessions',
    JSON.stringify(sessions.value)
  )
}

async function loadParticipants() {
  try {
    const data = await listParticipants({
      is_active: true
    })

    participants.value = Array.isArray(data)
      ? data
      : data.results || []
  } catch (e) {
    /*
      Backend may not be running while frontend is being developed.
      Keep the page usable with demo participants.
    */

    participants.value = [
      {
        id: 'demo-1',
        first_name: 'Hone',
        last_name: 'T',
        preferred_name: 'Hone'
      },
      {
        id: 'demo-2',
        first_name: 'Mere',
        last_name: 'R',
        preferred_name: 'Mere'
      },
      {
        id: 'demo-3',
        first_name: 'Wiremu',
        last_name: 'K',
        preferred_name: 'Wiremu'
      },
      {
        id: 'demo-4',
        first_name: 'Aroha',
        last_name: 'P',
        preferred_name: 'Aroha'
      }
    ]
  }
}

function participantName(participant) {
  return (
    participant.preferred_name ||
    `${participant.first_name || ''} ${participant.last_name || ''}`
  ).trim()
}

function openCreateSession() {
  error.value = ''

  form.value = {
    name: '',
    date: '',
    time: '',
    activity: ''
  }

  showCreateModal.value = true
}

function closeCreateSession() {
  showCreateModal.value = false
}

function createNewSession() {
  error.value = ''

  if (
    !form.value.name ||
    !form.value.date ||
    !form.value.time ||
    !form.value.activity
  ) {
    error.value = 'Please complete all fields.'
    return
  }

  const newSession = {
    id: crypto.randomUUID(),
    name: form.value.name,
    date: form.value.date,
    time: form.value.time,
    activity: form.value.activity,
    createdAt: new Date().toISOString(),
    attendance: participants.value.map(participant => ({
      participant_id: participant.id,
      name: participantName(participant),
      photo: participant.photo || participant.photo_url || null,
      status: 'Absent',
      absence_reason: ''
    }))
  }

  sessions.value.unshift(newSession)

  saveSessions()

  showCreateModal.value = false

  form.value = {
    name: '',
    date: '',
    time: '',
    activity: ''
  }
}

function openAttendance(session) {
  selectedSession.value = session
  showAttendanceModal.value = true
  showAttendanceMode.value = false
}

function closeAttendance() {
  showAttendanceModal.value = false
  selectedSession.value = null
}

function openAttendanceMode() {
  showAttendanceModal.value = false
  showAttendanceMode.value = true
}

function closeAttendanceMode() {
  showAttendanceMode.value = false
  selectedSession.value = null
}

function markPresent(person) {
  person.status = 'Present'
  person.absence_reason = ''

  saveSessions()
}

function updateStatus(person, event) {
  person.status = event.target.value

  if (person.status !== 'Absent') {
    person.absence_reason = ''
  }

  saveSessions()
}

function updateReason(person, event) {
  person.absence_reason = event.target.value

  saveSessions()
}

function attendanceCount(session) {
  if (!session) return 0

  return session.attendance.filter(
    person => person.status === 'Present'
  ).length
}

function formatDate(date) {
  if (!date) return ''

  return new Date(date).toLocaleDateString(
    'en-NZ',
    {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    }
  )
}

function resetDemoData() {
  if (
    !confirm(
      'Remove all Sprint 2 demo sessions?'
    )
  ) {
    return
  }

  sessions.value = []

  localStorage.removeItem(
    'taurite_sessions'
  )
}

onMounted(() => {
  loadSessions()
  loadParticipants()
})
</script>

<template>
  <div class="dash-page">

    <main class="content">

      <!-- HEADER -->

      <div class="page-header">

        <div>
          <h1>Sessions</h1>

          <p class="page-subtitle">
            Create sessions and record participant attendance.
          </p>
        </div>

        <button
          class="btn-primary"
          @click="openCreateSession"
        >
          + New session
        </button>

      </div>


      <!-- ERROR -->

      <div
        v-if="error"
        class="form-error"
      >
        {{ error }}
      </div>


      <!-- FILTER -->

      <div class="pills">

        <button
          v-for="filter in sessionFilters"
          :key="filter"
          :class="[
            'pill',
            {
              active:
                sessionFilter === filter
            }
          ]"
          @click="sessionFilter = filter"
        >
          {{ filter }}
        </button>

      </div>


      <!-- SESSIONS -->

      <div
        v-if="filteredSessions.length === 0"
        class="empty"
      >

        <h2>No sessions yet</h2>

        <p>
          Create your first session to start recording attendance.
        </p>

        <button
          class="btn-primary"
          @click="openCreateSession"
        >
          + Create session
        </button>

      </div>


      <table
        v-else
        class="data-table"
      >

        <thead>

          <tr>
            <th>Session</th>
            <th>Date</th>
            <th>Time</th>
            <th>Activity</th>
            <th>Attendance</th>
            <th></th>
          </tr>

        </thead>

        <tbody>

          <tr
            v-for="session in filteredSessions"
            :key="session.id"
            class="session-row"
            @click="openAttendance(session)"
          >

            <td>
              <strong>
                {{ session.name }}
              </strong>
            </td>

            <td>
              {{ formatDate(session.date) }}
            </td>

            <td>
              {{ session.time }}
            </td>

            <td>
              {{ session.activity }}
            </td>

            <td>

              <span class="attendance-ok">

                ✓
                {{ attendanceCount(session) }}
                /
                {{ session.attendance.length }}

                present

              </span>

            </td>

            <td class="arrow-cell">
              ›
            </td>

          </tr>

        </tbody>

      </table>


      <!-- DEVELOPMENT RESET -->

      <button
        v-if="sessions.length"
        class="reset-button"
        @click="resetDemoData"
      >
        Reset Sprint 2 demo data
      </button>


      <!-- CREATE SESSION MODAL -->

      <div
        v-if="showCreateModal"
        class="modal-backdrop"
        @click.self="closeCreateSession"
      >

        <div class="modal">

          <h2>Create new session</h2>

          <div class="form-group">

            <label>
              Session name
            </label>

            <input
              v-model="form.name"
              type="text"
              placeholder="Thursday morning class"
            />

          </div>


          <div class="form-row">

            <div class="form-group">

              <label>
                Date
              </label>

              <input
                v-model="form.date"
                type="date"
              />

            </div>


            <div class="form-group">

              <label>
                Time
              </label>

              <input
                v-model="form.time"
                type="time"
              />

            </div>

          </div>


          <div class="form-group">

            <label>
              Activity
            </label>

            <input
              v-model="form.activity"
              type="text"
              placeholder="Strength and mobility"
            />

          </div>


          <div class="modal-actions">

            <button
              class="btn-cancel"
              @click="closeCreateSession"
            >
              Cancel
            </button>

            <button
              class="btn-primary"
              @click="createNewSession"
            >
              Create session
            </button>

          </div>

        </div>

      </div>


      <!-- ATTENDANCE MODAL -->

      <div
        v-if="showAttendanceModal"
        class="modal-backdrop"
        @click.self="closeAttendance"
      >

        <div class="modal attendance-modal">

          <div class="modal-title-row">

            <div>

              <h2>
                {{ selectedSession.name }}
              </h2>

              <p>
                {{ formatDate(selectedSession.date) }}
                ·
                {{ selectedSession.time }}
                ·
                {{ selectedSession.activity }}
              </p>

            </div>

            <button
              class="close-button"
              @click="closeAttendance"
            >
              ×
            </button>

          </div>


          <div class="attendance-summary">

            <strong>
              {{ attendanceCount(selectedSession) }}
            </strong>

            /
            {{ selectedSession.attendance.length }}

            present

          </div>


          <button
            class="btn-roll-call"
            @click="openAttendanceMode"
          >
            Start Attendance Mode

            <span>
              Participants can tap their own photo
            </span>

          </button>


          <div class="attendance-list">

            <div
              v-for="person in selectedSession.attendance"
              :key="person.participant_id"
              class="attendance-item"
            >

              <div class="person-name">

                <div class="avatar">
                  {{ person.name.charAt(0) }}
                </div>

                <strong>
                  {{ person.name }}
                </strong>

              </div>


              <div class="attendance-fields">

                <select
                  :value="person.status"
                  @change="
                    updateStatus(
                      person,
                      $event
                    )
                  "
                >

                  <option
                    v-for="status in attendanceStatuses"
                    :key="status"
                    :value="status"
                  >
                    {{ status }}
                  </option>

                </select>


                <select
                  v-if="
                    person.status === 'Absent'
                  "
                  :value="person.absence_reason"
                  @change="
                    updateReason(
                      person,
                      $event
                    )
                  "
                >

                  <option value="">
                    Select reason
                  </option>

                  <option
                    v-for="reason in absenceReasons"
                    :key="reason"
                    :value="reason"
                  >
                    {{ reason }}
                  </option>

                </select>

              </div>

            </div>

          </div>

        </div>

      </div>


      <!-- ATTENDANCE MODE -->

      <div
        v-if="showAttendanceMode"
        class="attendance-mode"
      >

        <div class="attendance-mode-header">

          <div>

            <h1>
              Attendance Mode
            </h1>

            <p>
              {{ selectedSession.name }}
              ·
              {{ formatDate(selectedSession.date) }}
            </p>

          </div>


          <button
            class="btn-secondary"
            @click="closeAttendanceMode"
          >
            Exit
          </button>

        </div>


        <div class="attendance-big-counter">

          {{ attendanceCount(selectedSession) }}

          /

          {{ selectedSession.attendance.length }}

          present

        </div>


        <div class="photo-grid">

          <button
            v-for="person in selectedSession.attendance"
            :key="person.participant_id"
            :class="[
              'participant-card',
              {
                present:
                  person.status === 'Present'
              }
            ]"
            @click="markPresent(person)"
          >

            <div class="large-avatar">

              {{ person.name.charAt(0) }}

            </div>


            <strong>
              {{ person.name }}
            </strong>


            <span
              v-if="
                person.status === 'Present'
              "
              class="present-label"
            >
              ✓ Present
            </span>


            <span
              v-else
              class="tap-label"
            >
              Tap to sign in
            </span>

          </button>

        </div>

      </div>

    </main>

  </div>
</template>


<style scoped>

.session-row {
  cursor: pointer;
}

.session-row:hover {
  background: var(--surface-sunken);
}

.arrow-cell {
  text-align: right;
  font-size: 20px;
  color: var(--text-muted);
}

.attendance-ok {
  color: var(--success);
  font-size: 13px;
  font-weight: 600;
}

.empty {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 70px 30px;
  text-align: center;
  box-shadow: var(--shadow-card);
}

.empty h2 {
  margin-bottom: 8px;
}

.empty p {
  color: var(--text-muted);
  margin-bottom: 20px;
}

.reset-button {
  display: block;
  margin: 25px auto;
  border: none;
  background: transparent;
  color: var(--text-faint);
  cursor: pointer;
  font-size: 11px;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
  padding: 20px;
}

.modal {
  background: var(--surface);
  border-radius: var(--radius-xl);
  padding: 32px;
  width: 480px;
  max-width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-modal);
}

.attendance-modal {
  width: 760px;
}

.modal-title-row {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
}

.modal-title-row p {
  color: var(--text-muted);
  font-size: 13px;
}

.close-button {
  border: none;
  background: none;
  font-size: 26px;
  cursor: pointer;
  color: var(--text-muted);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.attendance-summary {
  background: var(--surface-sunken);
  border-radius: var(--radius);
  padding: 14px;
  margin-bottom: 15px;
}

.btn-roll-call {
  width: 100%;
  border: none;
  background: var(--maroon);
  color: white;
  padding: 13px;
  border-radius: var(--radius);
  cursor: pointer;
  font-weight: 600;
  margin-bottom: 18px;
}

.btn-roll-call span {
  display: block;
  font-size: 11px;
  opacity: .8;
  font-weight: 400;
  margin-top: 3px;
}

.attendance-list {
  border-top: 1px solid var(--border);
}

.attendance-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 13px 0;
  border-bottom: 1px solid var(--border-faint);
  gap: 15px;
}

.person-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--teal-tint);
  color: var(--teal-dark);
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: 700;
}

.attendance-fields {
  display: flex;
  gap: 8px;
}

.attendance-fields select {
  padding: 8px 10px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: var(--surface);
}

.attendance-mode {
  position: fixed;
  inset: 0;
  z-index: 500;
  background: var(--bg);
  padding: 35px;
  overflow-y: auto;
}

.attendance-mode-header {
  max-width: 1100px;
  margin: 0 auto 25px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.attendance-mode-header p {
  color: var(--text-muted);
}

.attendance-big-counter {
  max-width: 1100px;
  margin: 0 auto 25px;
  font-size: 22px;
  font-weight: 700;
}

.photo-grid {
  max-width: 1100px;
  margin: auto;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
}

.participant-card {
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 24px 15px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 9px;
  min-height: 190px;
  font-size: 14px;
}

.participant-card:hover {
  border-color: var(--maroon);
}

.participant-card.present {
  border-color: var(--success);
  background: var(--success-bg);
}

.large-avatar {
  width: 105px;
  height: 105px;
  border-radius: 50%;
  background: var(--teal-tint);
  color: var(--teal-dark);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 700;
}

.present-label {
  color: var(--success);
  font-weight: 700;
}

.tap-label {
  color: var(--text-muted);
  font-size: 12px;
}

@media (max-width: 800px) {
  .photo-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .attendance-item {
    flex-direction: column;
    align-items: stretch;
  }

  .attendance-fields {
    flex-wrap: wrap;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}

</style>