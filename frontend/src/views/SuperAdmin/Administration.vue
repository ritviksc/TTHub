<script setup>
import { ref } from 'vue'

const notice = ref(null)

function showNotice(title) {
  notice.value = `${title} is managed via automated system exports and administrative migrations.`
  setTimeout(() => {
    notice.value = null
  }, 4000)
}
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <div class="page-header">
        <div>
          <h1>Administration</h1>
          <p class="page-subtitle" style="margin-bottom: 0;">Low-frequency national settings and records.</p>
        </div>
      </div>

      <div v-if="notice" class="form-success" style="margin-bottom: 24px;" role="status">
        ✓ {{ notice }}
      </div>

      <div class="card-grid">
        <div class="card">
          <h3>Vocabularies</h3>
          <p>The shared absence reasons and physical-test measures every branch selects from.</p>
          <a href="#" @click.prevent="showNotice('Vocabularies')">Review records →</a>
        </div>
        <div class="card">
          <h3>Audit log</h3>
          <p>Every write and cross-branch read, append-only and enforced in the database.</p>
          <a href="#" @click.prevent="showNotice('Audit log')">Review records →</a>
        </div>
        <div class="card">
          <h3>Exports</h3>
          <p>De-identified research data, ready for external analysis.</p>
          <a href="#" @click.prevent="showNotice('Data export')">Generate export →</a>
        </div>
      </div>
    </main>
  </div>
</template>
