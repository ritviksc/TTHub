<script setup>
import axios from 'axios'
import { ref } from 'vue'
import { login } from '@/apis.js'

import { useRouter } from 'vue-router'
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  loading.value = true
  error.value = ""
  try {
    await login(username.value, password.value)
    router.push('/testdashboard')

  } catch (e) {
    e.value = "Login failed"

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
