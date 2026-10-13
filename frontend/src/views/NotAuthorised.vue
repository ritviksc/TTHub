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
      <div class="not-auth-wrap">
        <section class="card not-auth-card">
          <div class="shield-icon" aria-hidden="true">🔒</div>
          <h1>Not authorised</h1>
          <p>This page is unavailable or you do not have permission to access it with your current role.</p>
          <div class="actions">
            <RouterLink v-if="dashboard.name !== 'not-authorised'" :to="dashboard" class="btn-primary">
              Return to your dashboard
            </RouterLink>
            <p v-else class="contact-admin">Your account has no recognised role. Please contact a Taurite Tū administrator.</p>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.not-auth-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 50vh;
}

.not-auth-card {
  max-width: 480px;
  text-align: center;
  padding: 40px 32px;
}

.shield-icon {
  font-size: 40px;
  margin-bottom: 16px;
  line-height: 1;
}

.not-auth-card h1 {
  font-size: var(--text-2xl);
  margin-bottom: 12px;
}

.not-auth-card p {
  color: var(--text-secondary);
  font-size: var(--text-base);
  margin-bottom: 24px;
}

.actions {
  display: flex;
  justify-content: center;
}

.contact-admin {
  color: var(--danger);
  font-weight: 500;
}
</style>
