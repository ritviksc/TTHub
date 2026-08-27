<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import logoSrc from '@/assets/logo.png'
import { logout } from '@/apis.js'
 
const router = useRouter()
 
async function handleLogout() {
  try { await logout() } catch (e) {}
  router.push('/login')
}
 
const branchName = ref('Ngā Hau e Whā')
const managerName = ref('Materoa N.')
 
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
 
const navItems = ['Overview', 'Sessions', 'Participants', 'Instructors', 'Feedback', 'Reports']
const activeNav = ref('Overview')
</script>
 
<template>
  <div class="bm-dashboard">
 
    <!-- Navbar -->
    <nav class="navbar">
      <div class="nav-left">
        <img :src="logoSrc" class="logo" alt="Taurite Tū logo" />
        <span class="brand">Taurite Tū</span>
        <span class="branch-name">Kapa: {{ branchName }}</span>
      </div>
      <div class="nav-links">
        <button
          v-for="item in navItems"
          :key="item"
          :class="['nav-link', { active: activeNav === item }]"
          @click="activeNav = item"
        >
          {{ item }}
        </button>
      </div>
      <div class="nav-right">
        <span>{{ managerName }} · Branch Manager</span>
        <button class="logout-btn" @click="handleLogout">Log out</button>
      </div>
    </nav>
 
    <main class="content">
 
      <!-- Page header -->
      <div class="page-header">
        <div>
          <h1>Kia ora, {{ managerName.split(' ')[0] }}</h1>
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
 
      <!-- Bottom grid -->
      <div class="bottom-grid">
 
        <!-- Attendance chart (placeholder bars) -->
        <div class="chart-card">
          <h3>Attendance over the quarter</h3>
          <div class="chart-placeholder">
            <div class="bar-group" v-for="n in 10" :key="n">
              <div class="bar present" :style="{ height: (50 + Math.random() * 30) + 'px' }"></div>
              <div class="bar excused" :style="{ height: (5 + Math.random() * 10) + 'px' }"></div>
              <div class="bar absent"  :style="{ height: (5 + Math.random() * 15) + 'px' }"></div>
            </div>
          </div>
          <div class="legend">
            <span><span class="dot present"></span> Present</span>
            <span><span class="dot excused"></span> Excused</span>
            <span><span class="dot absent"></span> Absent</span>
          </div>
        </div>
 
        <!-- Recent sessions -->
        <div class="sessions-card">
          <h3>Recent sessions</h3>
          <div class="session-row" v-for="(s, i) in recentSessions" :key="i">
            <div class="session-date">{{ s.date }} · {{ s.name }}</div>
            <div v-if="s.amended" class="amended">↘ Amended</div>
            <div v-else class="session-count">{{ s.attended }} of {{ s.total }}</div>
          </div>
          <a href="#" class="view-all">View all →</a>
        </div>
 
      </div>
    </main>
  </div>
</template>
 
<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }
 
.bm-dashboard {
  min-height: 100vh;
  background: #f5f7f4;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
 
.navbar {
  display: flex; align-items: center; justify-content: space-between;
  background: #4D9298; color: white; padding: 0 24px; height: 56px; gap: 16px;
}
.nav-left { display: flex; align-items: center; gap: 10px; }
.logo { height: 30px; width: auto; }.brand { font-weight: 700; font-size: 16px; letter-spacing: 0.3px; }
.branch-name { font-size: 12px; opacity: 0.75; }
.nav-links { display: flex; gap: 4px; }
.nav-link {
  background: none; border: none; color: rgba(255,255,255,0.8);
  padding: 6px 14px; border-radius: 20px; font-size: 13px; cursor: pointer;
  transition: background 0.15s;
}
.nav-link:hover { background: rgba(255,255,255,0.15); color: white; }
.nav-link.active { background: rgba(255,255,255,0.2); color: white; font-weight: 600; }
.nav-right { display: flex; align-items: center; gap: 12px; font-size: 12px; opacity: 0.85; white-space: nowrap; }
.logout-btn {
  background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3);
  color: white; border-radius: 6px; padding: 4px 12px; font-size: 12px; cursor: pointer;
}
.logout-btn:hover { background: rgba(255,255,255,0.25); }
 
.content { max-width: 1100px; margin: 0 auto; padding: 36px 24px; }
 
.page-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 28px;
}
h1 { font-size: 28px; font-weight: 700; color: #1a1a1a; }
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
h2 { font-size: 18px; font-weight: 700; margin-bottom: 12px; }
.alerts { display: flex; flex-direction: column; gap: 8px; }
.alert-row {
  display: flex; justify-content: space-between; align-items: center;
  background: #fdf6e3; border: 1px solid #e8d9a0;
  border-radius: 8px; padding: 12px 16px; font-size: 13px; color: #5c4a00;
}
.alert-row a { color: #5c4a00; font-size: 12px; text-decoration: underline; white-space: nowrap; margin-left: 16px; }
 
.bottom-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.chart-card, .sessions-card {
  background: white; border-radius: 10px; padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
h3 { font-size: 14px; font-weight: 700; margin-bottom: 16px; }
 
.chart-placeholder {
  display: flex; align-items: flex-end; gap: 6px; height: 80px; margin-bottom: 10px;
}
.bar-group { display: flex; align-items: flex-end; gap: 2px; flex: 1; }
.bar { border-radius: 2px 2px 0 0; min-width: 8px; }
.bar.present { background: #2a7a4a; }
.bar.excused  { background: #c8860a; }
.bar.absent   { background: #c0392b; }
.legend { display: flex; gap: 14px; font-size: 11px; color: #555; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; }
.dot.present { background: #2a7a4a; }
.dot.excused  { background: #c8860a; }
.dot.absent   { background: #c0392b; }
 
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
 
