<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listParticipants, createParticipant, listBranches } from '@/apis.js'

const router = useRouter()

const participants = ref([])
const branches = ref([])
const loading = ref(true)
const loadError = ref(null)

const search = ref('')
const activeFilter = ref('All')
const branchFilter = ref('All')

const filters = ['All', 'Active', 'Inactive']

// The initial the avatar falls back to when there is no photo on file yet.
function initial(p) {
  return (p.preferred_name || p.full_name || '?').charAt(0).toUpperCase()
}

// Every filter here maps straight onto a query param listParticipants
// already supports (branch / is_active / search), so filtering happens on
// the server instead of being redone in the browser.
function currentParams() {
  const params = {}
  const query = search.value.trim()
  if (query) params.search = query
  if (activeFilter.value !== 'All') params.is_active = activeFilter.value === 'Active' ? 'true' : 'false'
  if (branchFilter.value !== 'All') params.branch = branchFilter.value
  return params
}

async function loadParticipants() {
  loading.value = true
  try {
    participants.value = await listParticipants(currentParams())
    loadError.value = null
  } catch (e) {
    participants.value = []
    loadError.value = 'Could not load the participant list.'
  } finally {
    loading.value = false
  }
}

async function loadBranches() {
  try { branches.value = await listBranches() } catch (e) { branches.value = [] }
}

onMounted(async () => {
  await loadBranches()
  await loadParticipants()
})

// Typing re-queries after a short pause so every keystroke doesn't hit the
// API; the pills and the branch picker re-query immediately since there is
// no typing to debounce there.
let searchDebounce = null
watch(search, () => {
  clearTimeout(searchDebounce)
  searchDebounce = setTimeout(loadParticipants, 300)
})
watch([activeFilter, branchFilter], loadParticipants)

function openDetail(id) {
  router.push(`/super-admin/participants/${id}`)
}

/* ---- add participant ---- */

const emptyParticipant = () => ({
  first_name: '', last_name: '', preferred_name: '',
  branch: '', phone: '', email: '',
})

const showModal = ref(false)
const newParticipant = ref(emptyParticipant())
const createError = ref(null)
const saving = ref(false)

function openModal() {
  newParticipant.value = emptyParticipant()
  createError.value = null
  showModal.value = true
  // branches are already loaded, so the picker is ready immediately
}

async function submitCreateParticipant() {
  saving.value = true
  createError.value = null
  try {
    await createParticipant(newParticipant.value)
    showModal.value = false
    await loadParticipants()
  } catch (e) {
    const data = e.response?.data
    createError.value =
      data?.branch?.[0] ?? data?.first_name?.[0] ?? data?.last_name?.[0] ??
      data?.detail ?? 'Could not add this participant.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="dash-page">

    <!-- Add participant -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
      <div class="modal">
        <h2>Add participant</h2>

        <form @submit.prevent="submitCreateParticipant">
          <div class="form-row">
            <div class="form-group">
              <label for="p-first">First name</label>
              <input id="p-first" v-model="newParticipant.first_name" required />
            </div>
            <div class="form-group">
              <label for="p-last">Last name</label>
              <input id="p-last" v-model="newParticipant.last_name" required />
            </div>
          </div>

          <div class="form-group">
            <label for="p-preferred">Preferred name</label>
            <input id="p-preferred" v-model="newParticipant.preferred_name" />
          </div>

          <div class="form-group">
            <label for="p-branch">Branch</label>
            <select id="p-branch" v-model="newParticipant.branch" required>
              <option value="" disabled>Select a branch</option>
              <option v-for="b in branches" :key="b.id" :value="b.id">{{ b.name }}</option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="p-phone">Phone</label>
              <input id="p-phone" v-model="newParticipant.phone" />
            </div>
            <div class="form-group">
              <label for="p-email">Email</label>
              <input id="p-email" v-model="newParticipant.email" type="email" />
            </div>
          </div>

          <div v-if="createError" class="form-error">{{ createError }}</div>

          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="showModal = false">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? 'Adding…' : 'Add participant' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <main class="content">
      <div class="page-header">
        <h1>Participants</h1>
        <button class="btn-primary" @click="openModal">Add participant</button>
      </div>

      <div v-if="loadError" class="form-error">{{ loadError }}</div>

      <input
        v-model="search"
        class="participant-search"
        type="search"
        placeholder="Search by participant or branch name…"
        aria-label="Search by participant or branch name"
      />

      <div class="filter-row">
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

        <select
          v-model="branchFilter"
          class="branch-filter"
          aria-label="Filter by branch"
        >
          <option value="All">All branches</option>
          <option v-for="b in branches" :key="b.id" :value="b.id">{{ b.name }}</option>
        </select>
      </div>

      <p class="result-count">
        {{ participants.length }} participant{{ participants.length === 1 ? '' : 's' }}
      </p>

      <table class="data-table">
        <thead>
          <tr>
            <th></th>
            <th>Participant</th>
            <th>Branch</th>
            <th>Phone</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="p in participants"
            :key="p.id"
            class="participant-row"
            tabindex="0"
            @click="openDetail(p.id)"
            @keydown.enter="openDetail(p.id)"
          >
            <td class="avatar-cell">
              <img
                v-if="p.photo || p.photo_url"
                class="photo"
                :src="p.photo || p.photo_url"
                alt=""
              />
              <span v-else class="initials-avatar">{{ initial(p) }}</span>
            </td>
            <td>
              <span class="participant-name">{{ p.full_name }}</span>
              <span v-if="p.preferred_name" class="participant-preferred">{{ p.preferred_name }}</span>
            </td>
            <td>{{ p.branch_name ?? '—' }}</td>
            <td>{{ p.phone || '—' }}</td>
            <td>
              <span :class="['status-badge', p.is_active ? 'active' : 'inactive']">
                {{ p.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="chevron" aria-hidden="true">›</td>
          </tr>

          <tr v-if="loading">
            <td colspan="6" class="empty-row">Loading participants…</td>
          </tr>
          <tr v-else-if="!participants.length">
            <td colspan="6" class="empty-row">
              {{ search || activeFilter !== 'All' || branchFilter !== 'All'
                ? 'No participants match these filters.'
                : 'No participants yet. Add the first one.' }}
            </td>
            <td><RouterLink :to="`/participants/${p.id}`">Consent / photo →</RouterLink></td>
          </tr>
        </tbody>
      </table>
    </main>
  </div>
</template>

<style scoped>
/* Every colour here is a theme.css token — nothing hardcoded. */

.participant-search {
  width: 100%;
  padding: 12px 18px;
  margin-bottom: 16px;
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius-pill);
  background: var(--surface);
  font-size: var(--text-md);
  outline: none;
}
.participant-search:focus { border-color: var(--teal); }

.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
}
.filter-row .pills { margin-bottom: 0; }

.branch-filter {
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  font-size: var(--text-base);
  background: var(--surface);
  color: var(--text-secondary);
  outline: none;
  min-width: 180px;
}
.branch-filter:focus { border-color: var(--teal); }

.result-count {
  font-size: var(--text-base);
  color: var(--text-muted);
  margin: 0 0 10px;
}

.avatar-cell { width: 52px; }
.avatar-cell .photo {
  display: block;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
}

/* Legal name over what the branch actually calls them. */
.participant-name { display: block; font-weight: 600; color: var(--text); }
.participant-preferred {
  display: block;
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.participant-row { cursor: pointer; }
.participant-row:hover td { background: var(--surface-sunken); }
.participant-row:focus-visible { outline: 2px solid var(--teal); outline-offset: -2px; }

.chevron { text-align: right; color: var(--text-faint); font-size: var(--text-md); }

.empty-row { text-align: center; color: var(--text-faint); padding: 32px 16px; }
</style>