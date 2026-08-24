<script setup>
import axios from 'axios'
import { ref, onMounted } from 'vue'
import { login, fetchCsrfCookie } from '@/apis.js'

import { useRouter } from 'vue-router'
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const roleRoutes = {
  super_admin: '/super-admin/dashboard',
  branch_manager: '/branch-manager/dashboard',
  instructor: '/instructor/dashboard',
}

onMounted(fetchCsrfCookie)

async function handleLogin() {
  loading.value = true
  error.value = ""
  try {
    await fetchCsrfCookie() // validate request
    const data = await login(username.value, password.value)
    // router.push('/testdashboard') // Can switch to router.push(roleRoutes[data.role]) once we have routing sorted
    console.log(data)

  } catch (e) {
    error.value = "Login failed"

  } finally {
    loading.value = false
  }
}
</script>

<template>
  <!-- @submit.prevent listens for submit and calls preventDefault() so browser won't reload -->
  <form @submit.prevent="handleLogin">
    <!-- v-model is two way binding, typing input updates username.value automatically -->
    <input v-model="username" placeholder="Username" /> 
    <input v-model="password" placeholder="Password" />
    <button type="submit" :disabled="loading">
      {{ loading ? 'Signing in' : 'Sign in'}}
    </button>
    <p v-if="error">{{ error }}</p>

  </form>  
</template>

<style scoped></style>
