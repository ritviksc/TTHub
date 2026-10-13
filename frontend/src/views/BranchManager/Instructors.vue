<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { listStaff, createStaffAccount, deactivateStaff, listSessions } from '@/apis.js'
import { auth } from '@/stores/auth.js'

const instructors = ref([])
const sessions = ref([])
const loading = ref(true)
const loadError = ref(null)
const search = ref('')
const activeFilter = ref('all') // 'all', 'active', 'inactive'

/* ---- create modal state ---- */
const showModal = ref(false)
const createError = ref(null)
const createLoading = ref(false)
const newInstructor = ref({
  email: '',
  first_name: '',
  last_name: '',
  password: '',
})

const branchName = computed(() => auth.user?.branch?.name ?? 'Your branch')

/* ---- session counts per instructor ---- */
const sessionsCountByInstructor = computed(() => {
  const map = {}
  for (const s of sessions.value) {
    const creatorId = s.created_by?.id || s.created_by
    if (creatorId) {
      map[creatorId] = (map[creatorId] || 0) + 1
    }
  }
  return map
})

/* ---- filtered instructors ---- */
const hasInstructors = computed(() => instructors.value.some(i => i.role === 'instructor'))

const emptyState = computed(() => {
  if (!hasInstructors.value) {
    return { title: 'No instructors yet', message: 'There are no instructors registered for this branch yet.' }
  }
  if (search.value.trim()) {
    return { title: 'No instructors found', message: `No instructors match your search term "${search.value.trim()}" within the selected filter.` }
  }
  if (activeFilter.value === 'inactive') {
    return { title: 'No inactive instructors', message: 'There are no deactivated instructor accounts in your branch.' }
  }
  return { title: 'No active instructors', message: 'There are no active instructor accounts in your branch.' }
})

function showAllInstructors() {
  activeFilter.value = 'all'
  search.value = ''
}

const filteredInstructors = computed(() => {
  const query = search.value.toLowerCase().trim()
  return instructors.value.filter(i => {
    // Role check: ensure it's an instructor
    if (i.role !== 'instructor') return false

    // Filter status
    if (activeFilter.value === 'active' && !i.is_active) return false
    if (activeFilter.value === 'inactive' && i.is_active) return false

    // Search query
    if (query) {
      const fullName = `${i.first_name || ''} ${i.last_name || ''}`.toLowerCase()
      const email = (i.email || '').toLowerCase()
      if (!fullName.includes(query) && !email.includes(query)) return false
    }

    return true
  })
})

function initials(person) {
  const first = person?.first_name?.[0] ?? ''
  const last = person?.last_name?.[0] ?? ''
  return (first + last || person?.email?.[0] || '?').toUpperCase()
}

async function load() {
  loading.value = true
  loadError.value = null
  try {
    const [staffData, sessionData] = await Promise.all([
      listStaff(),
      listSessions().catch(() => []),
    ])
    instructors.value = Array.isArray(staffData) ? staffData : (staffData.results || [])
    sessions.value = Array.isArray(sessionData) ? sessionData : (sessionData.results || [])
  } catch (err) {
    loadError.value = 'Could not load instructors for your branch.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

/* ---- modal methods ---- */
function openModal() {
  newInstructor.value = {
    email: '',
    first_name: '',
    last_name: '',
    password: '',
  }
  createError.value = null
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  createError.value = null
}

async function handleCreateInstructor() {
  createError.value = null
  createLoading.value = true
  try {
    await createStaffAccount({
      ...newInstructor.value,
      role: 'instructor',
      branch: auth.user?.branch?.id || auth.user?.branch,
    })
    closeModal()
    await load()
  } catch (err) {
    const data = err.response?.data
    if (data && typeof data === 'object') {
      createError.value = Object.entries(data)
        .map(([field, msg]) => `${field}: ${Array.isArray(msg) ? msg.join(' ') : msg}`)
        .join('; ')
    } else {
      createError.value = err.response?.data?.detail ?? 'Could not create instructor account.'
    }
  } finally {
    createLoading.value = false
  }
}

async function handleToggleActive(instructor) {
  const action = instructor.is_active ? 'deactivate' : 'reactivate'
  if (!confirm(`Are you sure you want to ${action} ${instructor.first_name || instructor.email}?`)) {
    return
  }

  try {
    await deactivateStaff(instructor.id)
    await load()
  } catch (err) {
    alert(`Could not ${action} instructor. Please try again.`)
  }
}
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <!-- Page Header -->
      <div class="page-header">
        <div>
          <h1>Kaimahi</h1>
          <p class="page-subtitle">Instructors delivering programmes at {{ branchName }}.</p>
        </div>
        <div class="header-actions">
          <button class="btn-primary" @click="openModal">+ Add Kaimahi</button>
        </div>
      </div>

      <!-- Controls: Search & Filters -->
      <div class="controls-row">
        <div class="search-wrap">
          <input
            v-model="search"
            type="search"
            class="search-input"
            placeholder="Search by name or email…"
          />
        </div>

        <div class="pills">
          <button
            :class="['pill', { active: activeFilter === 'all' }]"
            @click="activeFilter = 'all'"
          >
            All ({{ instructors.filter(i => i.role === 'instructor').length }})
          </button>
          <button
            :class="['pill', { active: activeFilter === 'active' }]"
            @click="activeFilter = 'active'"
          >
            Active ({{ instructors.filter(i => i.role === 'instructor' && i.is_active).length }})
          </button>
          <button
            :class="['pill', { active: activeFilter === 'inactive' }]"
            @click="activeFilter = 'inactive'"
          >
            Inactive ({{ instructors.filter(i => i.role === 'instructor' && !i.is_active).length }})
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <p v-if="loading" class="loading-note">Loading instructors…</p>

      <!-- Error State -->
      <div v-else-if="loadError" class="form-error">
        {{ loadError }}
        <button class="btn-cancel" style="margin-left: 12px;" @click="load">Try again</button>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredInstructors.length === 0" class="card empty-card">
        <h3>{{ emptyState.title }}</h3>
        <p>{{ emptyState.message }}</p>
        <button v-if="!hasInstructors" class="btn-primary" style="margin-top: 12px;" @click="openModal">+ Add your first instructor</button>
        <button v-else class="btn-primary" style="margin-top: 12px;" @click="showAllInstructors">Show all instructors</button>
      </div>

      <!-- Instructors Data Table -->
      <div v-else class="card table-card">
        <table class="data-table">
          <thead>
            <tr>
              <th>Instructor</th>
              <th>Email</th>
              <th>Status</th>
              <th>Sessions led</th>
              <th style="text-align: right;">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="inst in filteredInstructors" :key="inst.id">
              <td>
                <div class="user-cell">
                  <div class="initials-avatar">{{ initials(inst) }}</div>
                  <div>
                    <RouterLink
                      :to="{ name: 'staff-detail', params: { id: inst.id } }"
                      class="staff-name-link"
                    >
                      {{ inst.first_name }} {{ inst.last_name }}
                    </RouterLink>
                  </div>
                </div>
              </td>
              <td>{{ inst.email }}</td>
              <td>
                <span :class="['status-badge', inst.is_active ? 'active' : 'inactive']">
                  {{ inst.is_active ? 'Active' : 'Deactivated' }}
                </span>
              </td>
              <td>
                {{ sessionsCountByInstructor[inst.id] ?? 0 }}
              </td>
              <td style="text-align: right;">
                <button
                  v-if="inst.is_active"
                  class="btn-cancel btn-small"
                  @click="handleToggleActive(inst)"
                >
                  Deactivate
                </button>
                <RouterLink
                  v-else
                  :to="{ name: 'staff-detail', params: { id: inst.id } }"
                  class="btn-secondary btn-small"
                >
                  Manage
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Add Instructor Modal -->
      <div v-if="showModal" class="modal-backdrop" @click.self="closeModal">
        <div class="modal" role="dialog" aria-labelledby="modal-title">
          <div class="modal-header">
            <h2 id="modal-title">Add instructor</h2>
            <button class="modal-close" aria-label="Close" @click="closeModal">&times;</button>
          </div>

          <form @submit.prevent="handleCreateInstructor">
            <p class="modal-desc">
              Create an instructor account assigned to <strong>{{ branchName }}</strong>.
            </p>

            <div v-if="createError" class="form-error" style="margin-bottom: 16px;">
              {{ createError }}
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="modal-first-name">First name</label>
                <input
                  id="modal-first-name"
                  v-model="newInstructor.first_name"
                  type="text"
                  required
                  placeholder="First name"
                />
              </div>

              <div class="form-group">
                <label for="modal-last-name">Last name</label>
                <input
                  id="modal-last-name"
                  v-model="newInstructor.last_name"
                  type="text"
                  required
                  placeholder="Last name"
                />
              </div>
            </div>

            <div class="form-group">
              <label for="modal-email">Email address</label>
              <input
                id="modal-email"
                v-model="newInstructor.email"
                type="email"
                required
                placeholder="instructor@example.com"
              />
            </div>

            <div class="form-group">
              <label for="modal-password">Password</label>
              <input
                id="modal-password"
                v-model="newInstructor.password"
                type="password"
                required
                minlength="8"
                placeholder="At least 8 characters"
              />
              <span class="field-hint">The instructor will use this password to sign in.</span>
            </div>

            <div class="modal-actions">
              <button type="button" class="btn-cancel" @click="closeModal">Cancel</button>
              <button type="submit" class="btn-primary" :disabled="createLoading">
                {{ createLoading ? 'Creating…' : 'Create instructor' }}
              </button>
            </div>
          </form>
        </div>
      </div>

    </main>
  </div>
</template>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.controls-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.search-wrap {
  flex: 1;
  min-width: 260px;
  max-width: 420px;
}

.search-input {
  width: 100%;
  padding: 10px 16px;
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius-pill);
  background: var(--surface);
  color: var(--ink);
  font-size: var(--text-base);
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.search-input:focus {
  border-color: var(--teal);
  box-shadow: 0 0 0 3px var(--teal-tint);
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.staff-name-link {
  font-weight: 600;
  color: var(--text);
  text-decoration: none;
  transition: color 0.15s ease;
}

.staff-name-link:hover {
  text-decoration: underline;
  color: var(--teal);
}

.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 600;
}

.status-badge.active {
  background: var(--mint);
  color: var(--forest);
}

.status-badge.inactive {
  background: var(--sand-light);
  color: var(--bark);
}

.empty-card {
  text-align: center;
  padding: 48px 24px;
}

.table-card {
  padding: 0;
  overflow: hidden;
}

.btn-small {
  padding: 6px 12px;
  font-size: var(--text-xs);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--bark);
  padding: 4px 8px;
}

.modal-desc {
  color: var(--bark);
  font-size: var(--text-sm);
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border-faint);
}

.field-hint {
  display: block;
  font-size: var(--text-xs);
  color: var(--bark);
  margin-top: 4px;
}
</style>
