<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listBranches, createBranch } from '@/apis.js'

const router = useRouter()

const branches = ref([])
const loading = ref(true)
const loadError = ref(null)

const search = ref('')
const activeFilter = ref('All')

// Attendance and questionnaire returns have no models behind them yet, so the
// two filters that would need that data are shown but disabled rather than
// wired to something that would quietly return nothing.
const filters = [
  { label: 'All', ready: true },
  { label: 'No manager', ready: true },
  { label: 'No sessions in 3 weeks', ready: false },
  { label: 'Questionnaire outstanding', ready: false },
]

const PENDING_DATA = 'Needs session and questionnaire records, which do not exist yet.'

// 30 branches is a short list, so filtering here keeps typing instant. The same two
// filters exist on the endpoint (?search= and ?no_manager=) for when it grows.
const visibleBranches = computed(() => {
  const query = search.value.trim().toLowerCase()

  return branches.value.filter((b) => {
    const matchesSearch =
      !query ||
      b.name.toLowerCase().includes(query) ||
      (b.region ?? '').toLowerCase().includes(query)

    const matchesFilter =
      activeFilter.value !== 'No manager' || !b.manager_name

    return matchesSearch && matchesFilter
  })
})

async function load() {
  loading.value = true
  try {
    branches.value = await listBranches()
    loadError.value = null
  } catch (e) {
    branches.value = []
    loadError.value = 'Could not load the branch list.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function openBranch(id) {
  router.push(`/super-admin/branches/${id}`)
}

/* ---- add branch ---- */

const emptyBranch = () => ({ name: '', region: '' })

const showModal = ref(false)
const newBranch = ref(emptyBranch())
const createError = ref(null)
const saving = ref(false)

function openModal() {
  newBranch.value = emptyBranch()
  createError.value = null
  showModal.value = true
}

async function submitCreateBranch() {
  saving.value = true
  createError.value = null
  try {
    await createBranch(newBranch.value)
    showModal.value = false
    await load()
  } catch (e) {
    const data = e.response?.data
    createError.value = data?.name?.[0] ?? data?.detail ?? 'Could not add this branch.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="dash-page">

    <!-- Add branch -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
      <div class="modal">
        <h2>Add branch</h2>

        <form @submit.prevent="submitCreateBranch">
          <div class="form-group">
            <label for="branch-name">Name</label>
            <input id="branch-name" v-model="newBranch.name" required />
          </div>

          <div class="form-group">
            <label for="branch-region">Region</label>
            <input id="branch-region" v-model="newBranch.region" />
          </div>

          <div v-if="createError" class="form-error">{{ createError }}</div>

          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="showModal = false">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? 'Adding…' : 'Add branch' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <main class="content">
      <div class="page-header">
        <h1>Branch</h1>
        <button class="btn-primary" @click="openModal">Add branch</button>
      </div>

      <div v-if="loadError" class="form-error">{{ loadError }}</div>

      <input
        v-model="search"
        class="branch-search"
        type="search"
        placeholder="Search by branch name or region…"
        aria-label="Search by branch name or region"
      />

      <div class="pills">
        <button
          v-for="f in filters"
          :key="f.label"
          :class="['pill', { active: activeFilter === f.label }]"
          :disabled="!f.ready"
          :title="f.ready ? null : PENDING_DATA"
          @click="activeFilter = f.label"
        >
          {{ f.label }}
        </button>
      </div>

      <p class="result-count">{{ visibleBranches.length }} of {{ branches.length }} branches</p>

      <table class="data-table">
        <thead>
          <tr>
            <th>Branch</th>
            <th>Branch Manager</th>
            <th>Instructors</th>
            <th>Participants</th>
            <th>Attendance</th>
            <th>Questionnaire</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="b in visibleBranches"
            :key="b.id"
            class="branch-row"
            tabindex="0"
            @click="openBranch(b.id)"
            @keydown.enter="openBranch(b.id)"
          >
            <td>
              <span class="branch-name">{{ b.name }}</span>
              <span class="branch-region">{{ b.region || '—' }}</span>
            </td>
            <td>
              <span v-if="b.manager_name">{{ b.manager_name }}</span>
              <span v-else class="badge-warning">No manager</span>
            </td>
            <td>{{ b.instructor_count }}</td>
            <td>{{ b.participant_count }}</td>
            <td class="not-tracked" :title="PENDING_DATA">—</td>
            <td class="not-tracked" :title="PENDING_DATA">—</td>
            <td class="chevron" aria-hidden="true">›</td>
          </tr>

          <tr v-if="loading">
            <td colspan="7" class="empty-row">Loading branches…</td>
          </tr>
          <tr v-else-if="!visibleBranches.length">
            <td colspan="7" class="empty-row">
              {{ branches.length ? 'No branches match this search.' : 'No branches yet. Add the first one.' }}
            </td>
          </tr>
        </tbody>
      </table>

      <p class="table-note">
        Attendance and questionnaire returns appear here once sessions and
        questionnaires are recorded.
      </p>
    </main>
  </div>
</template>

<style scoped>
/* Every colour here is a theme.css token — nothing hardcoded. */

.branch-search {
  width: 100%;
  padding: 12px 18px;
  margin-bottom: 16px;
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius-pill);
  background: var(--surface);
  font-size: var(--text-md);
  outline: none;
}
.branch-search:focus { border-color: var(--teal); }

/* The two filters with no data behind them stay visible but unusable. */
.pill:disabled { opacity: 0.5; cursor: not-allowed; }
.pill:disabled:hover { border-color: var(--border-strong); }

.result-count {
  font-size: var(--text-base);
  color: var(--text-muted);
  margin: 0 0 10px;
}

/* Name over region, so the branch reads as one thing rather than two columns. */
.branch-name { display: block; font-weight: 600; color: var(--text); }
.branch-region { display: block; font-size: var(--text-sm); color: var(--text-muted); }

.branch-row { cursor: pointer; }
.branch-row:hover td { background: var(--surface-sunken); }
.branch-row:focus-visible { outline: 2px solid var(--teal); outline-offset: -2px; }

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

.not-tracked { color: var(--text-faint); }

.chevron { text-align: right; color: var(--text-faint); font-size: var(--text-md); }

.empty-row { text-align: center; color: var(--text-faint); padding: 32px 16px; }

.table-note {
  font-size: var(--text-sm);
  color: var(--text-faint);
  margin: 16px 0 0;
}
</style>
