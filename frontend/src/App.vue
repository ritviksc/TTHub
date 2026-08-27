<script setup>
import Navbar from './components/NavBar.vue'
</script>

<template>
  <Navbar />
  <main>
    <RouterView />
  </main>
</template>

<style scoped>
main {
  width: 100%;
  min-height: calc(100vh - 64px);
}
</style>