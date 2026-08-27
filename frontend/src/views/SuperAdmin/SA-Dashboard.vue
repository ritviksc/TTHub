<script setup>
import { ref, computed, onMounted } from 'vue'
import { createStaffAccount, listBranches, listStaff, deactivateStaff } from '@/apis.js'
import { ui } from '@/stores/auth.js'

const showModal = ref(false)
const branches = ref([])
const createError = ref(null)
const createSuccess = ref(false)
const newStaff = ref({ email: '', password: '', first_name: '', last_name: '', role: 'branch_manager', branch_id: '' })
 
async function openModal() {
  showModal.value = true
  createError.value = null
  createSuccess.value = false
  try { branches.value = await listBranches() } catch (e) { branches.value = [] }
}
 
async function submitCreateStaff() {
  createError.value = null
  try {
    await createStaffAccount(newStaff.value)
    createSuccess.value = true
    newStaff.value = { email: '', password: '', first_name: '', last_name: '', role: 'branch_manager', branch_id: '' }
  } catch (e) {
    createError.value = e.response?.data?.detail ?? 'Failed to create account.'
  }
}

async function handleDeactivate(id) {
  if (!confirm('Deactivate this account?')) return
  try {
    await deactivateStaff(id)
    users.value = await listStaff()  // refresh so the row reflects the change
  } catch (e) {
    // could surface this in a toast/error area if you have one
  }
}
 
const activeFilter = ref('All')
const filters = ['All', 'Branch Managers', 'Instructors', 'Super Admins']

const users = ref([])

onMounted(async () => {
  try {
    users.value = await listStaff()
  } catch (e) {
    users.value = []
  }
})
 
const filteredUsers = computed(() => {
  if (activeFilter.value === 'All') return users.value
  if (activeFilter.value === 'Branch Managers') return users.value.filter(u => u.role === 'branch_manager')
  if (activeFilter.value === 'Instructors') return users.value.filter(u => u.role === 'instructor')
  if (activeFilter.value === 'Super Admins') return users.value.filter(u => u.role === 'super_admin')
  return users.value
})
</script>
 
<template>
  <div class="sa-dashboard">
 
    <!-- Create Staff Account Modal -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
      <div class="modal">
        <h2>Create staff account</h2>
        <div v-if="createSuccess" class="form-success">
          Account created successfully. <a href="#" @click="createSuccess = false">Add another</a>
        </div>
        <form v-else @submit.prevent="submitCreateStaff">
          <div class="form-row">
            <div class="form-group">
              <label>First name</label>
              <input v-model="newStaff.first_name" required />
            </div>
            <div class="form-group">
              <label>Last name</label>
              <input v-model="newStaff.last_name" required />
            </div>
          </div>
          <div class="form-group">
            <label>Email</label>
            <input v-model="newStaff.email" required />
          </div>
          <div class="form-group">
            <label>Password</label>
            <input v-model="newStaff.password" type="password" required />
          </div>
          <div class="form-group">
            <label>Role</label>
            <select v-model="newStaff.role">
              <option value="branch_manager">Branch Manager</option>
              <option value="instructor">Instructor</option>
              <option value="super_admin">Super Admin</option>
            </select>
          </div>
          <div class="form-group" v-if="newStaff.role !== 'super_admin'">
            <label>Branch (Kapa)</label>
            <select v-model="newStaff.branch" required>
              <option value="" disabled>Select a branch</option>
              <option v-for="b in branches" :key="b.id" :value="b.id">{{ b.name }}</option>
            </select>
          </div>
          <div v-if="createError" class="form-error">{{ createError }}</div>
          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="showModal = false">Cancel</button>
            <button type="submit" class="btn-primary">Create account</button>
          </div>
        </form>
      </div>
    </div>
 
    <!-- ADMINISTRATION TAB -->
    <main v-if="ui.activeNav === 'Administration'" class="content">
      <h1>Administration</h1>
      <p class="page-subtitle">Low-frequency national settings and records.</p>
 
      <div class="admin-cards">
        <div class="admin-card">
          <h3>Vocabularies</h3>
          <p>The shared absence reasons and physical-test measures every kapa selects from.</p>
          <a href="#">Open →</a>
        </div>
        <div class="admin-card">
          <h3>Audit log</h3>
          <p>Every write and cross-kapa read, append-only and enforced in the database.</p>
          <a href="#">Open →</a>
        </div>
        <div class="admin-card">
          <h3>Exports</h3>
          <p>De-identified research data, ready for external analysis.</p>
          <a href="#">Open →</a>
        </div>
      </div>
 
      <p class="demo-note">Demonstration data only. All names, kapa and quotes are fictional.</p>
    </main>
 
    <!-- USERS TAB -->
    <main v-else-if="ui.activeNav === 'Users'" class="content">
      <div class="page-header">
        <h1>Users</h1>
        <button class="btn-primary" @click="openModal">Add user</button>
      </div>
 
      <div class="pills">
        <button
          v-for="f in filters"
          :key="f"
          :class="['pill', { active: activeFilter === f }]"
          @click="activeFilter = f"
        >
          {{ f }}
        </button>
      </div>
 
      <table class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Role</th>
            <th>Kapa</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
            <tr v-for="user in filteredUsers" :key="user.id">
                <td>{{ user.first_name }} {{ user.last_name }}</td>
                <td><span :class="['role-badge', user.role.replace('_', '-')]">{{ user.role }}</span></td>
                <td>{{ user.branch_name ?? '—' }}</td>
                <td><span :class="['status-badge', user.is_active ? 'active' : 'inactive']">{{ user.is_active ? 'Active' : 'Inactive' }}</span></td>
                <td class="edit-cell">
                    <a v-if="user.is_active" href="#" @click.prevent="handleDeactivate(user.id)">Deactivate</a>
                </td>
            </tr>
        </tbody>
      </table>
 
      <p class="demo-note">Demonstration data only. All names, kapa and quotes are fictional.</p>
    </main>
 
    <!-- OTHER TABS -->
    <main v-else class="content">
      <div class="placeholder-page">
        <h2>{{ ui.activeNav }}</h2>
        <p>This page is coming soon.</p>
      </div>
    </main>
 
  </div>
</template>
 
<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }
 
.sa-dashboard {
  min-height: 100vh;
  background: #f0ede6;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
 
.content { max-width: 1100px; margin: 0 auto; padding: 48px 24px; }
 
h1 { font-size: 28px; font-weight: 700; color: #1a1a1a; margin-bottom: 6px; }
.page-subtitle { font-size: 13px; color: #888; margin-bottom: 32px; }
 
.admin-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 48px; }
.admin-card { background: white; border-radius: 10px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.admin-card h3 { font-size: 16px; font-weight: 700; margin-bottom: 10px; color: #1a1a1a; }
.admin-card p { font-size: 13px; color: #777; line-height: 1.5; margin-bottom: 16px; }
.admin-card a { font-size: 13px; font-weight: 600; color: #1a1a1a; text-decoration: none; }
.admin-card a:hover { text-decoration: underline; }
 
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.btn-primary { background: #7a2e2e; color: white; border: none; border-radius: 6px; padding: 10px 18px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-primary:hover { background: #6a2424; }
 
.pills { display: flex; gap: 8px; margin-bottom: 20px; }
.pill { padding: 6px 16px; border: 1.5px solid #ccc; border-radius: 20px; font-size: 13px; background: white; cursor: pointer; color: #444; }
.pill:hover { border-color: #888; }
.pill.active { background: #1a1a1a; color: white; border-color: #1a1a1a; }
 
.data-table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }
.data-table th { text-align: left; padding: 12px 16px; font-size: 12px; font-weight: 600; color: #888; background: #f7f4ef; border-bottom: 1px solid #e8e2d8; }
.data-table td { padding: 14px 16px; font-size: 13px; border-bottom: 1px solid #f0ede6; color: #333; }
.data-table tr:last-child td { border-bottom: none; }
 
.role-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; background: #e8e2d8; color: #555; }
 
.status-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.status-badge.active  { background: #e6f4ec; color: #2a7a4a; }
.status-badge.pending { background: #e0f2f3; color: #2a7a7a; }
 
.edit-cell a { color: #7a2e2e; font-size: 13px; font-weight: 600; text-decoration: none; }
.edit-cell a:hover { text-decoration: underline; }
 
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: white; border-radius: 12px; padding: 32px; width: 480px; box-shadow: 0 8px 32px rgba(0,0,0,0.15); }
.modal h2 { font-size: 18px; font-weight: 700; margin-bottom: 24px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
.form-group label { font-size: 12px; font-weight: 600; color: #555; }
.form-group input, .form-group select { border: 1.5px solid #ddd; border-radius: 6px; padding: 8px 12px; font-size: 13px; outline: none; }
.form-group input:focus, .form-group select:focus { border-color: #4D9298; }
.form-error { background: #fdecea; color: #c0392b; border-radius: 6px; padding: 10px 14px; font-size: 13px; margin-bottom: 16px; }
.form-success { background: #e6f4ec; color: #2a7a4a; border-radius: 6px; padding: 14px; font-size: 13px; }
.form-success a { color: #2a7a4a; font-weight: 600; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.btn-cancel { background: #333; border: 1.5px solid #ddd; border-radius: 6px; padding: 8px 18px; font-size: 13px; cursor: pointer; }
.btn-cancel:hover { border-color: #888; }
 
.demo-note { text-align: center; font-size: 12px; color: #aaa; margin-top: 48px; }
 
.placeholder-page { text-align: center; padding: 80px; color: #aaa; }
.placeholder-page h2 { font-size: 20px; margin-bottom: 8px; color: #888; }
</style>
 
