<script setup>
import PhysicalReport from '@/components/reporting/PhysicalReport.vue'
</script>

<template><div class="dash-page"><main class="content">
  <RouterLink class="back-link" :to="{ name: 'sa-reporting' }">← Reporting options</RouterLink>
  <PhysicalReport show-branch-filter />
</main></div></template>
