<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '@/stores/auth.js'
import { listBranches, listStaff } from '@/apis.js'

const router = useRouter()

const branches = ref([])
const staff = ref([])
const loading = ref(true)
const loadError = ref(null)

const PENDING_DATA = 'Needs session and questionnaire records, which do not exist yet.'

const firstName = computed(() => {
  const u = auth.user
  if (!u) return ''
  return (u.first_name || u.email || '').split(' ')[0]
})

async function load() {
  loading.value = true
  loadError.value = null

  // Two independent reads. A failure in one (e.g. a Branch Manager-only 403 on
  // staff, which shouldn't happen for a Super Admin but is cheap to guard)
  // shouldn't blank a page the other half of could still render.
  const [branchesResult, staffResult] = await Promise.allSettled([
    listBranches(),
    listStaff(),
  ])

  branches.value = branchesResult.status === 'fulfilled' ? branchesResult.value : []
  staff.value = staffResult.status === 'fulfilled' ? staffResult.value : []

  if (branchesResult.status === 'rejected' && staffResult.status === 'rejected') {
    loadError.value = 'Could not load the national overview.'
  } else if (branchesResult.status === 'rejected') {
    loadError.value = 'Could not load branch data. Staff figures below may still be accurate.'
  } else if (staffResult.status === 'rejected') {
    loadError.value = 'Could not load staff data. Branch figures below may still be accurate.'
  }

  loading.value = false
}

onMounted(load)

/* ---- national stats ---- */

const totalBranches = computed(() => branches.value.length)

const totalParticipants = computed(() =>
  branches.value.reduce((sum, b) => sum + (b.participant_count ?? 0), 0)
)

const totalInstructors = computed(() =>
  staff.value.filter(u => u.role === 'instructor' && u.is_active).length
)

const totalBranchManagers = computed(() =>
  staff.value.filter(u => u.role === 'branch_manager' && u.is_active).length
)

const regionCount = computed(() =>
  new Set(branches.value.map(b => b.region).filter(Boolean)).size
)

/* ---- needs attention ---- */

const branchesWithoutManager = computed(() =>
  branches.value.filter(b => !b.manager_name)
)

const inactiveStaffCount = computed(() =>
  staff.value.filter(u => !u.is_active).length
)

/* ---- branches by region ---- */

const regionBreakdown = computed(() => {
  const byRegion = new Map()

  for (const b of branches.value) {
    const region = b.region || 'Unspecified'
    const entry = byRegion.get(region) ?? { region, branchCount: 0, participantCount: 0 }
    entry.branchCount += 1
    entry.participantCount += b.participant_count ?? 0
    byRegion.set(region, entry)
  }

  const rows = [...byRegion.values()].sort((a, b) => b.participantCount - a.participantCount)
  const max = Math.max(1, ...rows.map(r => r.participantCount))
  return rows.map(r => ({ ...r, barPct: Math.round((r.participantCount / max) * 100) }))
})

/* ---- top branches by participants ---- */

const topBranches = computed(() =>
  [...branches.value]
    .sort((a, b) => (b.participant_count ?? 0) - (a.participant_count ?? 0))
    .slice(0, 6)
)

function openBranch(id) {
  router.push(`/super-admin/branches/${id}`)
}
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <div class="page-header">
        <div>
          <h1>Kia ora{{ firstName ? `, ${firstName}` : '' }}</h1>
          <p class="page-subtitle" style="margin-bottom: 0;">
            A national snapshot across every branch.
          </p>
        </div>
      </div>

      <div v-if="loadError" class="form-error">{{ loadError }}</div>

      <!-- Stat tiles -->
      <div class="stat-grid">
        <div class="stat-tile">
          <div class="stat-tile-value">{{ loading ? '—' : totalBranches }}</div>
          <div class="stat-tile-label">Branches</div>
        </div>
        <div class="stat-tile">
          <div class="stat-tile-value">{{ loading ? '—' : totalParticipants }}</div>
          <div class="stat-tile-label">Active participants</div>
        </div>
        <div class="stat-tile">
          <div class="stat-tile-value">{{ loading ? '—' : totalInstructors }}</div>
          <div class="stat-tile-label">Instructors</div>
        </div>
        <div class="stat-tile">
          <div class="stat-tile-value">{{ loading ? '—' : totalBranchManagers }}</div>
          <div class="stat-tile-label">Branch managers</div>
        </div>
        <div class="stat-tile">
          <div class="stat-tile-value">{{ loading ? '—' : regionCount }}</div>
          <div class="stat-tile-label">Regions covered</div>
        </div>
      </div>

      <!-- Needs attention -->
      <section class="section" v-if="!loading && (branchesWithoutManager.length || inactiveStaffCount)">
        <h2>Needs attention</h2>
        <div class="alerts">
          <div
            v-for="b in branchesWithoutManager"
            :key="b.id"
            class="alert-row"
          >
            <span>⚠ {{ b.name }}{{ b.region ? ` (${b.region})` : '' }} has no branch manager</span>
            <a href="#" @click.prevent="openBranch(b.id)">See branch →</a>
          </div>
          <div v-if="inactiveStaffCount" class="alert-row">
            <span>⚠ {{ inactiveStaffCount }} staff account{{ inactiveStaffCount > 1 ? 's are' : ' is' }} deactivated</span>
            <a href="#" @click.prevent="router.push('/super-admin/users')">See users →</a>
          </div>
        </div>
      </section>

      <div class="bottom-grid">

        <!-- Branches by region -->
        <div class="panel">
          <h3>Participants by region</h3>
          <div v-if="loading" class="loading-note">Loading…</div>
          <div v-else-if="!regionBreakdown.length" class="loading-note">No branches yet.</div>
          <div v-else class="region-rows">
            <div class="region-row" v-for="r in regionBreakdown" :key="r.region">
              <div class="region-label">
                <span>{{ r.region }}</span>
                <span class="region-meta">{{ r.branchCount }} branch{{ r.branchCount === 1 ? '' : 'es' }} · {{ r.participantCount }} participants</span>
              </div>
              <div class="region-bar-track">
                <div class="region-bar" :style="{ width: r.barPct + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Top branches -->
        <div class="panel">
          <h3>Largest branches</h3>
          <div v-if="loading" class="loading-note">Loading…</div>
          <div v-else-if="!topBranches.length" class="loading-note">No branches yet.</div>
          <template v-else>
            <div
              class="branch-summary-row"
              v-for="b in topBranches"
              :key="b.id"
              tabindex="0"
              @click="openBranch(b.id)"
              @keydown.enter="openBranch(b.id)"
            >
              <div>
                <div class="branch-summary-name">{{ b.name }}</div>
                <div class="branch-summary-meta">
                  {{ b.manager_name || 'No manager' }} · {{ b.instructor_count }} instructor{{ b.instructor_count === 1 ? '' : 's' }}
                </div>
              </div>
              <div class="branch-summary-count">{{ b.participant_count }}</div>
            </div>
          </template>
          <a href="#" class="view-all" @click.prevent="router.push('/super-admin/branches')">View all branches →</a>
        </div>

      </div>

      <!-- Quick links -->
      <section class="section">
        <h2>Go to</h2>
        <div class="card-grid">
          <div class="card">
            <h3>Branches</h3>
            <p>Every branch, its manager, instructors and participant count.</p>
            <a href="#" @click.prevent="router.push('/super-admin/branches')">Open →</a>
          </div>
          <div class="card">
            <h3>Users</h3>
            <p>All staff accounts across the organisation, by role.</p>
            <a href="#" @click.prevent="router.push('/super-admin/users')">Open →</a>
          </div>
          <div class="card">
            <h3>Participants</h3>
            <p>Everyone attending a branch, nationally.</p>
            <a href="#" @click.prevent="router.push('/super-admin/participants')">Open →</a>
          </div>
        </div>
      </section>

      <p class="table-note">
        Attendance and questionnaire figures will appear here once branches start
        recording sessions — {{ PENDING_DATA.toLowerCase() }}
      </p>
    </main>
  </div>
</template>

<style scoped>
.section { margin-bottom: 28px; }
.section h2 { margin-bottom: 12px; }

.alerts { display: flex; flex-direction: column; gap: 8px; }
.alert-row {
  display: flex; justify-content: space-between; align-items: center;
  background: var(--warning-bg); border: 1px solid var(--warning-border);
  border-radius: var(--radius); padding: 12px 16px;
  font-size: var(--text-base); color: var(--warning-text);
}
.alert-row a {
  color: var(--warning-text); font-size: var(--text-sm); font-weight: 600;
  text-decoration: underline; white-space: nowrap; margin-left: 16px;
}

.bottom-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 28px; }
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-card);
}
.panel h3 { margin-bottom: 16px; font-size: var(--text-md); font-weight: 700; color: var(--text); }
.loading-note { color: var(--text-muted); font-size: var(--text-base); }

.region-rows { display: flex; flex-direction: column; gap: 14px; }
.region-label {
  display: flex; justify-content: space-between; align-items: baseline;
  font-size: var(--text-base); color: var(--text); margin-bottom: 6px;
}
.region-meta { font-size: var(--text-sm); color: var(--text-muted); }
.region-bar-track {
  height: 8px; border-radius: var(--radius-pill); background: var(--surface-sunken); overflow: hidden;
}
.region-bar {
  height: 100%;
  border-radius: var(--radius-pill);
  background: var(--teal);
  transition: width 0.3s ease;
}

.branch-summary-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 8px; border-bottom: 1px solid var(--border-faint); cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background-color 0.15s ease;
}
.branch-summary-row:last-of-type { border-bottom: none; }
.branch-summary-row:hover { background: var(--surface-sunken); }
.branch-summary-row:focus-visible { outline: 2px solid var(--teal); outline-offset: -2px; }
.branch-summary-name { font-size: var(--text-base); font-weight: 600; color: var(--text); }
.branch-summary-meta { font-size: var(--text-sm); color: var(--text-muted); margin-top: 2px; }
.branch-summary-count { font-size: var(--text-lg); font-weight: 700; color: var(--text); }

.view-all { display: block; margin-top: 16px; font-size: var(--text-sm); font-weight: 600; color: var(--teal); text-decoration: none; }
.view-all:hover { color: var(--teal-dark); text-decoration: underline; }

.table-note { font-size: var(--text-sm); color: var(--text-faint); margin: 0; }

@media (max-width: 860px) {
  .bottom-grid { grid-template-columns: 1fr; }
}
</style>