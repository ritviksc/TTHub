
<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import logoSrc from '@/assets/logo.png'
 
const router = useRouter()
 
// Current tab — switches between Home and Sessions view
const activeNav = ref('Home')
const navItems = ['Home', 'Sessions', 'Participants', 'Feedback']
 
// Instructor and branch info (placeholder — replace with API call later)
const instructorName = ref('Wikitōria P.')
const branchName = ref('Ngā Hau e Whā')
const today = ref('Thursday 13 August')
 
// ── Today's session card ─────────────────────────────────────────────────────
// Replace with GET /api/sessions/today/ when backend is ready
const todaySession = ref({
  name: 'Thursday morning class',
  startsIn: '25 minutes',
  time: '9:30–10:30am',
  location: 'Te Whare Manaaki, Rotorua',
  roster: 14,
  tags: ['2 sent word they\'re māuiui', '1 new participant this week'],
})
 
// ── Recent sessions (Home tab) ────────────────────────────────────────────────
// Replace with GET /api/sessions/?limit=4 when backend is ready
const recentSessions = ref([
  { name: 'Tuesday morning class', date: 'Tue 11 Aug', attended: 12, total: 14, amended: false },
  { name: 'Thursday morning class', date: 'Thu 6 Aug',  attended: 13, total: 14, amended: false },
  { name: 'Tuesday morning class', date: 'Tue 4 Aug',  attended: null, total: null, amended: true, amendedDate: 'Wed 5 Aug' },
  { name: 'Thursday morning class', date: 'Thu 30 Jul', attended: 11, total: 14, amended: false },
])
 
// ── Needs you this week (Home tab) ───────────────────────────────────────────
const alerts = ref([
  { type: 'warning', message: '3 participants overdue for physical testing', action: 'See who →' },
  { type: 'info',    message: 'Hone T. — GP consent renews 30 Aug', action: 'Open record →' },
  { type: 'info',    message: 'Quarterly whakaaro round closes Fri', action: 'Record feedback →' },
])
 
// ── Sessions page data ────────────────────────────────────────────────────────
const sessionFilter = ref('All')
const sessionFilters = ['This month', 'This quarter', 'All']
 
// Full sessions list — replace with GET /api/sessions/ when backend is ready
const allSessions = ref([
  { name: 'Thursday morning class', date: 'Thu 13 Aug', instructor: 'Wikitōria Paraone', attended: null, total: null, pending: true, amended: false },
  { name: 'Tuesday morning class',  date: 'Tue 11 Aug', instructor: 'Wikitōria Paraone', attended: 12,   total: 14,   pending: false, amended: false },
  { name: 'Thursday morning class', date: 'Thu 6 Aug',  instructor: 'Wikitōria Paraone', attended: 13,   total: 14,   pending: false, amended: false },
  { name: 'Tuesday morning class',  date: 'Tue 4 Aug',  instructor: 'Wikitōria Paraone', attended: null, total: null, pending: false, amended: true },
  { name: 'Thursday morning class', date: 'Thu 30 Jul', instructor: 'Wikitōria Paraone', attended: 11,   total: 14,   pending: false, amended: false },
])
</script>
 
<template>
  <div class="in-dashboard">
 
    <!-- ── Navbar ─────────────────────────────────────────────────────────── -->
    <nav class="navbar">
      <div class="nav-left">
        <img :src="logoSrc" class="logo" alt="Taurite Tū logo" />
        <span class="brand">Taurite Tū</span>
        <span class="scope">Kapa: {{ branchName }}</span>
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
      <div class="nav-right">{{ instructorName }} · Instructor</div>
    </nav>
 
    <!-- ════════════════════════════════════════════════════════════════════
         HOME TAB
    ════════════════════════════════════════════════════════════════════════ -->
    <main v-if="activeNav === 'Home'" class="content">
 
      <!-- Greeting -->
      <h1>Kia ora, {{ instructorName.split(' ')[0] }}</h1>
      <p class="page-subtitle">{{ today }} · one session today</p>
 
      <!-- Today's session card -->
      <div class="today-card">
        <div class="today-card-left">
          <div class="today-label">TODAY · STARTS IN {{ todaySession.startsIn.toUpperCase() }}</div>
          <h2>{{ todaySession.name }}</h2>
          <p class="session-meta">
            {{ todaySession.time }} · {{ todaySession.location }} · {{ todaySession.roster }} on the roster
          </p>
          <div class="session-tags">
            <span class="tag" v-for="tag in todaySession.tags" :key="tag">{{ tag }}</span>
          </div>
        </div>
        <div class="today-card-right">
          <button class="btn-primary">
            Start roll call
            <span class="btn-sub">Walk the room with the tablet</span>
          </button>
          <button class="btn-secondary">Open session details</button>
        </div>
      </div>
 
      <!-- Bottom two columns -->
      <div class="home-grid">
 
        <!-- Recent sessions table -->
        <div>
          <h3>Recent sessions</h3>
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
                  <!-- Amended sessions get an orange label -->
                  <span v-if="s.amended" class="amended">↗ Amended {{ s.amendedDate }}</span>
                  <span v-else class="attendance-ok">✓ {{ s.attended }} of {{ s.total }} present</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
 
        <!-- Needs you this week -->
        <div>
          <h3>Needs you this week</h3>
          <div class="alerts">
            <div
              v-for="(alert, i) in alerts"
              :key="i"
              :class="['alert-row', alert.type]"
            >
              <div>
                <span v-if="alert.type === 'warning'">⚠ </span>
                {{ alert.message }}
              </div>
              <a href="#">{{ alert.action }}</a>
            </div>
          </div>
        </div>
 
      </div>
 
      <p class="demo-note">Demonstration data only. All names, kapa and quotes are fictional.</p>
    </main>
 
    <!-- ════════════════════════════════════════════════════════════════════
         SESSIONS TAB
    ════════════════════════════════════════════════════════════════════════ -->
    <main v-else-if="activeNav === 'Sessions'" class="content">
      <div class="page-header">
        <h1>Sessions</h1>
        <button class="btn-primary">New session</button>
      </div>
 
      <!-- Filter pills -->
      <div class="pills">
        <button
          v-for="f in sessionFilters"
          :key="f"
          :class="['pill', { active: sessionFilter === f }]"
          @click="sessionFilter = f"
        >
          {{ f }}
        </button>
      </div>
 
      <!-- Sessions table -->
      <table class="data-table">
        <thead>
          <tr>
            <th>Session</th>
            <th>Date</th>
            <th>Instructor</th>
            <th>Attendance</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(s, i) in allSessions" :key="i">
            <td>{{ s.name }}</td>
            <td>{{ s.date }}</td>
            <td>{{ s.instructor }}</td>
            <td>
              <span v-if="s.pending" class="attendance-pending">✓</span>
              <span v-else-if="s.amended" class="amended">↗ Amended</span>
              <span v-else class="attendance-ok">✓ {{ s.attended }} of {{ s.total }} present</span>
            </td>
            <td class="arrow-cell">›</td>
          </tr>
        </tbody>
      </table>
 
      <p class="demo-note">Demonstration data only. All names, kapa and quotes are fictional.</p>
    </main>
 
    <!-- ════════════════════════════════════════════════════════════════════
         OTHER TABS (placeholder)
    ════════════════════════════════════════════════════════════════════════ -->
    <main v-else class="content">
      <div class="placeholder-page">
        <h2>{{ activeNav }}</h2>
        <p>This page is coming soon.</p>
      </div>
    </main>
 
  </div>
</template>
 
<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }
 
.in-dashboard {
  min-height: 100vh;
  background: #f0ede6;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
 
/* Navbar */
.navbar {
  display: flex; align-items: center; justify-content: space-between;
  background: #1a1a1a; color: white; padding: 0 24px; height: 52px; gap: 16px;
}
.nav-left { display: flex; align-items: center; gap: 8px; }
.logo { height: 30px; width: auto; filter: brightness(0) invert(1); }
.brand { font-weight: 700; font-size: 15px; }
.scope { font-size: 12px; color: #aaa; }
.nav-links { display: flex; gap: 4px; }
.nav-link {
  background: none; border: none; color: rgba(255,255,255,0.7);
  padding: 6px 14px; border-radius: 20px; font-size: 13px; cursor: pointer;
}
.nav-link:hover { color: white; }
.nav-link.active { background: #333; color: white; }
.nav-right { font-size: 12px; opacity: 0.7; white-space: nowrap; }
 
/* Content */
.content { max-width: 1100px; margin: 0 auto; padding: 48px 24px; }
 
h1 { font-size: 26px; font-weight: 700; color: #1a1a1a; margin-bottom: 4px; }
.page-subtitle { font-size: 13px; color: #888; margin-bottom: 28px; }
 
/* Today's session card */
.today-card {
  display: flex; justify-content: space-between; align-items: center;
  background: white; border-radius: 12px; padding: 24px 28px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07); margin-bottom: 36px; gap: 24px;
}
.today-label { font-size: 11px; font-weight: 700; color: #7a2e2e; letter-spacing: 0.5px; margin-bottom: 6px; }
.today-card h2 { font-size: 22px; font-weight: 700; color: #1a1a1a; margin-bottom: 6px; }
.session-meta { font-size: 13px; color: #777; margin-bottom: 12px; }
.session-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.tag {
  background: #f0ede6; border-radius: 20px; padding: 4px 12px;
  font-size: 12px; color: #555;
}
.today-card-right { display: flex; flex-direction: column; gap: 10px; min-width: 200px; }
.btn-primary {
  background: #7a2e2e; color: white; border: none; border-radius: 8px;
  padding: 12px 18px; font-size: 13px; font-weight: 600; cursor: pointer;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.btn-primary:hover { background: #6a2424; }
.btn-sub { font-size: 11px; font-weight: 400; opacity: 0.8; }
.btn-secondary {
  background: white; color: #1a1a1a; border: 1.5px solid #ccc; border-radius: 8px;
  padding: 10px 18px; font-size: 13px; cursor: pointer; font-weight: 500;
}
.btn-secondary:hover { border-color: #888; }
 
/* Home grid */
.home-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
h3 { font-size: 16px; font-weight: 700; color: #1a1a1a; margin-bottom: 14px; }
 
/* Alerts */
.alerts { display: flex; flex-direction: column; gap: 10px; }
.alert-row {
  background: white; border-radius: 8px; padding: 14px 16px;
  font-size: 13px; color: #333;
}
.alert-row.warning { background: #fdf6e3; border: 1px solid #e8d9a0; color: #5c4a00; font-weight: 600; }
.alert-row a { display: block; font-size: 12px; color: #7a2e2e; text-decoration: none; margin-top: 2px; }
.alert-row a:hover { text-decoration: underline; }
 
/* Sessions page */
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.pills { display: flex; gap: 8px; margin-bottom: 20px; }
.pill {
  padding: 6px 16px; border: 1.5px solid #ccc; border-radius: 20px;
  font-size: 13px; background: white; cursor: pointer; color: #444;
}
.pill:hover { border-color: #888; }
.pill.active { background: #1a1a1a; color: white; border-color: #1a1a1a; }
 
/* Tables */
.data-table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }
.data-table th {
  text-align: left; padding: 12px 16px; font-size: 12px; font-weight: 600;
  color: #888; background: #f7f4ef; border-bottom: 1px solid #e8e2d8;
}
.data-table td { padding: 14px 16px; font-size: 13px; border-bottom: 1px solid #f0ede6; color: #333; }
.data-table tr:last-child td { border-bottom: none; }
 
/* Attendance labels */
.attendance-ok { color: #2a7a4a; font-size: 13px; }
.attendance-pending { color: #888; font-size: 13px; }
.amended { color: #c8860a; font-size: 13px; font-weight: 500; }
.arrow-cell { color: #ccc; font-size: 18px; text-align: right; }
 
/* Demo note */
.demo-note { text-align: center; font-size: 12px; color: #aaa; margin-top: 48px; }
 
/* Placeholder */
.placeholder-page { text-align: center; padding: 80px; color: #aaa; }
.placeholder-page h2 { font-size: 20px; margin-bottom: 8px; color: #888; }
</style>
 
