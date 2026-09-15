<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { listSessions } from '@/apis.js'
import { SESSION_PERIODS, formatSessionDate, isInPeriod } from '@/utils/sessions.js'
import CreateSessionModal from '@/components/sessions/CreateSessionModal.vue'

const router = useRouter()

const sessions = ref([])
const loading = ref(true)
const loadError = ref(null)
const period = ref('All')
const showCreate = ref(false)

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
  return { name: 'in-session-detail', params: { id } }
}

// A new session has nobody marked yet, so take the instructor straight to it.
function onCreated(session) {
  showCreate.value = false
  router.push(sessionRoute(session.id))
}
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <div class="page-header">
        <div>
          <h1>Sessions</h1>
          <p class="page-subtitle">Create sessions and record participant attendance.</p>
        </div>
        <button class="btn-primary" @click="showCreate = true">+ New session</button>
      </div>

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

      <div v-if="loadError" class="form-error">{{ loadError }}</div>
      <p v-else-if="loading" class="loading-note">Loading sessions…</p>

      <div v-else-if="!visibleSessions.length" class="empty">
        <template v-if="sessions.length">
          <h2>No sessions in this period</h2>
          <p>Try a wider filter to see older sessions.</p>
        </template>
        <template v-else>
          <h2>No sessions yet</h2>
          <p>Create your first session to start recording attendance.</p>
          <button class="btn-primary" @click="showCreate = true">+ Create session</button>
        </template>
      </div>

      <table v-else class="data-table">
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
            v-for="session in visibleSessions"
            :key="session.id"
            class="session-row"
            @click="router.push(sessionRoute(session.id))"
          >
            <td>
              <RouterLink :to="sessionRoute(session.id)" class="session-name">{{ session.name }}</RouterLink>
            </td>
            <td>{{ formatSessionDate(session.date) }}</td>
            <td>{{ session.time }}</td>
            <td>{{ session.activity }}</td>
            <td class="attendance-count">✓ {{ session.present_count }} / {{ session.roster_count }} present</td>
            <td class="arrow-cell">›</td>
          </tr>
        </tbody>
      </table>

      <CreateSessionModal v-if="showCreate" @close="showCreate = false" @created="onCreated" />
    </main>
  </div>
</template>

<style scoped>
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
