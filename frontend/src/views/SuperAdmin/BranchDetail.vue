<script setup>
import { ref, computed, reactive, onMounted, onErrorCaptured } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import {
  getBranch,
  updateBranch,
  deleteBranch,
  assignBranchManager,
  removeBranchManager,
  assignBranchInstructor,
  removeBranchInstructor,
  listParticipants,
  listStaff,
} from '@/apis.js'

const route = useRoute()
const router = useRouter()
const branchId = route.params.id

const branch = ref(null)
const participants = ref([])
const staff = ref([])
const loading = ref(true)
const loadError = ref(null)

const PENDING_DATA = 'Needs session and questionnaire records, which do not exist yet.'

const ROLE_LABELS = {
  branch_manager: 'Branch Manager',
  instructor: 'Instructor',
}

const activeCount = computed(() => participants.value.filter(p => p.is_active).length)

async function loadBranch() {
  branch.value = await getBranch(branchId)
}

async function loadStaff() {
  try { staff.value = await listStaff() } catch (e) { /* keep what we had */ }
}

async function load() {
  loading.value = true
  try {
    // The branch is the page; the panels below it are extras, so a failure to
    // load those should not blank the whole screen.
    await loadBranch()
    loadError.value = null
  } catch (e) {
    branch.value = null
    loadError.value = e.response?.status === 404
      ? 'That branch does not exist, or you do not have access to it.'
      : 'Could not load this branch.'
    loading.value = false
    return
  }

  try {
    participants.value = await listParticipants({ branch: branchId })
  } catch (e) {
    participants.value = []
  }

  await loadStaff()
  loading.value = false
}

// A thrown render aborts Vue's patch and leaves whatever was on screen, which
// is how a template bug shows up as a page stuck on "Loading branch…".
// Surfacing it beats staring at a spinner.
onErrorCaptured((err) => {
  loading.value = false
  loadError.value = `Something went wrong rendering this page: ${err.message}`
  return false
})

onMounted(load)

/* ---- edit ---- */

const editing = ref(false)
const draft = ref({ name: '', region: '' })
const saveError = ref(null)
const saving = ref(false)

function startEdit() {
  draft.value = { name: branch.value.name, region: branch.value.region ?? '' }
  saveError.value = null
  editing.value = true
}

async function save() {
  saving.value = true
  saveError.value = null
  try {
    branch.value = await updateBranch(branchId, draft.value)
    editing.value = false
  } catch (e) {
    const data = e.response?.data
    saveError.value = e.response?.status === 403
      ? 'Only a Super Admin can edit a branch.'
      : data?.name?.[0] ?? data?.detail ?? 'Could not save these changes.'
  } finally {
    saving.value = false
  }
}

/* ---- delete ---- */

const deleting = ref(false)

async function handleDelete() {
  if (!confirm(`Delete ${branch.value.name}? This cannot be undone.`)) return

  deleting.value = true
  saveError.value = null
  try {
    await deleteBranch(branchId)
    router.push('/super-admin/branches')
  } catch (e) {
    // 409 carries the reason it is still in use, which is the useful part.
    saveError.value = e.response?.data?.detail ?? 'Could not delete this branch.'
  } finally {
    deleting.value = false
  }
}

/* ---- staff panels ----
   Managers and instructors behave identically, so they share one factory here
   and one block in the template. Two copies would only drift. */

function staffPanel({ key, title, assign, remove, note, emptyText, warnWhenEmpty }) {
  const selected = ref('')
  const message = ref(null)
  const error = ref(null)
  const busy = ref(false)

  const people = computed(() => branch.value?.[key] ?? [])

  // Anyone active who is not a Super Admin and is not already on this branch in
  // this role. The other role's people are included on purpose: picking one
  // moves them across, and the note under the picker says so.
  const assignable = computed(() => {
    const alreadyHere = new Set(people.value.map(p => p.id))
    return staff.value.filter(
      u => u.is_active && u.role !== 'super_admin' && !alreadyHere.has(u.id)
    )
  })

  async function refresh() {
    await loadBranch()
    await loadStaff()
  }

  async function handleAssign() {
    if (!selected.value) return

    busy.value = true
    error.value = null
    message.value = null
    try {
      const result = await assign(branchId, selected.value)

      const notes = []
      if (result.role_changed) notes.push(`role changed to ${ROLE_LABELS[result.role]}`)
      if (result.moved_from) notes.push(`moved from ${result.moved_from}`)
      message.value = notes.length
        ? `${result.name} assigned — ${notes.join(', ')}.`
        : `${result.name} assigned.`

      selected.value = ''
      await refresh()
    } catch (e) {
      error.value = e.response?.data?.detail ?? 'Could not assign that person.'
    } finally {
      busy.value = false
    }
  }

  async function handleRemove(person) {
    if (!confirm(`Remove ${person.name} from this branch?`)) return

    busy.value = true
    error.value = null
    message.value = null
    try {
      await remove(branchId, person.id)
      message.value = `${person.name} is no longer assigned to a branch. Their account is unchanged.`
      await refresh()
    } catch (e) {
      error.value = e.response?.data?.detail ?? 'Could not remove that person.'
    } finally {
      busy.value = false
    }
  }

  // reactive() so the template unwraps these refs. A plain object would hand
  // the template the Ref objects themselves, and `v-for` over a ComputedRef
  // yields undefined entries that blow up on `:key`.
  return reactive({
    key, title, note, emptyText, warnWhenEmpty,
    selected, message, error, busy, people, assignable,
    handleAssign, handleRemove,
  })
}

function staffLabel(u) {
  const name = `${u.first_name ?? ''} ${u.last_name ?? ''}`.trim() || u.email
  const role = ROLE_LABELS[u.role] ?? u.role
  return u.branch_name ? `${name} — ${role}, ${u.branch_name}` : `${name} — ${role}, unassigned`
}

const panels = [
  staffPanel({
    key: 'managers',
    title: 'Branch managers',
    assign: assignBranchManager,
    remove: removeBranchManager,
    emptyText: 'This branch has nobody managing it.',
    warnWhenEmpty: true,
    note: 'Assigning makes this person a Branch Manager and moves them off any '
        + 'branch they currently belong to. Removing only unassigns them — the '
        + 'account stays active and can be assigned elsewhere.',
  }),
  staffPanel({
    key: 'instructors',
    title: 'Instructors',
    assign: assignBranchInstructor,
    remove: removeBranchInstructor,
    emptyText: 'No instructors are assigned to this branch yet.',
    warnWhenEmpty: false,
    note: 'Assigning makes this person an Instructor and moves them off any '
        + 'branch they currently belong to. Removing only unassigns them — the '
        + 'account stays active and can be assigned elsewhere.',
  }),
]
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <RouterLink to="/super-admin/branches" class="back-link">&lsaquo; All branches</RouterLink>

      <div v-if="loadError" class="form-error">{{ loadError }}</div>
      <p v-else-if="loading" class="loading-note">Loading branch…</p>

      <template v-else-if="branch">
        <div class="page-header">
          <div>
            <h1>{{ branch.name }}</h1>
            <p class="page-subtitle">{{ branch.region || 'No region recorded' }}</p>
          </div>
          <button v-if="!editing" class="btn-primary" @click="startEdit">Edit details</button>
        </div>

        <!-- Details -->
        <section class="panel">
          <h2>Details</h2>

          <form v-if="editing" class="edit-form" @submit.prevent="save">
            <div class="form-row">
              <div class="form-group">
                <label for="branch-name">Name</label>
                <input id="branch-name" v-model="draft.name" required />
              </div>
              <div class="form-group">
                <label for="branch-region">Region</label>
                <input id="branch-region" v-model="draft.region" />
              </div>
            </div>

            <div v-if="saveError" class="form-error">{{ saveError }}</div>

            <div class="edit-actions">
              <button type="button" class="btn-danger" :disabled="deleting" @click="handleDelete">
                {{ deleting ? 'Deleting…' : 'Delete branch' }}
              </button>

              <div class="modal-actions">
                <button type="button" class="btn-cancel" @click="editing = false">Cancel</button>
                <button type="submit" class="btn-primary" :disabled="saving">
                  {{ saving ? 'Saving…' : 'Save changes' }}
                </button>
              </div>
            </div>

            <p class="delete-note">
              A branch can only be deleted once no staff or participants are attached to it.
            </p>
          </form>

          <dl v-else class="detail-grid">
            <div>
              <dt>Name</dt>
              <dd>{{ branch.name }}</dd>
            </div>
            <div>
              <dt>Region</dt>
              <dd>{{ branch.region || '—' }}</dd>
            </div>
            <div>
              <dt>Active participants</dt>
              <dd>{{ branch.participant_count }}</dd>
            </div>
            <div>
              <dt>Attendance</dt>
              <dd class="not-tracked" :title="PENDING_DATA">—</dd>
            </div>
            <div>
              <dt>Questionnaire</dt>
              <dd class="not-tracked" :title="PENDING_DATA">—</dd>
            </div>
          </dl>
        </section>

        <!-- Branch managers, then instructors: one block, rendered twice -->
        <section v-for="panel in panels" :key="panel.key" class="panel">
          <div class="panel-header">
            <h2>{{ panel.title }}</h2>
            <span class="result-count">{{ panel.people.length }}</span>
          </div>

          <div v-if="panel.error" class="form-error">{{ panel.error }}</div>
          <p v-if="panel.message" class="form-success">{{ panel.message }}</p>

          <ul v-if="panel.people.length" class="staff-list">
            <li v-for="person in panel.people" :key="person.id">
              <span>
                <span class="staff-name">{{ person.name }}</span>
                <span v-if="person.email" class="staff-email">{{ person.email }}</span>
              </span>
              <button
                type="button"
                class="link-danger"
                :disabled="panel.busy"
                @click="panel.handleRemove(person)"
              >
                Remove
              </button>
            </li>
          </ul>
          <p v-else class="no-staff">
            <span v-if="panel.warnWhenEmpty" class="badge-warning">No manager</span>
            {{ panel.emptyText }}
          </p>

          <div class="assign-row">
            <div class="form-group">
              <label :for="`assign-${panel.key}`">Assign</label>
              <select
                :id="`assign-${panel.key}`"
                v-model="panel.selected"
                :disabled="panel.busy"
              >
                <option value="" disabled>Select a staff member</option>
                <option v-for="u in panel.assignable" :key="u.id" :value="u.id">
                  {{ staffLabel(u) }}
                </option>
              </select>
            </div>
            <button
              type="button"
              class="btn-primary"
              :disabled="!panel.selected || panel.busy"
              @click="panel.handleAssign"
            >
              Assign
            </button>
          </div>

          <p class="assign-note">{{ panel.note }}</p>
        </section>

        <!-- Participants -->
        <section class="panel">
          <div class="panel-header">
            <h2>Participants</h2>
            <span class="result-count">{{ activeCount }} active of {{ participants.length }}</span>
          </div>

          <table class="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Phone</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in participants" :key="p.id">
                <td>
                  <span class="staff-name">{{ p.full_name }}</span>
                  <span v-if="p.preferred_name" class="staff-email">{{ p.preferred_name }}</span>
                </td>
                <td>{{ p.phone || '—' }}</td>
                <td>
                  <span :class="['status-badge', p.is_active ? 'active' : 'inactive']">
                    {{ p.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
              </tr>
              <tr v-if="!participants.length">
                <td colspan="3" class="empty-row">No participants recorded for this branch yet.</td>
              </tr>
            </tbody>
          </table>
        </section>

        <p class="table-note">
          Attendance, questionnaire returns and summary insights appear here once
          sessions and questionnaires are recorded.
        </p>
      </template>
    </main>
  </div>
</template>

<style scoped>
/* Every colour here is a theme.css token — nothing hardcoded. */

.panel {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 24px;
  margin-bottom: 24px;
}

.panel-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 16px;
}

.panel h2 { margin-bottom: 16px; }
.panel-header h2 { margin-bottom: 0; }

/* Label over value, wrapping across the panel rather than a rigid grid, so a
   long branch name does not squash its neighbours. */
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px 24px;
  margin: 0;
}
.detail-grid dt {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.detail-grid dd {
  margin: 0;
  font-size: var(--text-md);
  color: var(--text);
}

/* Delete sits opposite Save/Cancel so it is never the button you hit by
   reflex on your way to saving. */
.edit-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 8px;
}
.edit-actions .modal-actions { margin-top: 0; }

.btn-danger {
  background: var(--surface);
  color: var(--danger);
  border: 1.5px solid var(--danger);
  border-radius: var(--radius-sm);
  padding: 8px 18px;
  font-size: var(--text-base);
  font-weight: 600;
}
.btn-danger:hover:not(:disabled) { background: var(--danger-bg); }

.delete-note {
  font-size: var(--text-sm);
  color: var(--text-faint);
  margin: 12px 0 0;
}

/* ---- managers and instructors ---- */

.staff-list { list-style: none; margin: 0 0 20px; padding: 0; }
.staff-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-faint);
}
.staff-list li:last-child { border-bottom: none; }

.staff-name { display: block; font-weight: 600; color: var(--text); }
.staff-email { display: block; font-size: var(--text-sm); color: var(--text-muted); }

.link-danger {
  background: none;
  border: none;
  padding: 0;
  color: var(--danger);
  font-size: var(--text-base);
  font-weight: 600;
}
.link-danger:hover:not(:disabled) { text-decoration: underline; }

.no-staff {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 20px;
  font-size: var(--text-base);
  color: var(--text-secondary);
}

.assign-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}
.assign-row .form-group { flex: 1; margin-bottom: 0; }

.assign-note {
  font-size: var(--text-sm);
  color: var(--text-faint);
  margin: 12px 0 0;
}

/* dashboard.css has no warning variant of .status-badge, and adding one there
   would change a shared class, so this stays local to the page. */
.badge-warning {
  display: inline-block;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--warning-border);
  background: var(--warning-bg);
  color: var(--warning-text);
  font-size: var(--text-xs);
  font-weight: 600;
}

.result-count { font-size: var(--text-base); color: var(--text-muted); }

.not-tracked { color: var(--text-faint); }

.empty-row { text-align: center; color: var(--text-faint); padding: 32px 16px; }

.table-note {
  font-size: var(--text-sm);
  color: var(--text-faint);
  margin: 0;
}
</style>
