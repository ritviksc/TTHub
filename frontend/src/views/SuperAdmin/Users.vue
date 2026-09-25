<script setup>
import { ref, computed, onMounted } from "vue";
import { RouterLink } from 'vue-router'
import {
  createStaffAccount,
  listBranches,
  listStaff,
  deactivateStaff,
} from "@/apis.js";

const users = ref([]);
const loadError = ref(null);

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

async function load() {
  try {
    users.value = await listStaff();
    loadError.value = null;
  } catch (e) {
    users.value = [];
    loadError.value = "Could not load the user list.";
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

/* ---- deactivate ---- */

async function handleDeactivate(id) {
  if (!confirm("Deactivate this account?")) return;
  try {
    await deactivateStaff(id);
    await load();
  } catch (e) {
    loadError.value = "Could not deactivate this account.";
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

      <table class="data-table">
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
              <RouterLink :to="`/super-admin/users/${user.id}`" class="user-link">
                
              <RouterLink :to="`/staff/${user.id}`" class="user-link">
                {{ user.first_name }} {{ user.last_name }}
              </RouterLink>
            
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
              <a
                v-if="user.is_active"
                href="#"
                @click.prevent="handleDeactivate(user.id)"
                >Deactivate</a
              >
            </td>
          </tr>
          <tr v-if="!filteredUsers.length">
            <td colspan="6" class="empty-row">No users match this filter.</td>
          </tr>
        </tbody>
      </table>
    </main>
  </div>
</template>

<style scoped>
/* Filter bar holds role pills and branch dropdown side by side */
.filter-bar { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.filter-bar .pills { margin-bottom: 0; }
.branch-select {
  border: 1.5px solid var(--border-strong); border-radius: var(--radius-sm);
  padding: 6px 12px; font-size: var(--text-base); background: var(--surface); color: var(--text);
}
.user-link { font-weight: 600; color: var(--text); text-decoration: none; }
.user-link:hover { color: var(--teal); }
.empty-row { text-align: center; color: var(--text-faint); padding: 32px 16px; }
.empty-row {
  text-align: center;
  color: var(--text-faint);
  padding: 32px 16px;
}
.user-link {
  color: var(--text);
  font-weight: 600;
}

.user-link:hover {
  color: var(--maroon);
  text-decoration: none;
}
</style>
