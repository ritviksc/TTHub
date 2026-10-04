<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { auth } from '@/stores/auth.js'
import { listSessions } from '@/apis.js'
import { programmeToday, formatSessionDate } from '@/utils/sessions.js'
import { formatTimeDisplay, formatFullDate } from '@/utils/calendar.js'

const router = useRouter()

const instructorName = computed(() => {
  const u = auth.user
  if (!u) return ''
  return `${u.first_name ?? ''} ${u.last_name ?? ''}`.trim() || u.email
})
const firstName = computed(() => instructorName.value.split(' ')[0] || 'Kaimahi')

const sessions = ref([])
const loading = ref(true)
const loadError = ref(null)

const todayDateStr = programmeToday()
const todayDisplay = computed(() => formatFullDate(todayDateStr))

async function load() {
  loading.value = true
  loadError.value = null
  try {
    sessions.value = await listSessions()
  } catch (err) {
    loadError.value = 'Could not load sessions.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

// Determine the featured session (today's, next upcoming, or most recent)
const featuredSession = computed(() => {
  if (!sessions.value.length) return null

  // 1. Session today
  const todayMatch = sessions.value.find(s => s.date === todayDateStr)
  if (todayMatch) return todayMatch

  // 2. Next upcoming session
  const upcoming = sessions.value
    .filter(s => s.date > todayDateStr)
    .sort((a, b) => (a.date + (a.time || '')).localeCompare(b.date + (b.time || '')))
  if (upcoming.length > 0) return upcoming[0]

  // 3. Fallback to most recent session
  return sessions.value[0]
})

const isToday = computed(() => featuredSession.value?.date === todayDateStr)
const isUpcoming = computed(() => featuredSession.value && featuredSession.value.date > todayDateStr)

const sessionCardLabel = computed(() => {
  if (!featuredSession.value) return 'SESSIONS'
  if (isToday.value) {
    return `TODAY · ${formatTimeDisplay(featuredSession.value.time)}`
  }
  if (isUpcoming.value) {
    return `NEXT SESSION · ${formatSessionDate(featuredSession.value.date)}`
  }
  return `MOST RECENT · ${formatSessionDate(featuredSession.value.date)}`
})

const pageSubtitle = computed(() => {
  const todayCount = sessions.value.filter(s => s.date === todayDateStr).length
  if (todayCount === 1) return `${todayDisplay.value} · 1 session today`
  if (todayCount > 1) return `${todayDisplay.value} · ${todayCount} sessions today`
  return `${todayDisplay.value} · No sessions today`
})

function startRollCall() {
  if (featuredSession.value?.id) {
    router.push({
      name: 'in-attendance-mode',
      params: { id: featuredSession.value.id },
    })
  } else {
    router.push({ name: 'in-sessions' })
  }
}

function openSessionDetails() {
  if (featuredSession.value?.id) {
    router.push({
      name: 'in-session-detail',
      params: { id: featuredSession.value.id },
    })
  } else {
    router.push({ name: 'in-sessions' })
  }
}

const recentSessions = computed(() => {
  return [...sessions.value]
    .sort((a, b) => (b.date + (b.time || '')).localeCompare(a.date + (a.time || '')))
    .slice(0, 5)
})

const alerts = [
  {
    type: 'warning',
    message: 'Check kaumātua attendance & record assessments',
    action: 'Open kaumātua →',
    to: { name: 'in-participants' },
  },
  {
    type: 'info',
    message: 'Review full timetable and session calendar',
    action: 'Open sessions →',
    to: { name: 'in-sessions' },
  },
  {
    type: 'info',
    message: 'Read training resources and programme documentation',
    action: 'Open documents →',
    to: { name: 'documents' },
  },
]
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <h1>Kia ora, {{ firstName }}</h1>
      <p class="page-subtitle">{{ pageSubtitle }}</p>

      <div v-if="loading" class="loading-state">
        <p>Loading your sessions…</p>
      </div>

      <div v-else-if="featuredSession" class="today-card">
        <div>
          <div class="today-label">{{ sessionCardLabel }}</div>
          <h2 class="today-title">{{ featuredSession.activity || 'Class session' }}</h2>
          <p class="session-meta">
            {{ formatTimeDisplay(featuredSession.time) }} · 
            {{ featuredSession.branch_name || auth.user?.branch?.name || 'Branch' }} · 
            {{ featuredSession.roster_count ?? 0 }} on the roster
          </p>
          <div class="session-tags">
            <span v-if="featuredSession.attendance_finalised" class="tag tag--finalised">
              ✓ Attendance finalised
            </span>
            <span v-else class="tag tag--active">
              Ready for roll call
            </span>
            <span class="tag">
              {{ featuredSession.present_count ?? 0 }} present
            </span>
            <span v-if="featuredSession.roster_count" class="tag">
              {{ featuredSession.roster_count }} rostered
            </span>
          </div>
        </div>
        <div class="today-card-right">
          <button class="btn-roll-call" @click="startRollCall" title="Start roll call attendance mode">
            Start roll call
            <span class="btn-sub">Walk the room with the tablet</span>
          </button>
          <button class="btn-secondary" @click="openSessionDetails" title="Open full session details">
            Open session details
          </button>
        </div>
      </div>

      <div v-else class="today-card empty-card">
        <div>
          <div class="today-label">SCHEDULE</div>
          <h2 class="today-title">No sessions scheduled</h2>
          <p class="session-meta">
            There are currently no sessions scheduled for this branch.
          </p>
        </div>
        <div class="today-card-right">
          <button class="btn-roll-call" @click="router.push({ name: 'in-sessions' })">
            Go to Sessions
            <span class="btn-sub">Create or schedule a session</span>
          </button>
        </div>
      </div>

      <div class="home-grid">
        <div>
          <h3 class="section-heading">Recent sessions</h3>
          <table class="data-table">
            <thead>
              <tr>
                <th>Session</th>
                <th>Date</th>
                <th>Attendance</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!recentSessions.length">
                <td colspan="3" class="empty-sessions">No sessions found.</td>
              </tr>
              <tr
                v-for="s in recentSessions"
                :key="s.id"
                class="clickable-row"
                @click="router.push({ name: 'in-session-detail', params: { id: s.id } })"
              >
                <td>
                  <RouterLink :to="{ name: 'in-session-detail', params: { id: s.id } }" class="session-name-link" @click.stop>
                    {{ s.activity || 'Class session' }}
                  </RouterLink>
                </td>
                <td>{{ formatSessionDate(s.date) }}</td>
                <td>
                  <span v-if="s.attendance_finalised" class="attendance-ok">
                    ✓ {{ s.present_count }} of {{ s.roster_count }} present
                  </span>
                  <span v-else class="amended">
                    ⏱ Unfinalised
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div>
          <h3 class="section-heading">Needs you this week</h3>
          <div class="alerts">
            <div v-for="(alert, i) in alerts" :key="i" :class="['alert-row', alert.type]">
              <div>
                <span v-if="alert.type === 'warning'">⚠ </span>
                {{ alert.message }}
              </div>
              <RouterLink :to="alert.to">{{ alert.action }}</RouterLink>
            </div>
          </div>
        </div>
      </div>

      <p class="demo-note">Taurite Tū Māori Movement & Well-being programme.</p>
    </main>
  </div>
</template>

<style scoped>
.today-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-top: 4px solid var(--teal);
  border-radius: var(--radius-xl);
  padding: 28px 32px;
  box-shadow: var(--shadow-panel);
  margin-bottom: 36px;
  gap: 24px;
}
.today-label {
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--teal);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 6px;
}
.today-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text);
  margin-bottom: 6px;
}
.session-meta {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: 14px;
}
.session-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.tag {
  background: var(--sand-light);
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  padding: 4px 12px;
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--bark);
}
.tag--active {
  background: var(--teal-tint);
  border-color: var(--teal-light);
  color: var(--teal-dark);
  font-weight: 600;
}
.tag--finalised {
  background: var(--success-bg, #ecfdf5);
  border-color: var(--success, #10b981);
  color: var(--success, #10b981);
  font-weight: 600;
}

.today-card-right {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 200px;
}
.btn-roll-call {
  background: var(--primary);
  color: var(--text-on-ink);
  border: none;
  border-radius: var(--radius);
  padding: 12px 18px;
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  box-shadow: 0 2px 6px var(--shadow-glow, rgba(37, 99, 235, 0.25));
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.btn-roll-call:hover {
  background: var(--primary-dark);
  box-shadow: 0 4px 14px var(--shadow-glow, rgba(37, 99, 235, 0.4));
  transform: translateY(-1px);
}
.btn-roll-call:active {
  transform: translateY(0.5px);
}
.btn-sub {
  font-size: var(--text-xs);
  font-weight: 400;
  opacity: 0.88;
}
.btn-secondary {
  background: var(--surface);
  color: var(--text);
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius);
  padding: 10px 18px;
  font-size: var(--text-sm);
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.btn-secondary:hover {
  border-color: var(--teal);
  background: var(--surface-sunken);
  color: var(--teal-dark);
  transform: translateY(-1px);
}
.btn-secondary:active {
  transform: translateY(0.5px);
}

.home-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}
.section-heading {
  margin-bottom: 16px;
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text);
}

.clickable-row {
  cursor: pointer;
  transition: background-color 0.15s ease;
}
.clickable-row:hover {
  background-color: var(--surface-sunken);
}
.session-name-link {
  font-weight: 600;
  color: var(--teal);
  text-decoration: none;
}
.session-name-link:hover {
  text-decoration: underline;
}
.empty-sessions {
  text-align: center;
  color: var(--text-muted);
  padding: 16px;
}
.loading-state {
  padding: 32px;
  text-align: center;
  color: var(--text-muted);
}

.alerts {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.alert-row {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  box-shadow: var(--shadow-card);
}
.alert-row.warning {
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
  color: var(--warning-text);
  font-weight: 600;
}
.alert-row a {
  display: inline-block;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--teal);
  text-decoration: none;
  margin-top: 4px;
}
.alert-row a:hover {
  text-decoration: underline;
}

.attendance-ok {
  color: var(--success);
  font-size: var(--text-sm);
  font-weight: 600;
}
.amended {
  color: var(--warning);
  font-size: var(--text-sm);
  font-weight: 600;
}

@media (max-width: 768px) {
  .today-card {
    flex-direction: column;
    align-items: flex-start;
  }
  .today-card-right {
    width: 100%;
  }
  .home-grid {
    grid-template-columns: 1fr;
  }
}
</style>
