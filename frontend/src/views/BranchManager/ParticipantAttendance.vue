<script setup>
import { useRoute } from 'vue-router'
import ParticipantDetail from '@/components/participants/ParticipantDetail.vue'

const route = useRoute()
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <ParticipantDetail :key="route.params.id" :participant-id="route.params.id" page="attendance" route-prefix="bm" />
    </main>
  </div>
</template>
