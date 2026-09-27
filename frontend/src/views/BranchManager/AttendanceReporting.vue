<script setup>
import AttendanceReport from '@/components/reporting/AttendanceReport.vue'
import { auth } from '@/stores/auth.js'
</script>

<template>
  <div class="dash-page"><main class="content">
    <RouterLink class="back-link" :to="{ name: 'bm-reports' }">← Reporting options</RouterLink>
    <AttendanceReport :branch-name="auth.user?.branch?.name ?? 'Your branch'" />
  </main></div>
</template>
