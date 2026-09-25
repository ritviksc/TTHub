<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { auth } from '@/stores/auth.js'
import ParticipantDetail from '@/components/participants/ParticipantDetail.vue'

const route = useRoute()
// Preserve the shared URL used by existing participant lists.
const canRecordGpConsent = computed(() => ['super_admin', 'branch_manager'].includes(auth.user?.role))
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <ParticipantDetail :key="route.params.id" :participant-id="route.params.id" :can-record-gp-consent="canRecordGpConsent" />
    </main>
  </div>
</template>
