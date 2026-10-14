<script setup>
import { RouterLink } from 'vue-router'
import { ADMIN_LABEL } from '@/utils/nav.js'
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <div class="page-header">
        <div>
          <h1>{{ ADMIN_LABEL }}</h1>
          <p class="page-subtitle" style="margin-bottom: 0;">Low-frequency national settings and records.</p>
        </div>
      </div>

      <div class="card-grid">
        <div class="card">
          <h3>Users</h3>
          <p>Add staff and manage accounts, roles and access across every kapa.</p>
          <RouterLink :to="{ name: 'sa-users' }">Manage users →</RouterLink>
        </div>
        <div class="card">
          <h3>Audit log</h3>
          <p>Review staff and branch changes, report generation, and API write outcomes.</p>
          <RouterLink :to="{ name: 'sa-audit-log' }">Open →</RouterLink>
        </div>
        <div class="card">
          <h3>Documents</h3>
          <p>Organisation-wide files, and files for each kapa.</p>
          <RouterLink :to="{ name: 'documents' }">Open documents →</RouterLink>
        </div>
      </div>
    </main>
  </div>
</template>
