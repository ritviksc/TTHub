<script setup>
import { useRoute } from 'vue-router'
import ParticipantDetail from '@/components/participants/ParticipantDetail.vue'

const route = useRoute()
// GP consent remains read-only for instructors in the shared form.
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <ParticipantDetail :key="route.params.id" :participant-id="route.params.id" page="details" route-prefix="in" />
    </main>
  </div>
</template>
