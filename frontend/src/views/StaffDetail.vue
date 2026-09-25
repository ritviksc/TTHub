<script setup>
import { ref, computed, onMounted } from "vue";
import { RouterLink, useRoute } from "vue-router";
import {
  getStaff,
  updateStaff,
  deactivateStaff,
  listBranches,
} from "@/apis.js";
import { auth } from "@/stores/auth.js";

const route = useRoute();
const staffId = route.params.id;

const staff = ref(null);
const branches = ref([]);

const loading = ref(true);
const loadError = ref(null);

const editing = ref(false);
const draft = ref({});
const saveError = ref(null);
const saving = ref(false);
const deactivating = ref(false);

const isSuperAdmin = computed(() => auth.user?.role === "super_admin");

const backPath = computed(() =>
  isSuperAdmin.value ? "/super-admin/users" : "/branch-manager/instructors",
);

const backLabel = computed(() =>
  isSuperAdmin.value ? "All users" : "Instructors",
);

const roleLabels = {
  super_admin: "Super Admin",
  branch_manager: "Branch Manager",
  instructor: "Instructor",
};

const roleLabel = computed(() => {
  return roleLabels[staff.value?.role] ?? staff.value?.role ?? "—";
});

const branchName = computed(() => {
  const branch = branches.value.find(
    (b) => String(b.id) === String(staff.value?.branch),
  );

  return branch?.name ?? staff.value?.branch_name ?? "No branch assigned";
});

function initials(person) {
  const first = person?.first_name?.[0] ?? "";
  const last = person?.last_name?.[0] ?? "";

  return (first + last || person?.email?.[0] || "?").toUpperCase();
}

async function load() {
  loading.value = true;
  loadError.value = null;

  try {
    staff.value = await getStaff(staffId);
  } catch (error) {
    staff.value = null;

    if (error.response?.status === 404) {
      loadError.value =
        "That staff account does not exist, or you do not have access to it.";
    } else {
      loadError.value = "Could not load this staff account.";
    }

    loading.value = false;
    return;
  }

  try {
    branches.value = await listBranches();
  } catch {
    branches.value = [];
  }

  loading.value = false;
}

onMounted(load);

function startEdit() {
  draft.value = {
    first_name: staff.value.first_name ?? "",
    last_name: staff.value.last_name ?? "",
    email: staff.value.email ?? "",
    role: staff.value.role,
    branch: staff.value.branch ?? "",
  };

  saveError.value = null;
  editing.value = true;
}

function cancelEdit() {
  editing.value = false;
  saveError.value = null;
}

async function save() {
  saving.value = true;
  saveError.value = null;

  try {
    staff.value = await updateStaff(staffId, draft.value);

    editing.value = false;
  } catch (error) {
    const data = error.response?.data;

    saveError.value =
      data?.email?.[0] ??
      data?.branch?.[0] ??
      data?.role?.[0] ??
      data?.detail ??
      (typeof data === "string" ? data : "Could not save these changes.");
  } finally {
    saving.value = false;
  }
}

async function handleDeactivate() {
  const name =
    `${staff.value.first_name} ${staff.value.last_name}`.trim() ||
    staff.value.email;

  if (!confirm(`Deactivate ${name}? They will no longer be able to sign in.`)) {
    return;
  }

  deactivating.value = true;
  saveError.value = null;

  try {
    const result = await deactivateStaff(staffId);

    staff.value = {
      ...staff.value,
      is_active: result.is_active,
    };
  } catch (error) {
    saveError.value =
      error.response?.data?.detail ?? "Could not deactivate this account.";
  } finally {
    deactivating.value = false;
  }
}
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <!-- Back -->
      <RouterLink :to="backPath" class="back-link">
        &lsaquo; {{ backLabel }}
      </RouterLink>

      <!-- Error -->
      <div v-if="loadError" class="form-error">
        {{ loadError }}
      </div>

      <!-- Loading -->
      <p v-else-if="loading" class="loading-note">Loading staff account…</p>

      <!-- Staff page -->
      <template v-else-if="staff">
        <div v-if="saveError" class="form-error" role="alert">
          {{ saveError }}
        </div>
        <!-- Header -->
        <div class="page-header staff-header">
          <div class="identity">
            <span class="initials-avatar lg">
              {{ initials(staff) }}
            </span>

            <div>
              <h1>
                {{ staff.first_name }}
                {{ staff.last_name }}
              </h1>

              <div class="page-subtitle identity-meta">
                <span>{{ roleLabel }}</span>

                <span>·</span>

                <span>{{ branchName }}</span>

                <span
                  :class="[
                    'status-badge',
                    staff.is_active ? 'active' : 'inactive',
                  ]"
                >
                  {{ staff.is_active ? "Active" : "Inactive" }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="!editing" class="header-actions">
            <button
              v-if="staff.is_active"
              class="btn-danger"
              :disabled="deactivating"
              @click="handleDeactivate"
            >
              {{ deactivating ? "Deactivating…" : "Deactivate" }}
            </button>

            <button class="btn-primary" @click="startEdit">Edit details</button>
          </div>
        </div>

        <!-- Account Details -->
        <section class="panel">
          <div class="section-heading">
            <div>
              <h2>Account details</h2>

              <p>Staff identity, access role and branch assignment.</p>
            </div>
          </div>

          <!-- Edit form -->
          <form v-if="editing" class="edit-form" @submit.prevent="save">
            <div class="form-row">
              <div class="form-group">
                <label for="sd-first"> First name </label>

                <input id="sd-first" v-model="draft.first_name" required />
              </div>

              <div class="form-group">
                <label for="sd-last"> Last name </label>

                <input id="sd-last" v-model="draft.last_name" required />
              </div>
            </div>

            <div class="form-group">
              <label for="sd-email"> Email </label>

              <input
                id="sd-email"
                v-model="draft.email"
                type="email"
                required
              />

              <span class="field-help">
                This email is also used as the sign-in username.
              </span>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="sd-role"> Role </label>

                <select
                  id="sd-role"
                  v-model="draft.role"
                  :disabled="!isSuperAdmin"
                >
                  <option value="instructor">Instructor</option>

                  <option value="branch_manager">Branch Manager</option>

                  <option value="super_admin">Super Admin</option>
                </select>
              </div>

              <div class="form-group">
                <label for="sd-branch"> Branch </label>

                <select
                  id="sd-branch"
                  v-model="draft.branch"
                  :disabled="!isSuperAdmin"
                >
                  <option value="">No branch</option>

                  <option
                    v-for="branch in branches"
                    :key="branch.id"
                    :value="branch.id"
                  >
                    {{ branch.name }}
                  </option>
                </select>
              </div>
            </div>

            <p v-if="!isSuperAdmin" class="field-help permission-note">
              Branch Managers can edit instructor details, but role and branch
              assignments are managed by a Super Admin.
            </p>

            <div class="edit-actions">
              <button type="button" class="btn-cancel" @click="cancelEdit">
                Cancel
              </button>

              <button type="submit" class="btn-primary" :disabled="saving">
                {{ saving ? "Saving…" : "Save changes" }}
              </button>
            </div>
          </form>

          <!-- Read-only details -->
          <dl v-else class="detail-grid">
            <div>
              <dt>First name</dt>
              <dd>
                {{ staff.first_name || "—" }}
              </dd>
            </div>

            <div>
              <dt>Last name</dt>
              <dd>
                {{ staff.last_name || "—" }}
              </dd>
            </div>

            <div>
              <dt>Email</dt>
              <dd>
                {{ staff.email || "—" }}
              </dd>
            </div>

            <div>
              <dt>Role</dt>
              <dd>
                {{ roleLabel }}
              </dd>
            </div>

            <div>
              <dt>Branch</dt>
              <dd>
                {{ branchName }}
              </dd>
            </div>

            <div>
              <dt>Account status</dt>
              <dd>
                <span
                  :class="[
                    'status-badge',
                    staff.is_active ? 'active' : 'inactive',
                  ]"
                >
                  {{ staff.is_active ? "Active" : "Inactive" }}
                </span>
              </dd>
            </div>
          </dl>
        </section>

        <!-- Access -->
        <section class="panel access-panel">
          <h2>Access</h2>

          <div class="access-row">
            <div>
              <strong>
                {{ roleLabel }}
              </strong>

              <p>
                {{
                  staff.role === "super_admin"
                    ? "National access across all branches."
                    : staff.role === "branch_manager"
                      ? "Management access scoped to the assigned branch."
                      : "Instructor access scoped to the assigned branch."
                }}
              </p>
            </div>

            <span
              :class="['status-badge', staff.is_active ? 'active' : 'inactive']"
            >
              {{ staff.is_active ? "Can sign in" : "Sign-in disabled" }}
            </span>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.staff-header {
  align-items: flex-start;
}

.identity {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.identity h1 {
  margin-bottom: 4px;
}

.identity-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 0;
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.btn-danger {
  background: var(--surface);
  color: var(--danger);
  border: 1.5px solid var(--danger);
  border-radius: var(--radius-sm);
  padding: 8px 18px;
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
}

.btn-danger:hover:not(:disabled) {
  background: var(--danger-bg);
}

.btn-danger:disabled,
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.panel {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 24px;
  margin-bottom: 24px;
}

.section-heading {
  margin-bottom: 20px;
}

.section-heading p {
  margin: 5px 0 0;
  color: var(--text-muted);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 22px 40px;
}

.detail-grid dt {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 5px;
}

.detail-grid dd {
  margin: 0;
  color: var(--text);
  font-size: var(--text-base);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.form-group {
  margin-bottom: 18px;
}

.form-group label {
  display: block;
  margin-bottom: 7px;
  font-weight: 600;
}

.form-group input,
.form-group select {
  width: 100%;
  box-sizing: border-box;
}

.field-help {
  display: block;
  margin-top: 5px;
  color: var(--text-muted);
  font-size: 13px;
}

.permission-note {
  margin-bottom: 18px;
}

.form-error {
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  background: var(--danger-bg);
  color: var(--danger);
  margin: 16px 0;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

.btn-cancel {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: var(--radius-sm);
  padding: 8px 18px;
  cursor: pointer;
}

.access-panel h2 {
  margin-bottom: 18px;
}

.access-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.access-row strong {
  display: block;
  margin-bottom: 5px;
}

.access-row p {
  margin: 0;
  color: var(--text-muted);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.active {
  background: var(--success-bg);
  color: var(--success);
}

.status-badge.inactive {
  background: var(--danger-bg);
  color: var(--danger);
}

.initials-avatar.lg {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 700;
  font-size: 20px;
  background: var(--maroon);
  color: white;
}

.loading-note {
  color: var(--text-muted);
}

@media (max-width: 700px) {
  .staff-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions button {
    flex: 1;
  }

  .detail-grid,
  .form-row {
    grid-template-columns: 1fr;
  }

  .access-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
