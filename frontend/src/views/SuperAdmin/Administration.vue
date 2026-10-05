<template>
  <div class="dash-page">
    <main class="content">
      <h1>Administration</h1>
      <p class="page-subtitle">Low-frequency national settings and records.</p>

      <div class="card-grid">
        <div class="card">
          <h3>Vocabularies</h3>
          <p>The shared absence reasons and physical-test measures every branch selects from.</p>
          <a href="#">Open →</a>
        </div>
        <div class="card">
          <h3>Audit log</h3>
          <p>Review staff and branch changes, report generation, and API write outcomes.</p>
          <RouterLink :to="{ name: 'sa-audit-log' }">Open →</RouterLink>
        </div>
        <div class="card">
          <h3>Exports</h3>
          <p>De-identified research data, ready for external analysis.</p>
          <a href="#">Open →</a>
        </div>
      </div>
    </main>
  </div>
</template>
