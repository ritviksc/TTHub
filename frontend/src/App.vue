<script setup>
import PublicNav from './components/NavBar.vue'
import DashboardNav from './components/DashboardNav.vue'
import { auth } from './stores/auth.js'
</script>

<template>
  <PublicNav v-if="!auth.user" />
  <DashboardNav v-else />
  <RouterView v-slot="{ Component }">
    <Transition name="fade" mode="out-in">
      <component :is="Component" />
    </Transition>
  </RouterView>
</template>