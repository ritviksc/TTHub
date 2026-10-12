<script setup>
import PhysicalReport from '@/components/reporting/PhysicalReport.vue'
</script>

<template><div class="dash-page"><main class="content">
  <RouterLink class="back-link" :to="{ name: 'sa-reporting' }">← Reporting options</RouterLink>
  <p><RouterLink :to="{ name: 'sa-physical-history' }">View past physical-test reports</RouterLink></p>
  <PhysicalReport show-branch-filter />
</main></div></template>
