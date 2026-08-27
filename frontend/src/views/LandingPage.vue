<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="public-page landing">
    <section class="hero">
      <p class="eyebrow">Taurite Tū</p>
      <h1>Programme tracking made simple</h1>
      <p class="lead">
        A digital platform designed to help manage, track and monitor
        programmes across kapa.
      </p>
    </section>
  </div>
</template>

<style scoped>
.landing {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 24px;
}

.hero {
  max-width: 700px;
  text-align: center;
  padding: 80px 0;
}

.eyebrow {
  font-size: var(--text-sm);
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--teal);
  margin: 0 0 12px;
}

.hero h1 {
  font-size: 52px;
  color: var(--text);
  margin-bottom: 16px;
}

.hero .lead {
  color: var(--text-secondary);
  margin-bottom: 32px;
}

@media (max-width: 640px) {
  .hero { padding: 56px 0; }
  .hero h1 { font-size: 34px; }
}
</style>
