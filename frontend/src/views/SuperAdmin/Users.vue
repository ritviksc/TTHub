<script setup>
import { ref, computed, onMounted } from "vue";
import { RouterLink } from 'vue-router'
import {
  createStaffAccount,
  listBranches,
  listStaff,
  deactivateStaff,
  reactivateStaff,
} from "@/apis.js";

const users = ref([]);
const loadError = ref(null);
const loading = ref(true);
const changingStatus = ref(false);
const actionError = ref(null);

const activeFilter = ref("All");
const filters = ["All", "Branch Managers", "Instructors", "Super Admins"];

const ROLE_FOR_FILTER = {
  "Branch Managers": "branch_manager",
  Instructors: "instructor",
  "Super Admins": "super_admin",
};
//Branch filter state:branchOptions is loadedon mount
const selectedBranch = ref('')
const branchOptions = ref([])
const filteredUsers = computed(() => {
  const role = ROLE_FOR_FILTER[activeFilter.value]
  // Filter by role and branch: empty string means "show all"
  return users.value.filter(u => {
    const matchesRole = !role || u.role === role
    const matchesBranch = !selectedBranch.value || u.branch_name === selectedBranch.value
    return matchesRole && matchesBranch
  })
})

const hasFilters = computed(() => activeFilter.value !== 'All' || !!selectedBranch.value)
const emptyState = computed(() => {
  if (!hasFilters.value) {
    return { title: 'No other users yet', message: 'There are no other staff accounts to manage.' }
  }
  const role = activeFilter.value === 'All' ? 'users' : activeFilter.value.toLowerCase()
  const scope = selectedBranch.value ? 'in the selected branch' : 'across all branches'
  return { title: `No ${role} found`, message: `There are no ${role} matching this filter ${scope}.` }
})
function showAllUsers() {
  activeFilter.value = 'All'
  selectedBranch.value = ''
}

async function load() {
  loading.value = true;
  try {
    users.value = await listStaff();
    loadError.value = null;
  } catch (e) {
    users.value = [];
    loadError.value = "Could not load the user list.";
  } finally {
    loading.value = false;
  }
}

// Also fetch branches on mount so the branch filter dropdown has options
onMounted(async () => {
  await load()
  try { branchOptions.value = await listBranches() } catch (e) {}
})

/* ---- create ---- */

const emptyStaff = () => ({
  email: "",
  password: "",
  first_name: "",
  last_name: "",
  role: "branch_manager",
  branch: "",
});

const showModal = ref(false);
const branches = ref([]);
const createError = ref(null);
const createSuccess = ref(false);
const newStaff = ref(emptyStaff());

async function openModal() {
  showModal.value = true;
  createError.value = null;
  createSuccess.value = false;
  newStaff.value = emptyStaff();
  try {
    branches.value = await listBranches();
  } catch (e) {
    branches.value = [];
  }
}

async function submitCreateStaff() {
  createError.value = null;
  try {
    await createStaffAccount(newStaff.value);
    createSuccess.value = true;
    newStaff.value = emptyStaff();
    await load();
  } catch (e) {
    createError.value = e.response?.data?.detail ?? "Failed to create account.";
  }
}

/* ---- account status ---- */

async function handleToggleActive(user) {
  if (changingStatus.value) return;
  const action = user.is_active ? 'deactivate' : 'reactivate';
  if (!confirm(user.is_active ? "Deactivate this account?" : "Reactivate this account? They will be able to sign in again.")) return;
  changingStatus.value = true;
  actionError.value = null;
  try {
    const result = await (user.is_active ? deactivateStaff : reactivateStaff)(user.id);
    user.is_active = result.is_active;
  } catch (e) {
    actionError.value = e.response?.data?.detail ?? `Could not ${action} this account.`;
  } finally {
    changingStatus.value = false;
  }
}
</script>

<template>
  <div class="dash-page">
    <!-- Create Staff Account Modal -->
    <div
      v-if="showModal"
      class="modal-backdrop"
      @click.self="showModal = false"
    >
      <div class="modal">
        <h2>Create staff account</h2>

        <div v-if="createSuccess" class="form-success">
          Account created successfully.
          <a href="#" @click.prevent="createSuccess = false">Add another</a>
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
            <input v-model="newStaff.email" type="email" required />
          </div>

          <div class="form-group">
            <label>Password</label>
            <input
              v-model="newStaff.password"
              type="password"
              minlength="8"
              required
            />
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
            <label>Branch</label>
            <select v-model="newStaff.branch" required>
              <option value="" disabled>Select a branch</option>
              <option v-for="b in branches" :key="b.id" :value="b.id">
                {{ b.name }}
              </option>
            </select>
          </div>

          <div v-if="createError" class="form-error">{{ createError }}</div>

          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="showModal = false">
              Cancel
            </button>
            <button type="submit" class="btn-primary">Create account</button>
          </div>
        </form>
      </div>
    </div>

    <main class="content">
      <div class="page-header">
        <h1>Users</h1>
        <button class="btn-primary" @click="openModal">Add user</button>
      </div>

      <div v-if="loadError" class="form-error">{{ loadError }}</div>
      <div v-if="actionError" class="form-error" role="alert">{{ actionError }}</div>

       <!-- Role pills + branch dropdown sit in one row -->
      <div class="filter-bar">
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
        <select v-model="selectedBranch" class="branch-select">
          <option value="">All branches</option>
          <option v-for="b in branchOptions" :key="b.id" :value="b.name">{{ b.name }}</option>
        </select>
      </div>

      <p v-if="loading" class="loading-note">Loading users…</p>
      <table v-else-if="!loadError" class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Branch</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <!-- Link to user detail page -->
            <td>
              <RouterLink :to="{ name: 'staff-detail', params: { id: user.id } }" class="user-link">
                {{ user.first_name }} {{ user.last_name }}
              </RouterLink>
            </td>            
            <td>{{ user.email }}</td>
            <td>
              <span class="role-badge">{{ user.role }}</span>
            </td>
            <td>{{ user.branch_name ?? "—" }}</td>
            <td>
              <span
                :class="[
                  'status-badge',
                  user.is_active ? 'active' : 'inactive',
                ]"
              >
                {{ user.is_active ? "Active" : "Inactive" }}
              </span>
            </td>
            <td class="edit-cell">
              <button
                class="btn-cancel btn-small"
                :class="user.is_active ? 'btn-deactivate' : 'btn-reactivate'"
                :disabled="changingStatus"
                @click="handleToggleActive(user)"
                >{{ user.is_active ? 'Deactivate' : 'Reactivate' }}</button
              >
            </td>
          </tr>
          <tr v-if="!filteredUsers.length">
            <td colspan="6" class="empty-row">
              <h3>{{ emptyState.title }}</h3>
              <p>{{ emptyState.message }}</p>
              <button v-if="hasFilters" class="btn-primary" @click="showAllUsers">Show all users</button>
              <button v-else class="btn-primary" @click="openModal">Add user</button>
            </td>
          </tr>
        </tbody>
      </table>
    </main>
  </div>
</template>

<style scoped>
/* Filter bar holds role pills and branch dropdown side by side */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.filter-bar .pills {
  margin-bottom: 0;
}
.branch-select {
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius-sm);
  padding: 8px 14px;
  font-size: var(--text-base);
  background: var(--surface);
  color: var(--text);
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.branch-select:focus {
  border-color: var(--teal);
  box-shadow: 0 0 0 3px var(--teal-tint);
}
.user-link {
  font-weight: 600;
  color: var(--text);
  text-decoration: none;
  transition: color 0.15s ease;
}
.user-link:hover {
  color: var(--teal);
  text-decoration: underline;
}
.empty-row {
  text-align: center;
  color: var(--text-muted);
  padding: 32px 16px;
}
</style>
