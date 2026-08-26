<script setup>
import axios from 'axios'
import { ref, onMounted } from 'vue'
import { TIMEOUT_ERROR, MAX_ATTEMPTS, withRetry, login, fetchCsrfCookie } from '@/apis.js'

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

onMounted(async () => {
  try {
    await withRetry(MAX_ATTEMPTS, fetchCsrfCookie);
  } catch (err) {
    console.error("Unable to get CSRF cookie:",err);
    error.value = "Unable to connect to server. Try logging in later."
    
  }
});

async function handleLogin() {
  loading.value = true
  error.value = ""
  try {
    const data = await login(username.value, password.value)
    router.push(roleRoutes[data.role])
    console.log(data);
  } catch (err) {
    if (err.code === TIMEOUT_ERROR) {
      error.value = "The server took too long to respond.";
    } else if (err.response?.status === 401) {
        error.value = "Incorrect username or password.";
    } else if (err.response?.status === 403) {
        error.value = "Request was rejected. Please refresh and try again.";
    } else if (!err.response) {
        error.value = "Unable to reach the server.";
    } else {
        error.value = "Something went wrong. Please try again later.";
    }
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
