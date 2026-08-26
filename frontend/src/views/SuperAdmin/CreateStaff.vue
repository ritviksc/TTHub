<script setup>
import { ref } from 'vue'
import { createStaffAccount } from '@/apis.js'

const form = ref({
  email: '', password: '', first_name: '', last_name: '',
  role: 'instructor', branch: '',
})
const error = ref('')
const success = ref('')

async function submit() {
  error.value = ''
  success.value = ''
  try {
    await createStaffAccount(form.value)
    success.value = `Account created for ${form.value.email}`
    form.value = { email: '', password: '', first_name: '', last_name: '', role: 'instructor', branch: '' }
  } catch (e) {
    error.value = e.response?.data?.role?.[0] ?? 'Could not create account'
  }
}
</script>

<template>
  <form @submit.prevent="submit">
    <input v-model="form.email" type="email" placeholder="Email" required />
    <input v-model="form.first_name" placeholder="First name" required />
    <input v-model="form.last_name" placeholder="Last name" required />
    <input v-model="form.password" type="password" placeholder="Temporary password" required />
    <select v-model="form.role">
      <option value="instructor">Instructor</option>
      <option value="branch_manager">Branch Manager</option>
      <option value="super_admin">Super Admin</option>
    </select>
    <!-- branch selector would go here once we've got an endpoint listing branches. Still need to add branches to models -->
    <button type="submit">Create account</button>
    <p v-if="error">{{ error }}</p>
    <p v-if="success">{{ success }}</p>
  </form>
</template>