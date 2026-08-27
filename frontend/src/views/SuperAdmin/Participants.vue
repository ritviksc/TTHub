<script setup>
import { ref, computed, onMounted } from 'vue'
import { listParticipants, createParticipant, listBranches } from '@/apis.js'

const participants = ref([])
const loading = ref(true)
const loadError = ref(null)

const search = ref('')
const activeFilter = ref('All')

const filters = ['All', 'Active', 'Inactive']

const visibleParticipants = computed(() => {
  const query = search.value.trim().toLowerCase()

  return participants.value.filter((p) => {
    const matchesSearch =
      !query ||
      p.full_name.toLowerCase().includes(query) ||
      (p.preferred_name ?? '').toLowerCase().includes(query) ||
      (p.branch_name ?? '').toLowerCase().includes(query)

    const matchesFilter =
      activeFilter.value === 'All' ||
      (activeFilter.value === 'Active' ? p.is_active : !p.is_active)

    return matchesSearch && matchesFilter
  })
})

async function load() {
  loading.value = true
  try {
    participants.value = await listParticipants()
    loadError.value = null
  } catch (e) {
    participants.value = []
    loadError.value = 'Could not load the participant list.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

/* ---- add participant ---- */

const emptyParticipant = () => ({
  first_name: '', last_name: '', preferred_name: '',
  branch: '', phone: '', email: '',
})

const showModal = ref(false)
const branches = ref([])
const newParticipant = ref(emptyParticipant())
const createError = ref(null)
const saving = ref(false)

async function openModal() {
  newParticipant.value = emptyParticipant()
  createError.value = null
  showModal.value = true
  // A Super Admin has to say which branch, so the picker has to be populated
  // before the form is usable.
  try { branches.value = await listBranches() } catch (e) { branches.value = [] }
}

async function submitCreateParticipant() {
  saving.value = true
  createError.value = null
  try {
    await createParticipant(newParticipant.value)
    showModal.value = false
    await load()
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

      <p class="result-count">
        {{ visibleParticipants.length }} of {{ participants.length }} participants
      </p>

      <table class="data-table">
        <thead>
          <tr>
            <th>Participant</th>
            <th>Branch</th>
            <th>Phone</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in visibleParticipants" :key="p.id">
            <td>
              <span class="participant-name">{{ p.full_name }}</span>
              <span v-if="p.preferred_name" class="participant-preferred">
                {{ p.preferred_name }}
              </span>
            </td>
            <td>{{ p.branch_name ?? '—' }}</td>
            <td>{{ p.phone || '—' }}</td>
            <td>
              <span :class="['status-badge', p.is_active ? 'active' : 'inactive']">
                {{ p.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
          </tr>

          <tr v-if="loading">
            <td colspan="4" class="empty-row">Loading participants…</td>
          </tr>
          <tr v-else-if="!visibleParticipants.length">
            <td colspan="4" class="empty-row">
              {{ participants.length
                ? 'No participants match this search.'
                : 'No participants yet. Add the first one.' }}
            </td>
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

.result-count {
  font-size: var(--text-base);
  color: var(--text-muted);
  margin: 0 0 10px;
}

/* Legal name over what the branch actually calls them. */
.participant-name { display: block; font-weight: 600; color: var(--text); }
.participant-preferred {
  display: block;
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.empty-row { text-align: center; color: var(--text-faint); padding: 32px 16px; }
</style>
