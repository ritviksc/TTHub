<script setup>
import { ref, computed } from 'vue'
import { auth } from '@/stores/auth.js'

const managerName = computed(() => {
  const u = auth.user
  if (!u) return ''
  return `${u.first_name ?? ''} ${u.last_name ?? ''}`.trim() || u.email
})
const firstName = computed(() => managerName.value.split(' ')[0])
const branchName = computed(() => auth.user?.branch?.name ?? '')

// TODO: all of the below is prototype data — no API behind it yet.
const stats = ref({
  participants: 24,
  attendance: 88,
  sessions: 22,
  instructors: 3,
})

const alerts = ref([
  { message: '3 participants have no current GP consent', action: 'See who →' },
  { message: '5 participants are overdue for physical testing', action: 'See who →' },
  { message: 'Quarterly questionnaire not started — closes 30 Sep', action: 'Start →' },
  { message: '2 offline changes need a decision', action: 'Resolve →' },
])

const recentSessions = ref([
  { date: 'Thu 13 Aug', name: 'Wikitōria', attended: 12, total: 14, amended: false },
  { date: 'Tue 11 Aug', name: 'Tāne',      attended: 13, total: 14, amended: false },
  { date: 'Thu 6 Aug',  name: 'Wikitōria', attended: null, total: null, amended: true },
])

// Fixed placeholder bars. Was Math.random() inline, which re-rolled the whole
// chart on every re-render.
const chartBars = Array.from({ length: 10 }, () => ({
  present: 50 + Math.round(Math.random() * 30),
  excused: 5 + Math.round(Math.random() * 10),
  absent:  5 + Math.round(Math.random() * 15),
}))
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <div class="page-header">
        <div>
          <h1>Kia ora, {{ firstName }}</h1>
          <p class="subtext">
            This quarter: {{ stats.participants }} participants ·
            {{ stats.sessions }} sessions ·
            {{ stats.instructors }} instructors
          </p>
        </div>
        <div class="quarter-selector">{{ branchName }} · this quarter ▾</div>
      </div>

      <!-- Stat cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-number">{{ stats.participants }}</div>
          <div class="stat-label">Active participants</div>
          <div class="stat-change positive">▲ +2 this month</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ stats.attendance }}%</div>
          <div class="stat-label">Average attendance</div>
          <div class="stat-change positive">▲ up from 84%</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ stats.sessions }}</div>
          <div class="stat-label">Sessions this quarter</div>
          <div class="stat-change neutral">on schedule</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ stats.instructors }}</div>
          <div class="stat-label">Instructors</div>
        </div>
      </div>

      <!-- Needs attention -->
      <section class="section">
        <h2>Needs attention</h2>
        <div class="alerts">
          <div class="alert-row" v-for="(alert, i) in alerts" :key="i">
            <span>⚠ {{ alert.message }}</span>
            <a href="#">{{ alert.action }}</a>
          </div>
        </div>
      </section>

      <div class="bottom-grid">

        <!-- Attendance chart (placeholder bars) -->
        <div class="panel">
          <h3>Attendance over the quarter</h3>
          <div class="chart-placeholder">
            <div class="bar-group" v-for="(b, i) in chartBars" :key="i">
              <div class="bar present" :style="{ height: b.present + 'px' }"></div>
              <div class="bar excused" :style="{ height: b.excused + 'px' }"></div>
              <div class="bar absent"  :style="{ height: b.absent  + 'px' }"></div>
            </div>
          </div>
          <div class="legend">
            <span><span class="dot present"></span> Present</span>
            <span><span class="dot excused"></span> Excused</span>
            <span><span class="dot absent"></span> Absent</span>
          </div>
        </div>

        <!-- Recent sessions -->
        <div class="panel">
          <h3>Recent sessions</h3>
          <div class="session-row" v-for="(s, i) in recentSessions" :key="i">
            <div class="session-date">{{ s.date }} · {{ s.name }}</div>
            <div v-if="s.amended" class="amended">↘ Amended</div>
            <div v-else class="session-count">{{ s.attended }} of {{ s.total }}</div>
          </div>
          <a href="#" class="view-all">View all →</a>
        </div>

      </div>

      <p class="demo-note">Demonstration data only. All names, kapa and quotes are fictional.</p>
    </main>
  </div>
</template>

<style scoped>
.page-header { align-items: flex-start; margin-bottom: 28px; }
.subtext { font-size: 13px; color: #888; margin-top: 4px; }
.quarter-selector { font-size: 13px; color: #555; cursor: pointer; }

.stats-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 16px; margin-bottom: 32px;
}
.stat-card {
  background: white; border-radius: 10px; padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.stat-number { font-size: 36px; font-weight: 700; color: #1a1a1a; }
.stat-label { font-size: 12px; color: #888; margin-top: 4px; }
.stat-change { font-size: 11px; margin-top: 6px; }
.positive { color: #2a7a4a; }
.neutral { color: #888; }

.section { margin-bottom: 28px; }
.section h2 { margin-bottom: 12px; }
.alerts { display: flex; flex-direction: column; gap: 8px; }
.alert-row {
  display: flex; justify-content: space-between; align-items: center;
  background: #fdf6e3; border: 1px solid #e8d9a0;
  border-radius: 8px; padding: 12px 16px; font-size: 13px; color: #5c4a00;
}
.alert-row a {
  color: #5c4a00; font-size: 12px; text-decoration: underline;
  white-space: nowrap; margin-left: 16px;
}

.bottom-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.panel {
  background: white; border-radius: 10px; padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.panel h3 { font-size: 14px; margin-bottom: 16px; }

.chart-placeholder {
  display: flex; align-items: flex-end; gap: 6px; height: 80px; margin-bottom: 10px;
}
.bar-group { display: flex; align-items: flex-end; gap: 2px; flex: 1; }
.bar { border-radius: 2px 2px 0 0; min-width: 8px; }
.bar.present { background: #2a7a4a; }
.bar.excused { background: #c8860a; }
.bar.absent  { background: #c0392b; }
.legend { display: flex; gap: 14px; font-size: 11px; color: #555; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; }
.dot.present { background: #2a7a4a; }
.dot.excused { background: #c8860a; }
.dot.absent  { background: #c0392b; }

.session-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-bottom: 1px solid #f0f0f0; font-size: 13px;
}
.session-date { color: #333; }
.session-count { color: #555; }
.amended { color: #888; font-size: 12px; }
.view-all { display: block; margin-top: 12px; font-size: 12px; color: #4D9298; text-decoration: none; }
.view-all:hover { text-decoration: underline; }
</style>
