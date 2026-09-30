<script setup>
import { ref, onMounted } from 'vue'
import { createStaffAccount, listBranches } from '@/apis.js'

const form = ref({
  email: '', password: '', first_name: '', last_name: '',
  role: 'instructor', branch: '',
})
const branches = ref([])
const error = ref('')
const success = ref('')

onMounted(async () => {
  try {
    branches.value = await listBranches()
  } catch (e) {
    error.value = e.response?.data?.detail ?? 'Could not load branches. Please reload the page.'
  }
})

async function submit() {
  error.value = ''
  success.value = ''
  try {
    await createStaffAccount(form.value)
    success.value = `Account created for ${form.value.email}`
    form.value = { email: '', password: '', first_name: '', last_name: '', role: 'instructor', branch: '' }
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
    <input v-model="form.password" type="password" placeholder="Password" required />
    <select v-model="form.role">
      <option value="instructor">Instructor</option>
      <option value="branch_manager">Branch Manager</option>
      <option value="super_admin">Super Admin</option>
    </select>
    <select v-model="form.branch" v-if="form.role !== 'super_admin'" required>
      <option value="" disabled>Select a branch</option>
      <option v-for="b in branches" :key="b.id" :value="b.id">{{ b.name }}</option>
    </select>
    <button type="submit">Create account</button>
    <p v-if="error">{{ error }}</p>
    <p v-if="success">{{ success }}</p>
  </form>
</template>
