<script setup>
import PublicNav from './components/NavBar.vue'
import DashboardNav from './components/DashboardNav.vue'
import { auth } from './stores/auth.js'
</script>

<template>
  <PublicNav v-if="!auth.user" />
  <DashboardNav v-else />
  <RouterView v-slot="{ Component }">
    <transition name="page-fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </RouterView>
</template>

<style>
/* Smooth page navigation transition */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1), transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
