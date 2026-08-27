<script setup>
import { ref, onMounted } from 'vue'
import { listStaff, deactivateStaff } from '@/apis.js'

const staff = ref([])
const error = ref('')

async function load() {
  try {
    staff.value = await listStaff()
  } catch {
    error.value = 'Could not load staff list.'
  }
}

async function handleDeactivate(id) {
  if (!confirm('Deactivate this account?')) return
  try {
    await deactivateStaff(id)
    await load()
  } catch {
    error.value = 'Could not deactivate this account.'
  }
}

onMounted(load)
</script>

<template>
  <div>
    <p v-if="error">{{ error }}</p>
    <table>
      <thead>
        <tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th></th></tr>
      </thead>
      <tbody>
        <tr v-for="s in staff" :key="s.id">
          <td>{{ s.first_name }} {{ s.last_name }}</td>
          <td>{{ s.email }}</td>
          <td>{{ s.role }}</td>
          <td>{{ s.is_active ? 'Active' : 'Inactive' }}</td>
          <td>
            <button v-if="s.is_active" @click="handleDeactivate(s.id)">Deactivate</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>