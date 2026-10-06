<script setup>
import { auth } from '@/stores/auth.js'
defineProps({ attendanceRoute: String, physicalRoute: String })
</script>
<template>
  <div class="dash-page"><main class="content">
    <div class="page-header"><h1>Reporting</h1></div>
    <p class="page-subtitle">Choose a report, select your dates, and optionally request an AI explanation of the recorded trends.</p>
    <div class="report-options">
      <section class="card">
        <h2>Attendance reporting</h2>
        <p>See attendance rates, participant visits and monthly trends. Finalised empty sessions are included; incomplete registers are counted separately.</p>
        <RouterLink class="btn-primary" :to="{ name: attendanceRoute }">View attendance statistics</RouterLink>
        <p v-if="auth.user?.role === 'super_admin'"><RouterLink :to="{ name: 'sa-attendance-history' }">View past attendance reports</RouterLink></p>
      </section>
      <section class="card">
        <h2>Physical-testing reporting</h2>
        <p>Check testing completion for each kaumātua, assessment counts, exercise measurements and comparable changes. Explore graphs and request an AI explanation.</p>
        <RouterLink class="btn-primary" :to="{ name: physicalRoute }">View physical-testing statistics</RouterLink>
        <p v-if="auth.user?.role === 'super_admin'"><RouterLink :to="{ name: 'sa-physical-history' }">View past physical-test reports</RouterLink></p>
      </section>
    </div>
  </main></div>
</template>
<style scoped>
.report-options { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 24px; }
.card a.btn-primary { display: inline-block; color: var(--text-on-ink); }
</style>
