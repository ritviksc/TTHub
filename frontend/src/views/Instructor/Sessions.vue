<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { listSessions } from '@/apis.js'
import { SESSION_PERIODS, formatSessionDate, isInPeriod } from '@/utils/sessions.js'
import CreateSessionModal from '@/components/sessions/CreateSessionModal.vue'
import SessionCalendar from '@/components/sessions/SessionCalendar.vue'
import { auth } from '@/stores/auth.js'

const router = useRouter()

const sessions = ref([])
const loading = ref(true)
const loadError = ref(null)
const period = ref('All')
const viewMode = ref('calendar') // 'calendar' | 'list'
const showCreate = ref(false)
const createInitialDate = ref('')

const isInstructor = computed(() => auth.user?.role === 'instructor')
const canCreate = computed(() => ['instructor', 'branch_manager'].includes(auth.user?.role))
const detailRouteName = computed(() => isInstructor.value ? 'in-session-detail' : 'bm-session-detail')

const visibleSessions = computed(() =>
  sessions.value.filter(s => isInPeriod(s.date, period.value))
)

/* ---- load ---- */

async function load() {
  try {
    sessions.value = await listSessions()
  } catch (e) {
    loadError.value = 'Could not load sessions.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

/* ---- navigation ---- */

function sessionRoute(id) {
  return { name: detailRouteName.value, params: { id } }
}

function openSession(id) {
  router.push(sessionRoute(id))
}

function openCreateModal(date = '') {
  createInitialDate.value = date
  showCreate.value = true
}

// A new session has nobody marked yet, so take the user straight to it.
function onCreated(session) {
  showCreate.value = false
  // Update local list if it's there
  if (session && session.id) {
    sessions.value.unshift(session)
    router.push(sessionRoute(session.id))
  }
}
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <div class="page-header">
        <div>
          <h1>Sessions</h1>
          <p class="page-subtitle">Schedule sessions, view the calendar, and record participant attendance.</p>
        </div>

        <div class="header-actions">
          <div class="view-toggle" role="tablist" aria-label="Sessions view">
            <button
              type="button"
              :class="['toggle-btn', { active: viewMode === 'calendar' }]"
              role="tab"
              :aria-selected="viewMode === 'calendar'"
              @click="viewMode = 'calendar'"
            >
              📅 Calendar
            </button>
            <button
              type="button"
              :class="['toggle-btn', { active: viewMode === 'list' }]"
              role="tab"
              :aria-selected="viewMode === 'list'"
              @click="viewMode = 'list'"
            >
              ☰ List
            </button>
          </div>

          <button v-if="canCreate" class="btn-primary" @click="openCreateModal()">+ New session</button>
        </div>
      </div>

      <div v-if="loadError" class="form-error">{{ loadError }}</div>
      <p v-else-if="loading" class="loading-note">Loading sessions…</p>

      <!-- Calendar View -->
      <SessionCalendar
        v-else-if="viewMode === 'calendar'"
        :sessions="sessions"
        :can-create="canCreate"
        @select-session="openSession"
        @create-session="openCreateModal"
      />

      <!-- List View -->
      <template v-else-if="viewMode === 'list'">
        <div class="pills">
          <button
            v-for="p in SESSION_PERIODS"
            :key="p"
            :class="['pill', { active: period === p }]"
            @click="period = p"
          >
            {{ p }}
          </button>
        </div>

        <div v-if="!visibleSessions.length" class="empty">
          <template v-if="sessions.length">
            <h2>No sessions in this period</h2>
            <p>Try a wider filter to see older sessions.</p>
          </template>
          <template v-else>
            <h2>No sessions yet</h2>
            <p>Create your first session to start recording attendance.</p>
            <button v-if="canCreate" class="btn-primary" @click="openCreateModal()">+ Create session</button>
          </template>
        </div>

        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Activity</th>
              <th>Date</th>
              <th>Time</th>
              <th>Attendance</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="session in visibleSessions"
              :key="session.id"
              class="session-row"
              @click="openSession(session.id)"
            >
              <td>
                <RouterLink :to="sessionRoute(session.id)" class="session-name">{{ session.activity }}</RouterLink>
              </td>
              <td>{{ formatSessionDate(session.date) }}</td>
              <td>{{ session.time }}</td>
              <td class="attendance-count">✓ {{ session.present_count }} / {{ session.roster_count }} present</td>
              <td class="arrow-cell">›</td>
            </tr>
          </tbody>
        </table>
      </template>

      <CreateSessionModal
        v-if="canCreate && showCreate"
        :initial-date="createInitialDate"
        @close="showCreate = false"
        @created="onCreated"
      />
    </main>
  </div>
</template>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.view-toggle {
  display: inline-flex;
  background: var(--sand-light);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  padding: 3px;
  gap: 2px;
}

.toggle-btn {
  background: transparent;
  border: none;
  border-radius: calc(var(--radius) - 2px);
  padding: 6px 14px;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.toggle-btn:hover {
  color: var(--text);
}

.toggle-btn.active {
  background: var(--surface);
  color: var(--teal-dark);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.session-row { cursor: pointer; }
.session-row:hover td { background: var(--surface-sunken); }

.session-name { font-weight: 600; color: var(--text); }

.attendance-count {
  color: var(--success);
  font-size: var(--text-sm);
  font-weight: 600;
}

.arrow-cell {
  text-align: right;
  font-size: var(--text-lg);
  color: var(--text-muted);
}

.empty {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 64px 24px;
  text-align: center;
}
.empty h2 { margin-bottom: 8px; }
.empty p { color: var(--text-muted); margin: 0 0 20px; }
</style>
