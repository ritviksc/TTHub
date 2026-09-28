<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { auth } from '@/stores/auth.js'
import { listParticipants, listSessions, listStaff, getAttendanceReport } from '@/apis.js'
import { formatSessionDate } from '@/utils/sessions.js'

const loading = ref(true)
const loadError = ref(null)

const participants = ref([])
const sessions = ref([])
const instructors = ref([])
const attendanceReport = ref(null)

const managerName = computed(() => {
  const u = auth.user
  if (!u) return ''
  return `${u.first_name ?? ''} ${u.last_name ?? ''}`.trim() || u.email
})
const firstName = computed(() => managerName.value.split(' ')[0] || 'Manager')
const branchName = computed(() => auth.user?.branch?.name ?? 'Your branch')

/* ---- Real Derived Metrics ---- */
const activeParticipants = computed(() =>
  participants.value.filter(p => p.is_active !== false)
)

const activeInstructors = computed(() =>
  instructors.value.filter(i => i.role === 'instructor' && i.is_active)
)

const participantsMissingGp = computed(() =>
  activeParticipants.value.filter(p => !p.gp_consent_date && !p.gp_consent_document)
)

const unfinalisedSessions = computed(() =>
  sessions.value.filter(s => !s.attendance_finalised)
)

const averageAttendanceRate = computed(() => {
  if (attendanceReport.value?.totals?.attendance_rate != null) {
    return Math.round(attendanceReport.value.totals.attendance_rate)
  }
  // Fallback calculation from sessions if report not available
  let totalPresent = 0
  let totalRoster = 0
  for (const s of sessions.value) {
    const present = s.present_count ?? s.attendance?.filter(a => a.status === 'present').length ?? 0
    const total = s.roster_count ?? s.attendance?.length ?? 0
    totalPresent += present
    totalRoster += total
  }
  return totalRoster > 0 ? Math.round((totalPresent / totalRoster) * 100) : 0
})

/* ---- Alerts ---- */
const alerts = computed(() => {
  const list = []
  if (participantsMissingGp.value.length > 0) {
    list.push({
      type: 'warning',
      message: `${participantsMissingGp.value.length} participant${participantsMissingGp.value.length === 1 ? '' : 's'} missing GP consent`,
      to: { name: 'bm-participants' },
      action: 'View participants →',
    })
  }

  if (unfinalisedSessions.value.length > 0) {
    const firstUnfinalised = unfinalisedSessions.value[0]
    list.push({
      type: 'info',
      message: `${unfinalisedSessions.value.length} session${unfinalisedSessions.value.length === 1 ? '' : 's'} awaiting attendance finalisation`,
      to: { name: 'bm-session-detail', params: { id: firstUnfinalised.id } },
      action: 'Finalise attendance →',
    })
  }

  list.push({
    type: 'success',
    message: 'Quarterly attendance & physical report ready to generate',
    to: { name: 'bm-reports' },
    action: 'Open reports →',
  })

  return list
})

/* ---- Recent Sessions ---- */
const recentSessions = computed(() => {
  return [...sessions.value]
    .sort((a, b) => new Date(b.date) - new Date(a.date))
    .slice(0, 5)
})

/* ---- Attendance Chart Bars from Real Sessions ---- */
const sessionBars = computed(() => {
  const sorted = [...sessions.value]
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .slice(-10) // last 10 sessions

  if (sorted.length === 0) {
    return []
  }

  return sorted.map(s => {
    const present = s.present_count ?? s.attendance?.filter(a => a.status === 'present').length ?? 0
    const total = s.roster_count ?? s.attendance?.length ?? 0
    const rate = total > 0 ? Math.round((present / total) * 100) : 0
    const dateLabel = formatSessionDate(s.date).split(' ').slice(0, 2).join(' ')
    return {
      date: dateLabel,
      rate,
      present,
      total,
      activity: s.activity,
    }
  })
})

async function loadData() {
  loading.value = true
  loadError.value = null

  try {
    const [parts, sess, staff] = await Promise.all([
      listParticipants().catch(() => []),
      listSessions().catch(() => []),
      listStaff().catch(() => []),
    ])

    participants.value = Array.isArray(parts) ? parts : (parts.results || [])
    sessions.value = Array.isArray(sess) ? sess : (sess.results || [])
    instructors.value = Array.isArray(staff) ? staff : (staff.results || [])

    // Calculate dates for current quarter to fetch attendance statistics
    const now = new Date()
    const quarterMonth = Math.floor(now.getMonth() / 3) * 3
    const startQ = new Date(now.getFullYear(), quarterMonth, 1).toISOString().split('T')[0]
    const endQ = new Date(now.getFullYear(), quarterMonth + 3, 0).toISOString().split('T')[0]

    try {
      attendanceReport.value = await getAttendanceReport({
        start_date: startQ,
        end_date: endQ,
        branch_id: auth.user?.branch?.id || auth.user?.branch,
      })
    } catch {
      // Non-fatal if reporting service is uninitialised
    }
  } catch (err) {
    loadError.value = 'Could not load branch overview data. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <!-- Page Header -->
      <div class="page-header">
        <div>
          <h1>Kia ora, {{ firstName }}</h1>
          <p class="page-subtitle">
            Branch overview for {{ branchName }} ·
            {{ activeParticipants.length }} participants ·
            {{ sessions.length }} sessions ·
            {{ activeInstructors.length }} instructors
          </p>
        </div>
        <div class="header-badges">
          <span class="branch-pill">{{ branchName }}</span>
        </div>
      </div>

      <!-- Loading State -->
      <p v-if="loading" class="loading-note">Loading branch data…</p>

      <!-- Error State -->
      <div v-else-if="loadError" class="form-error">
        {{ loadError }}
        <button class="btn-cancel" style="margin-left: 12px;" @click="loadData">Retry</button>
      </div>

      <template v-else>
        <!-- Stat Cards Grid -->
        <div class="stat-grid">
          <div class="stat-tile">
            <div class="stat-tile-value">{{ activeParticipants.length }}</div>
            <div class="stat-tile-label">Active participants</div>
            <div class="stat-tile-sub">
              {{ participants.length }} total enrolled
            </div>
          </div>

          <div class="stat-tile">
            <div class="stat-tile-value">{{ averageAttendanceRate }}%</div>
            <div class="stat-tile-label">Average attendance</div>
            <div class="stat-tile-sub">Across recorded sessions</div>
          </div>

          <div class="stat-tile">
            <div class="stat-tile-value">{{ sessions.length }}</div>
            <div class="stat-tile-label">Sessions held</div>
            <div class="stat-tile-sub">
              <span v-if="unfinalisedSessions.length > 0" class="sub-alert">
                {{ unfinalisedSessions.length }} unfinalised
              </span>
              <span v-else>All finalised</span>
            </div>
          </div>

          <div class="stat-tile">
            <div class="stat-tile-value">{{ activeInstructors.length }}</div>
            <div class="stat-tile-label">Instructors</div>
            <div class="stat-tile-sub">Leading programmes</div>
          </div>
        </div>

        <!-- Needs Attention Section -->
        <section class="overview-section">
          <h2>Needs attention</h2>
          <div class="alert-list">
            <div
              v-for="(alert, i) in alerts"
              :key="i"
              class="card alert-card"
            >
              <div class="alert-info">
                <span class="alert-icon">⚠</span>
                <span class="alert-text">{{ alert.message }}</span>
              </div>
              <RouterLink :to="alert.to" class="alert-action">{{ alert.action }}</RouterLink>
            </div>
          </div>
        </section>

        <!-- Two Column Content Grid -->
        <div class="overview-columns">

          <!-- Left Column: Attendance Trends Chart -->
          <div class="card column-card">
            <div class="card-head">
              <h3>Attendance by session</h3>
              <RouterLink :to="{ name: 'bm-attendance-report' }" class="card-link">Full report →</RouterLink>
            </div>

            <div v-if="sessionBars.length === 0" class="empty-chart">
              <p>No recorded sessions yet.</p>
              <RouterLink :to="{ name: 'bm-sessions' }" class="btn-primary btn-small">+ Add session</RouterLink>
            </div>

            <div v-else class="chart-container">
              <div class="bar-chart">
                <div
                  v-for="(bar, i) in sessionBars"
                  :key="i"
                  class="chart-col"
                  :title="`${bar.activity} (${bar.date}): ${bar.rate}% (${bar.present}/${bar.total})`"
                >
                  <div class="bar-track">
                    <div
                      class="bar-fill"
                      :style="{ height: `${Math.max(bar.rate, 6)}%` }"
                    ></div>
                  </div>
                  <span class="col-rate">{{ bar.rate }}%</span>
                  <span class="col-date">{{ bar.date }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Right Column: Recent Sessions -->
          <div class="card column-card">
            <div class="card-head">
              <h3>Recent sessions</h3>
              <RouterLink :to="{ name: 'bm-sessions' }" class="card-link">All sessions →</RouterLink>
            </div>

            <div v-if="recentSessions.length === 0" class="empty-list">
              <p>No sessions recorded yet.</p>
            </div>

            <div v-else class="recent-list">
              <div
                v-for="s in recentSessions"
                :key="s.id"
                class="session-row"
              >
                <div class="session-info">
                  <RouterLink :to="{ name: 'bm-session-detail', params: { id: s.id } }" class="session-name">
                    {{ s.activity }}
                  </RouterLink>
                  <span class="session-meta">
                    {{ formatSessionDate(s.date) }} · {{ s.time }}
                  </span>
                </div>

                <div class="session-stat">
                  <span class="attendance-count">
                    {{ s.present_count ?? 0 }} / {{ s.roster_count ?? 0 }} attended
                  </span>
                  <span :class="['status-badge', s.attendance_finalised ? 'active' : 'inactive']">
                    {{ s.attendance_finalised ? 'Finalised' : 'Draft' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </template>

    </main>
  </div>
</template>

<style scoped>
.header-badges {
  display: flex;
  align-items: center;
  gap: 8px;
}

.branch-pill {
  background: var(--sand-light);
  color: var(--bark);
  padding: 6px 14px;
  border-radius: 999px;
  font-size: var(--text-sm);
  font-weight: 600;
  border: 1px solid var(--border);
}

.stat-tile-sub {
  font-size: var(--text-xs);
  color: var(--bark);
  margin-top: 6px;
}

.sub-alert {
  color: var(--terracotta);
  font-weight: 600;
}

.overview-section {
  margin: 32px 0 24px;
}

.overview-section h2 {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 16px;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  flex-wrap: wrap;
  gap: 12px;
}

.alert-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.alert-icon {
  color: var(--terracotta);
  font-size: 18px;
}

.alert-text {
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--ink);
}

.alert-action {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--maroon);
  text-decoration: none;
}

.alert-action:hover {
  text-decoration: underline;
  color: var(--maroon-dark);
}

.overview-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 32px;
}

@media (max-width: 840px) {
  .overview-columns {
    grid-template-columns: 1fr;
  }
}

.column-card {
  padding: 24px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-head h3 {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--ink);
  margin: 0;
}

.card-link {
  font-size: var(--text-sm);
  color: var(--maroon);
  text-decoration: none;
  font-weight: 600;
}

.card-link:hover {
  text-decoration: underline;
}

.empty-chart, .empty-list {
  padding: 32px 16px;
  text-align: center;
  color: var(--bark);
  font-size: var(--text-sm);
}

/* Attendance bar chart */
.chart-container {
  padding-top: 10px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  height: 180px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
}

.chart-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: flex-end;
}

.bar-track {
  width: 100%;
  max-width: 28px;
  height: 130px;
  background: var(--sand-light);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: flex-end;
  overflow: hidden;
}

.bar-fill {
  width: 100%;
  background: var(--forest);
  border-radius: var(--radius-sm);
  transition: height 0.3s ease;
}

.col-rate {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink);
  margin-top: 6px;
}

.col-date {
  font-size: 10px;
  color: var(--bark);
  margin-top: 2px;
  white-space: nowrap;
}

/* Recent sessions */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.session-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-faint);
  gap: 12px;
}

.session-row:last-child {
  border-bottom: none;
}

.session-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-name {
  font-weight: 600;
  color: var(--maroon);
  text-decoration: none;
}

.session-name:hover {
  text-decoration: underline;
}

.session-meta {
  font-size: var(--text-xs);
  color: var(--bark);
}

.session-stat {
  display: flex;
  align-items: center;
  gap: 10px;
}

.attendance-count {
  font-size: var(--text-xs);
  color: var(--bark);
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}

.status-badge.active {
  background: var(--mint);
  color: var(--forest);
}

.status-badge.inactive {
  background: var(--sand-light);
  color: var(--bark);
}

.btn-small {
  padding: 6px 12px;
  font-size: var(--text-xs);
  margin-top: 8px;
  display: inline-block;
}
</style>
