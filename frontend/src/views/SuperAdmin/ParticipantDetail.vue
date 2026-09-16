<script setup>
import { ref, computed, onMounted, onErrorCaptured } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import {
  getParticipant,
  updateParticipant,
  deactivateParticipant,
  listBranches,
} from '@/apis.js'

const route = useRoute()
const router = useRouter()
const participantId = route.params.id

const participant = ref(null)
const branches = ref([])
const loading = ref(true)
const loadError = ref(null)

function initial(p) {
  return (p?.preferred_name || p?.full_name || '?').charAt(0).toUpperCase()
}

async function load() {
  loading.value = true
  try {
    participant.value = await getParticipant(participantId)
    loadError.value = null
  } catch (e) {
    participant.value = null
    loadError.value = e.response?.status === 404
      ? 'That participant does not exist, or you do not have access to them.'
      : 'Could not load this participant.'
    loading.value = false
    return
  }

  try { branches.value = await listBranches() } catch (e) { branches.value = [] }
  loading.value = false
}

// A thrown render aborts Vue's patch and leaves whatever was on screen, which
// is how a template bug shows up as a page stuck on "Loading participant…".
// Surfacing it beats staring at a spinner.
onErrorCaptured((err) => {
  loading.value = false
  loadError.value = `Something went wrong rendering this page: ${err.message}`
  return false
})

onMounted(load)

/* ---- edit ---- */

const editing = ref(false)
const draft = ref({})
const saveError = ref(null)
const saving = ref(false)

function startEdit() {
  const p = participant.value
  draft.value = {
    first_name: p.first_name,
    last_name: p.last_name,
    preferred_name: p.preferred_name ?? '',
    branch: p.branch,
    date_of_birth: p.date_of_birth ?? '',
    email: p.email ?? '',
    phone: p.phone ?? '',
    emergency_contact_name: p.emergency_contact_name ?? '',
    emergency_contact_phone: p.emergency_contact_phone ?? '',
    joined_on: p.joined_on ?? '',
    notes: p.notes ?? '',
  }
  saveError.value = null
  editing.value = true
}

async function save() {
  saving.value = true
  saveError.value = null
  try {
    participant.value = await updateParticipant(participantId, draft.value)
    editing.value = false
  } catch (e) {
    const data = e.response?.data
    saveError.value = e.response?.status === 403
      ? 'Only staff with access to this branch can edit this participant.'
      : data?.branch?.[0] ?? data?.first_name?.[0] ?? data?.last_name?.[0] ??
        data?.detail ?? 'Could not save these changes.'
  } finally {
    saving.value = false
  }
}

/* ---- deactivate ---- */

const deactivating = ref(false)

async function handleDeactivate() {
  if (!confirm(`Deactivate ${participant.value.full_name}? They will be marked inactive but their record and attendance history stay intact.`)) return

  deactivating.value = true
  saveError.value = null
  try {
    const result = await deactivateParticipant(participantId)
    participant.value = { ...participant.value, is_active: result.is_active }
  } catch (e) {
    saveError.value = e.response?.data?.detail ?? 'Could not deactivate this participant.'
  } finally {
    deactivating.value = false
  }
}

const branchName = computed(() =>
  branches.value.find(b => b.id === participant.value?.branch)?.name
  ?? participant.value?.branch_name
)
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <RouterLink to="/super-admin/participants" class="back-link">&lsaquo; All participants</RouterLink>

      <div v-if="loadError" class="form-error">{{ loadError }}</div>
      <p v-else-if="loading" class="loading-note">Loading participant…</p>

      <template v-else-if="participant">
        <div class="page-header">
          <div class="identity">
            <img
              v-if="participant.photo || participant.photo_url"
              class="photo-lg"
              :src="participant.photo || participant.photo_url"
              alt=""
            />
            <span v-else class="initials-avatar lg">{{ initial(participant) }}</span>

            <div>
              <h1>{{ participant.full_name }}</h1>
              <p class="page-subtitle">
                {{ branchName || 'No branch recorded' }}
                <span :class="['status-badge', participant.is_active ? 'active' : 'inactive']">
                  {{ participant.is_active ? 'Active' : 'Inactive' }}
                </span>
              </p>
            </div>
          </div>

          <div class="header-actions" v-if="!editing">
            <button
              v-if="participant.is_active"
              class="btn-danger"
              :disabled="deactivating"
              @click="handleDeactivate"
            >
              {{ deactivating ? 'Deactivating…' : 'Deactivate' }}
            </button>
            <button class="btn-primary" @click="startEdit">Edit details</button>
          </div>
        </div>

        <!-- Details -->
        <section class="panel">
          <h2>Details</h2>

          <form v-if="editing" class="edit-form" @submit.prevent="save">
            <div class="form-row">
              <div class="form-group">
                <label for="pd-first">First name</label>
                <input id="pd-first" v-model="draft.first_name" required />
              </div>
              <div class="form-group">
                <label for="pd-last">Last name</label>
                <input id="pd-last" v-model="draft.last_name" required />
              </div>
            </div>

            <div class="form-group">
              <label for="pd-preferred">Preferred name</label>
              <input id="pd-preferred" v-model="draft.preferred_name" />
            </div>

            <div class="form-group">
              <label for="pd-branch">Branch</label>
              <select id="pd-branch" v-model="draft.branch" required>
                <option value="" disabled>Select a branch</option>
                <option v-for="b in branches" :key="b.id" :value="b.id">{{ b.name }}</option>
              </select>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="pd-dob">Date of birth</label>
                <input id="pd-dob" v-model="draft.date_of_birth" type="date" />
              </div>
              <div class="form-group">
                <label for="pd-joined">Joined on</label>
                <input id="pd-joined" v-model="draft.joined_on" type="date" />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="pd-phone">Phone</label>
                <input id="pd-phone" v-model="draft.phone" />
              </div>
              <div class="form-group">
                <label for="pd-email">Email</label>
                <input id="pd-email" v-model="draft.email" type="email" />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="pd-ec-name">Emergency contact name</label>
                <input id="pd-ec-name" v-model="draft.emergency_contact_name" />
              </div>
              <div class="form-group">
                <label for="pd-ec-phone">Emergency contact phone</label>
                <input id="pd-ec-phone" v-model="draft.emergency_contact_phone" />
              </div>
            </div>

            <div class="form-group">
              <label for="pd-notes">Notes</label>
              <textarea id="pd-notes" v-model="draft.notes" rows="4"></textarea>
            </div>

            <div v-if="saveError" class="form-error">{{ saveError }}</div>

            <div class="edit-actions">
              <div class="modal-actions">
                <button type="button" class="btn-cancel" @click="editing = false">Cancel</button>
                <button type="submit" class="btn-primary" :disabled="saving">
                  {{ saving ? 'Saving…' : 'Save changes' }}
                </button>
              </div>
            </div>
          </form>

          <dl v-else class="detail-grid">
            <div>
              <dt>Preferred name</dt>
              <dd>{{ participant.preferred_name || '—' }}</dd>
            </div>
            <div>
              <dt>Date of birth</dt>
              <dd>{{ participant.date_of_birth || '—' }}</dd>
            </div>
            <div>
              <dt>Joined on</dt>
              <dd>{{ participant.joined_on || '—' }}</dd>
            </div>
            <div>
              <dt>Phone</dt>
              <dd>{{ participant.phone || '—' }}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{{ participant.email || '—' }}</dd>
            </div>
            <div>
              <dt>Emergency contact</dt>
              <dd>
                {{ participant.emergency_contact_name || '—' }}
                <span v-if="participant.emergency_contact_phone">
                  · {{ participant.emergency_contact_phone }}
                </span>
              </dd>
            </div>
          </dl>

          <template v-if="!editing && participant.notes">
            <h3 class="notes-heading">Notes</h3>
            <p class="notes-body">{{ participant.notes }}</p>
          </template>
        </section>

        <p class="table-note">
          Attendance history appears here once sessions are recorded.
        </p>
      </template>
    </main>
  </div>
</template>

<style scoped>
/* Every colour here is a theme.css token — nothing hardcoded. */

.page-header { align-items: flex-start; }

.identity {
  display: flex;
  align-items: center;
  gap: 16px;
}

.photo-lg {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.identity h1 { margin-bottom: 4px; }

.page-subtitle {
  display: flex;
  align-items: center;
  gap: 10px;
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
}
.btn-danger:hover:not(:disabled) { background: var(--danger-bg); }

.panel {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 24px;
  margin-bottom: 24px;
}
.panel h2 { margin-bottom: 16px; }

/* Label over value, wrapping across the panel rather than a rigid grid, so a
   long name does not squash its neighbours. */
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

.notes-heading { margin: 24px 0 8px; }
.notes-body {
  font-size: var(--text-base);
  color: var(--text-secondary);
  white-space: pre-wrap;
  margin: 0;
}

.form-group textarea {
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  font-size: var(--text-base);
  outline: none;
  background: var(--surface);
  font-family: inherit;
  resize: vertical;
}
.form-group textarea:focus { border-color: var(--teal); }

.edit-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 8px;
}
.edit-actions .modal-actions { margin-top: 0; }

.table-note {
  font-size: var(--text-sm);
  color: var(--text-faint);
  margin: 0;
}
</style>