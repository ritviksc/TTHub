<script setup>
import { useRoute } from 'vue-router'
import ParticipantDetail from '@/components/participants/ParticipantDetail.vue'

const route = useRoute()
// Reuse the form without loading the separate attendance section.
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <ParticipantDetail :key="route.params.id" :participant-id="route.params.id" can-record-gp-consent page="details" />
    </main>
  </div>
</template>
