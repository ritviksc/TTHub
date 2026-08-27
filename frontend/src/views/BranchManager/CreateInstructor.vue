<script setup>
import { ref } from 'vue'
import { createStaffAccount } from '@/apis.js'

const form = ref({ email: '', password: '', first_name: '', last_name: ''})
const error = ref('')
const success = ref('')

async function submit() {
    error.value = ''
    success.value = ''
    try {
        await createStaffAccount({ ...form.value, role: 'instructor' })
        success.value = `Instructor account created for ${form.value.email}`
        form.value = { email: '', password: '', first_name: '', last_name: '' }
    } catch (e) {
        const data = e.response?.data
        error.value = data ? Object.values(data).flat().join(' ') : 'Could not create account'
  }
}
</script>

<template>
    <form @submit.prevent="submit">
      <input v-model="form.email" type="email" placeholder="Email" required />
      <input v-model="form.first_name" placeholder="First name" required />
      <input v-model="form.last_name" placeholder="Last name" required />
      <input v-model="form.password" type="password" placeholder="Temporary password" required />
      <button type="submit">Create instructor account</button>
      <p v-if="error">{{ error }}</p>
      <p v-if="success">{{ success }}</p>
    </form>
  </template>