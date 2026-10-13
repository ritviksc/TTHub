<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

// Every not-yet-built tab routes here. The title comes from the route's
// meta.title, so a new placeholder page costs one line in the router.
const route = useRoute()
const title = computed(() => route.meta.title ?? 'Coming soon')
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <div class="placeholder-wrap">
        <div class="card placeholder-card">
          <div class="placeholder-icon" aria-hidden="true">⏳</div>
          <h2>{{ title }}</h2>
          <p>This section is currently being scheduled and prepared for release.</p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.placeholder-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 50vh;
}

.placeholder-card {
  max-width: 480px;
  text-align: center;
  padding: 48px 32px;
}

.placeholder-icon {
  font-size: 38px;
  margin-bottom: 16px;
  line-height: 1;
}

.placeholder-card h2 {
  font-size: var(--text-xl);
  margin-bottom: 8px;
  color: var(--text);
}

.placeholder-card p {
  color: var(--text-muted);
  font-size: var(--text-base);
  margin: 0;
}
</style>
