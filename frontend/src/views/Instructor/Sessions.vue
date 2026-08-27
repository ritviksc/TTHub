<script setup>
import { ref } from 'vue'

const sessionFilter = ref('All')
const sessionFilters = ['This month', 'This quarter', 'All']

// TODO: prototype data — no API behind it yet. The filter above is not wired
// up either; it will need a date range once sessions come from the backend.
const allSessions = ref([
  { name: 'Thursday morning class', date: 'Thu 13 Aug', instructor: 'Wikitōria Paraone', attended: null, total: null, pending: true,  amended: false },
  { name: 'Tuesday morning class',  date: 'Tue 11 Aug', instructor: 'Wikitōria Paraone', attended: 12,   total: 14,   pending: false, amended: false },
  { name: 'Thursday morning class', date: 'Thu 6 Aug',  instructor: 'Wikitōria Paraone', attended: 13,   total: 14,   pending: false, amended: false },
  { name: 'Tuesday morning class',  date: 'Tue 4 Aug',  instructor: 'Wikitōria Paraone', attended: null, total: null, pending: false, amended: true },
  { name: 'Thursday morning class', date: 'Thu 30 Jul', instructor: 'Wikitōria Paraone', attended: 11,   total: 14,   pending: false, amended: false },
])
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <div class="page-header">
        <h1>Sessions</h1>
        <button class="btn-primary">New session</button>
      </div>

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

      <p class="demo-note">Demonstration data only. All names, branches and quotes are fictional.</p>
    </main>
  </div>
</template>

<style scoped>
.attendance-ok { color: var(--success); font-size: 13px; }
.attendance-pending { color: var(--text-muted); font-size: 13px; }
.amended { color: var(--warning); font-size: 13px; font-weight: 500; }
.arrow-cell { color: var(--border-strong); font-size: 18px; text-align: right; }
</style>
