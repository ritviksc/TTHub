<script setup>
import { ref, computed } from 'vue'
import { auth } from '@/stores/auth.js'

const instructorName = computed(() => {
  const u = auth.user
  if (!u) return ''
  return `${u.first_name ?? ''} ${u.last_name ?? ''}`.trim() || u.email
})
const firstName = computed(() => instructorName.value.split(' ')[0])

// TODO: all of the below is prototype data — no API behind it yet.
const today = ref('Thursday 13 August')

const todaySession = ref({
  name: 'Thursday morning class',
  startsIn: '25 minutes',
  time: '9:30–10:30am',
  location: 'Te Whare Manaaki, Rotorua',
  roster: 14,
  tags: ['2 sent word they\'re māuiui', '1 new participant this week'],
})

const recentSessions = ref([
  { name: 'Tuesday morning class',  date: 'Tue 11 Aug', attended: 12,   total: 14,   amended: false },
  { name: 'Thursday morning class', date: 'Thu 6 Aug',  attended: 13,   total: 14,   amended: false },
  { name: 'Tuesday morning class',  date: 'Tue 4 Aug',  attended: null, total: null, amended: true, amendedDate: 'Wed 5 Aug' },
  { name: 'Thursday morning class', date: 'Thu 30 Jul', attended: 11,   total: 14,   amended: false },
])

const alerts = ref([
  { type: 'warning', message: '3 participants overdue for physical testing', action: 'See who →' },
  { type: 'info',    message: 'Hone T. — GP consent renews 30 Aug', action: 'Open record →' },
  { type: 'info',    message: 'Quarterly whakaaro round closes Fri', action: 'Record feedback →' },
])
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <h1>Kia ora, {{ firstName }}</h1>
      <p class="page-subtitle">{{ today }} · one session today</p>

      <div class="today-card">
        <div>
          <div class="today-label">TODAY · STARTS IN {{ todaySession.startsIn.toUpperCase() }}</div>
          <h2 class="today-title">{{ todaySession.name }}</h2>
          <p class="session-meta">
            {{ todaySession.time }} · {{ todaySession.location }} · {{ todaySession.roster }} on the roster
          </p>
          <div class="session-tags">
            <span class="tag" v-for="tag in todaySession.tags" :key="tag">{{ tag }}</span>
          </div>
        </div>
        <div class="today-card-right">
          <button class="btn-roll-call">
            Start roll call
            <span class="btn-sub">Walk the room with the tablet</span>
          </button>
          <button class="btn-secondary">Open session details</button>
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
              <tr v-for="(s, i) in recentSessions" :key="i">
                <td>{{ s.name }}</td>
                <td>{{ s.date }}</td>
                <td>
                  <span v-if="s.amended" class="amended">↗ Amended {{ s.amendedDate }}</span>
                  <span v-else class="attendance-ok">✓ {{ s.attended }} of {{ s.total }} present</span>
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
              <a href="#">{{ alert.action }}</a>
            </div>
          </div>
        </div>

      </div>

      <p class="demo-note">Demonstration data only. All names, branches and quotes are fictional.</p>
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

.today-card-right {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 200px;
}
.btn-roll-call {
  background: var(--maroon);
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
  box-shadow: 0 1px 3px rgba(36, 28, 23, 0.12);
  transition: all 0.15s ease;
}
.btn-roll-call:hover {
  background: var(--maroon-dark);
  box-shadow: 0 4px 10px rgba(36, 28, 23, 0.18);
}
.btn-sub {
  font-size: var(--text-xs);
  font-weight: 400;
  opacity: 0.85;
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
  transition: all 0.15s ease;
}
.btn-secondary:hover {
  border-color: var(--text-muted);
  background: var(--surface-sunken);
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
  color: var(--maroon);
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
