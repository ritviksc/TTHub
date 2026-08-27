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
      <div class="placeholder-page">
        <h2>{{ title }}</h2>
        <p>This page is coming soon.</p>
      </div>
    </main>
  </div>
</template>
