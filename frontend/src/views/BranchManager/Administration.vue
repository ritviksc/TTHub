<script setup>
import { RouterLink } from 'vue-router'
import { ADMIN_LABEL } from '@/utils/nav.js'
</script>

<template>
  <div class="dash-page"><main class="content">
    <h1>{{ ADMIN_LABEL }}</h1>
    <p class="page-subtitle">Administrative activity for your branch.</p>
    <div class="card-grid">
      <section class="card">
        <h2>Kaimahi</h2>
        <p>The kaimahi in your kapa, their details and access.</p>
        <RouterLink :to="{ name: 'bm-instructors' }">Manage kaimahi →</RouterLink>
      </section>
      <section class="card">
        <h2>Audit log</h2>
        <p>Review staff changes, reports and recorded operations related to your branch.</p>
        <RouterLink :to="{ name: 'bm-audit-log' }">Open audit log →</RouterLink>
      </section>
      <section class="card">
        <h2>Documents</h2>
        <p>Organisation-wide files, and files for your kapa.</p>
        <RouterLink :to="{ name: 'documents' }">Open documents →</RouterLink>
      </section>
    </div>
  </main></div>
</template>
