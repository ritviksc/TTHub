<script setup>
import AttendanceReport from '@/components/reporting/AttendanceReport.vue'
</script>

<template>
  <div class="dash-page"><main class="content">
    <RouterLink class="back-link" :to="{ name: 'sa-reporting' }">← Reporting options</RouterLink>
    <AttendanceReport show-branch-filter />
  </main></div>
</template>
