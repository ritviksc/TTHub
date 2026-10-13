<!---
 UserDetail.vue Super Admin: individual staff account page
 
  Reached from: /super-admin/users/:id  (e.g. /super-admin/users/42)
  Linked from:  Users.vue :each user's name is a RouterLink to this page
 
  Shows: name, role, branch, email, active status
  Actions: deactivate or reactivate account
-->
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listStaff, deactivateStaff, reactivateStaff } from '@/apis.js'

const route = useRoute()
const router = useRouter()
const userId = route.params.id
// route.params.id comes from the :id in the route path in router/index.js
// e.g. URL /super-admin/users/42 → userId = '42'

const user = ref(null)
const loading = ref(true)
const loadError = ref(null)
const actionError = ref(null)
const changingStatus = ref(false)
// --- state ---
// ROLE_LABELS maps database codes to readable strings e.g. 'branch_manager' → 'Branch Manager'
const ROLE_LABELS = {
  super_admin: 'Super Admin',
  branch_manager: 'Branch Manager',
  instructor: 'Instructor',
}
// --- data fetching ---
// No single-user endpoint exists so we fetch all staff and find the match by id
onMounted(async () => {
  try {
    const all = await listStaff()
    user.value = all.find(u => String(u.id) === String(userId)) ?? null
    if (!user.value) loadError.value = 'User not found.'
  } catch (e) {
    loadError.value = 'Could not load this user.'
  } finally {
    loading.value = false
  }
})
// --- actions ---
async function handleToggleActive() {
  if (changingStatus.value) return
  const active = user.value.is_active
  if (!confirm(active ? 'Deactivate this account?' : 'Reactivate this account? They will be able to sign in again.')) return
  changingStatus.value = true
  actionError.value = null
  try {
    const result = await (active ? deactivateStaff : reactivateStaff)(user.value.id)
    user.value.is_active = result.is_active
  } catch (e) {
    actionError.value = `Could not ${active ? 'deactivate' : 'reactivate'} this account.`
  } finally {
    changingStatus.value = false
  }
}
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <a class="back-link" @click.prevent="router.push('/super-admin/users')" href="#">&lsaquo; All users</a>
<!-- loading → error → content (same three-state pattern used across all pages) -->
      <p v-if="loading" class="loading-note">Loading…</p>
      <div v-else-if="loadError" class="form-error">{{ loadError }}</div>

      <template v-else-if="user">
        <div class="page-header">
          <div>
            <h1>{{ user.first_name }} {{ user.last_name }}</h1>
            <p class="page-subtitle">{{ ROLE_LABELS[user.role] ?? user.role }}</p>
          </div>
          <button
            :class="user.is_active ? 'btn-cancel' : 'btn-primary'"
            :disabled="changingStatus"
            @click="handleToggleActive"
          >
            {{ changingStatus ? 'Saving…' : user.is_active ? 'Deactivate account' : 'Reactivate account' }}
          </button>
        </div>

        <div v-if="actionError" class="form-error">{{ actionError }}</div>

        <section class="panel">
          <dl class="detail-grid">
            <div>
              <dt>Email</dt>
              <dd>{{ user.email }}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{{ ROLE_LABELS[user.role] ?? user.role }}</dd>
            </div>
            <div>
              <dt>Branch</dt>
              <dd>{{ user.branch_name ?? '—' }}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <span :class="['status-badge', user.is_active ? 'active' : 'inactive']">
                  {{ user.is_active ? 'Active' : 'Inactive' }}
                </span>
              </dd>
            </div>
          </dl>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.panel {
  background: var(--surface); border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card); padding: 24px;
}
.detail-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px 24px; margin: 0;
}
.detail-grid dt { font-size: var(--text-sm); font-weight: 600; color: var(--text-muted); margin-bottom: 4px; }
.detail-grid dd { margin: 0; font-size: var(--text-md); color: var(--text); }
</style>
