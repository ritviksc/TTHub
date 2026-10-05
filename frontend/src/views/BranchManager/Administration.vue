<template>
  <div class="dash-page"><main class="content">
    <h1>Administration</h1>
    <p class="page-subtitle">Administrative activity for your branch.</p>
    <section class="card">
      <h2>Audit log</h2>
      <p>Review staff changes, reports and recorded operations related to your branch.</p>
      <RouterLink :to="{ name: 'bm-audit-log' }">Open audit log →</RouterLink>
    </section>
  </main></div>
</template>
