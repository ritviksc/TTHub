<script setup>
import { useRoute } from 'vue-router'
import ParticipantDetail from '@/components/participants/ParticipantDetail.vue'

const route = useRoute()
// Keep the same participant identity and navigation on the history page.
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <ParticipantDetail :key="route.params.id" :participant-id="route.params.id" page="attendance" />
    </main>
  </div>
</template>
