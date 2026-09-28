<script setup>
// BranchManager/Instructors.vue  
// Lists instructors belonging to this branch manager's branch.
// The backend scopes listStaff() to this branch automatically.
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { listStaff } from '@/apis.js'
import { auth } from '@/stores/auth.js'

// --- State ---
const instructors = ref([])
const loading = ref(true)
const error = ref(null)

// --- On page load, fetch staff and filter to this branch's instructors ---
onMounted(async () => {
  try {
 instructors.value = await listStaff()
    
  } catch (e) {
    error.value = 'Could not load instructors.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <div class="page-header">
        <h1>Kaimahi</h1>
        <RouterLink to="/branch-manager/create-instructor" class="btn-primary">
          + Add Kaimahi
        </RouterLink>
      </div>

      <div v-if="loading">Loading…</div>
      <div v-else-if="error" class="error-msg">{{ error }}</div>
      <div v-else-if="instructors.length === 0" class="empty">
        No instructors found for your branch.
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="instructor in instructors" :key="instructor.id">
            <td>{{ instructor.first_name }} {{ instructor.last_name }}</td>
            <td>{{ instructor.email }}</td>
            <td>
              <span :class="instructor.is_active ? 'badge-active' : 'badge-inactive'">
                {{ instructor.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>

    </main>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.btn-primary {
  background: var(--teal);
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  text-decoration: none;
  font-size: 14px;
}
.btn-primary:hover { opacity: 0.9; }

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--surface);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-faint);
}
.data-table td {
  padding: 14px 16px;
  font-size: 14px;
  border-bottom: 1px solid var(--border-faint);
}
.data-table tr:last-child td { border-bottom: none; }

.badge-active {
  background: var(--success-bg);
  color: var(--success);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.badge-inactive {
  background: var(--border-faint);
  color: var(--text-muted);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.error-msg { color: var(--danger); }
.empty { color: var(--text-muted); }
</style>