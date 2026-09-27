<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { auth } from '@/stores/auth.js'
import { dashboardRoute } from '@/router/access.js'

const dashboard = computed(() => dashboardRoute(auth.user?.role))
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <section class="card">
        <h1>Not authorised</h1>
        <p>This page is unavailable or you do not have permission to access it.</p>
        <RouterLink v-if="dashboard.name !== 'not-authorised'" :to="dashboard">
          Return to your dashboard
        </RouterLink>
        <p v-else>Your account has no recognised dashboard. Please contact an administrator.</p>
      </section>
    </main>
  </div>
</template>
