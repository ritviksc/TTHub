<script setup>
import AttendanceReport from '@/components/reporting/AttendanceReport.vue'
</script>

<template>
  <div class="dash-page"><main class="content">
    <RouterLink class="back-link" :to="{ name: 'sa-reporting' }">← Reporting options</RouterLink>
    <p><RouterLink :to="{ name: 'sa-attendance-history' }">View past attendance reports</RouterLink></p>
    <AttendanceReport show-branch-filter />
  </main></div>
</template>
