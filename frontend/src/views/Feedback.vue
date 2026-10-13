<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { auth } from '@/stores/auth.js'
import { listBranches, listParticipants, listSessions, listFeedback, createFeedback } from '@/apis.js'
import { programmeToday } from '@/utils/sessions.js'

const activeFilter = ref('all')
const search = ref('')
const feedbackDialog = ref(null)
const branches = ref([])
const branchFilter = ref('')
const participants = ref([])
const sessions = ref([])
const feedbackList = ref([])
const loading = ref(true)
const loadError = ref(null)
const saving = ref(false)
const newEntryError = ref(null)
const isSuperAdmin = computed(() => auth.user?.role === 'super_admin')
const branchName = computed(() => isSuperAdmin.value ? 'all branches' : auth.user?.branch?.name ?? 'Your branch')
const emptyEntry = () => ({ quote: '', participant: '', session: '', date: programmeToday(), consent: false,
  branch: isSuperAdmin.value ? branchFilter.value : auth.user?.branch?.id ?? '' })
const newEntry = ref(emptyEntry())
const entryParticipants = computed(() => participants.value.filter(person => person.branch === newEntry.value.branch))
const entrySessions = computed(() => sessions.value.filter(session => session.branch === newEntry.value.branch))
watch(() => newEntry.value.branch, () => {
  newEntry.value.participant = ''
  newEntry.value.session = ''
}, { flush: 'sync' })

async function loadFeedback() {
  loading.value = true
  loadError.value = null
  feedbackList.value = []
  participants.value = []
  sessions.value = []
  branches.value = []
  try {
    const [entries, people, classes, branchList] = await Promise.all([
      listFeedback(), listParticipants(), listSessions(),
      isSuperAdmin.value ? listBranches() : Promise.resolve([]),
    ])
    feedbackList.value = entries
    participants.value = people
    sessions.value = classes
    branches.value = branchList
  } catch {
    loadError.value = 'Could not load feedback. Please try again.'
  } finally {
    loading.value = false
  }
}

function openModal() {
  if (loading.value || loadError.value || saving.value) return
  newEntry.value = emptyEntry()
  newEntryError.value = null
  feedbackDialog.value.showModal()
}

function closeModal() {
  if (saving.value) return
  feedbackDialog.value.close()
  newEntryError.value = null
}

async function handleAddFeedback() {
  if (saving.value || loading.value || loadError.value) return
  newEntryError.value = null
  if (!newEntry.value.quote.trim()) {
    newEntryError.value = 'Enter a quote or short story.'
    return
  }
  if (!newEntry.value.branch) {
    newEntryError.value = isSuperAdmin.value ? 'Choose a branch first.' : 'You must belong to a branch to record feedback.'
    return
  }
  if (!newEntry.value.participant && !newEntry.value.session) {
    newEntryError.value = 'Choose a participant or session.'
    return
  }
  if ((newEntry.value.participant && !entryParticipants.value.some(person => person.id === newEntry.value.participant)) ||
      (newEntry.value.session && !entrySessions.value.some(session => session.id === newEntry.value.session))) {
    newEntryError.value = 'Choose a participant and session from the selected branch.'
    return
  }
  saving.value = true
  try {
    const entry = await createFeedback({
      quote: newEntry.value.quote.trim(),
      date: newEntry.value.date,
      consent: newEntry.value.consent,
      participant: newEntry.value.participant || null,
      session: newEntry.value.session || null,
    })
    feedbackList.value.unshift(entry)
    feedbackDialog.value.close()
  } catch (error) {
    const data = error.response?.data
    newEntryError.value = data ? Object.values(data).flat().join(' ') : 'Could not save feedback. Please try again.'
  } finally {
    saving.value = false
  }
}

const scopedFeedback = computed(() => feedbackList.value.filter(entry =>
  !isSuperAdmin.value || !branchFilter.value || entry.branch === branchFilter.value,
))
function feedbackBranch(entry) {
  return branches.value.find(branch => branch.id === entry.branch)?.name ?? ''
}
const filteredFeedback = computed(() => {
  const query = search.value.toLowerCase().trim()
  return scopedFeedback.value.filter(f => {
    if (activeFilter.value === 'with' && !f.consent) return false
    if (activeFilter.value === 'without' && f.consent) return false
    return !query || [f.quote, f.source, f.recordedBy, feedbackBranch(f)].some(value => (value || '').toLowerCase().includes(query))
  })
})

onMounted(loadFeedback)
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <!-- Header -->
      <div class="page-header">
        <div>
          <h1>Feedback</h1>
          <p class="page-subtitle">Participant voice, personal stories and quotes for reporting at {{ branchName }}.</p>
        </div>
        <button class="btn-primary" :disabled="loading || !!loadError" @click="openModal">+ New entry</button>
      </div>

      <!-- Controls: Filters & Search -->
      <div class="controls-row">
        <div v-if="isSuperAdmin" class="form-group">
          <label for="feedback-branch-filter">Branch</label>
          <select id="feedback-branch-filter" v-model="branchFilter" :disabled="loading || !!loadError">
            <option value="">All branches</option>
            <option v-for="branch in branches" :key="branch.id" :value="branch.id">{{ branch.name }}</option>
          </select>
        </div>
        <div class="pills">
          <button
            :class="['pill', { active: activeFilter === 'all' }]"
            @click="activeFilter = 'all'"
          >
            All ({{ scopedFeedback.length }})
          </button>
          <button
            :class="['pill', { active: activeFilter === 'with' }]"
            @click="activeFilter = 'with'"
          >
            With quote consent ({{ scopedFeedback.filter(f => f.consent).length }})
          </button>
          <button
            :class="['pill', { active: activeFilter === 'without' }]"
            @click="activeFilter = 'without'"
          >
            Without consent ({{ scopedFeedback.filter(f => !f.consent).length }})
          </button>
        </div>

        <div class="search-wrap">
          <input
            v-model="search"
            type="search"
            class="search-input"
            placeholder="Search quotes or participants…"
            aria-label="Search feedback"
          />
        </div>
      </div>

      <!-- Feedback Cards List -->
      <p v-if="loading" class="loading-note">Loading feedback…</p>
      <div v-else-if="loadError" class="form-error" role="alert">
        {{ loadError }} <button class="btn-cancel" @click="loadFeedback">Retry</button>
      </div>
      <div v-else-if="filteredFeedback.length === 0" class="card empty-card">
        <h3>No feedback found</h3>
        <p v-if="search">No entries match your search "{{ search }}".</p>
        <p v-else>There is no feedback matching this filter.</p>
        <button class="btn-primary" style="margin-top: 12px;" @click="openModal">+ Record feedback</button>
      </div>

      <div v-else class="feedback-grid">
        <div
          v-for="item in filteredFeedback"
          :key="item.id"
          class="card feedback-card"
        >
          <blockquote class="quote-text">
            "{{ item.quote }}"
          </blockquote>

          <div class="feedback-meta">
            <span class="feedback-source">
              <strong>{{ item.source }}</strong> · {{ item.date }} · recorded by {{ item.recordedBy }}
              <template v-if="isSuperAdmin"> · {{ feedbackBranch(item) }}</template>
            </span>

            <span
              :class="['consent-badge', item.consent ? 'consent-yes' : 'consent-no']"
            >
              {{ item.consent ? 'Consent ✓' : 'Not for reporting' }}
            </span>
          </div>
        </div>
      </div>

      <!-- New Feedback Entry Modal -->
      <dialog ref="feedbackDialog" class="modal feedback-dialog" aria-labelledby="modal-title" @cancel.prevent="closeModal">
          <div class="modal-header">
            <h2 id="modal-title">Record feedback entry</h2>
            <button class="modal-close" aria-label="Close" @click="closeModal">&times;</button>
          </div>

          <form @submit.prevent="handleAddFeedback">
            <fieldset :disabled="saving || loading || !!loadError" class="feedback-fields">
            <p class="modal-desc">
              Record a participant quote or qualitative observation from a session or check-in. Choose a participant, a session, or both.
            </p>

            <div v-if="newEntryError" class="form-error" style="margin-bottom: 16px;" role="alert">
              {{ newEntryError }}
            </div>

            <div v-if="isSuperAdmin" class="form-group">
              <label for="feedback-entry-branch">Branch</label>
              <select id="feedback-entry-branch" v-model="newEntry.branch" required autofocus>
                <option value="" disabled>Choose a branch</option>
                <option v-for="branch in branches" :key="branch.id" :value="branch.id">{{ branch.name }}</option>
              </select>
            </div>
            <p v-else>Branch: {{ branchName }}</p>

            <div class="form-group">
              <label for="feedback-quote">Quote / short story</label>
              <textarea
                id="feedback-quote"
                v-model="newEntry.quote"
                rows="4"
                required
                :autofocus="!isSuperAdmin"
                placeholder="What did the participant share? e.g. 'I was able to walk without my stick this week…'"
              ></textarea>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="feedback-participant">Participant</label>
                <select id="feedback-participant" v-model="newEntry.participant" :disabled="!newEntry.branch">
                  <option value="">Choose a participant</option>
                  <option v-for="p in entryParticipants" :key="p.id" :value="p.id">{{ p.full_name }}</option>
                </select>
              </div>
              <div class="form-group">
                <label for="feedback-session">Session</label>
                <select id="feedback-session" v-model="newEntry.session" :disabled="!newEntry.branch">
                  <option value="">No session selected</option>
                  <option v-for="s in entrySessions" :key="s.id" :value="s.id">{{ s.date }} · {{ s.activity }}</option>
                </select>
              </div>

              <div class="form-group">
                <label for="feedback-date">Date recorded</label>
                <input
                  id="feedback-date"
                  v-model="newEntry.date"
                  :max="programmeToday()"
                  type="date"
                  required
                />
              </div>
            </div>

            <div class="checkbox-group">
              <label class="checkbox-label">
                <input
                  v-model="newEntry.consent"
                  type="checkbox"
                />
                <span>Consent is recorded for this feedback to be included in reports</span>
              </label>
            </div>

            <div class="modal-actions">
              <button type="button" class="btn-cancel" @click="closeModal">Cancel</button>
              <button type="submit" class="btn-primary">{{ saving ? 'Saving…' : 'Save entry' }}</button>
            </div>
            </fieldset>
          </form>
      </dialog>

    </main>
  </div>
</template>

<style scoped>
.dash-page .modal {
  max-width: calc(100vw - 32px);
  max-height: calc(100dvh - 32px);
  overflow-y: auto;
}
.feedback-dialog::backdrop { background: var(--ink); opacity: 0.6; }

/* Fieldsets and grid items otherwise keep the controls' intrinsic width. */
.feedback-fields {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}

.modal .form-row {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.modal .form-group {
  min-width: 0;
}

.modal .form-group input,
.modal .form-group select,
.modal .form-group textarea {
  min-width: 0;
  width: 100%;
  max-width: 100%;
}

.modal textarea {
  resize: vertical;
  padding: 8px 12px;
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: var(--surface);
}

.modal textarea:focus {
  outline: 2px solid var(--teal);
  outline-offset: 1px;
}

@media (max-width: 520px) {
  .dash-page .modal { padding: 20px; }
  .modal .form-row { grid-template-columns: minmax(0, 1fr); }
}

.controls-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.controls-row .form-group,
.controls-row .pills {
  margin-bottom: 0;
}

.controls-row select,
.controls-row .pill,
.controls-row .search-input {
  min-height: 44px;
}

.search-wrap {
  flex: 1;
  min-width: 240px;
  max-width: 380px;
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

.feedback-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feedback-card {
  padding: 24px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.quote-text {
  font-size: var(--text-lg);
  font-style: italic;
  line-height: 1.5;
  color: var(--ink);
  margin: 0 0 16px;
  border-left: 3px solid var(--terracotta);
  padding-left: 16px;
}

.feedback-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-faint);
}

.feedback-source {
  font-size: var(--text-sm);
  color: var(--bark);
}

.consent-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 600;
}

.consent-yes {
  background: var(--mint);
  color: var(--forest);
}

.consent-no {
  background: var(--sand-light);
  color: var(--bark);
}

.empty-card {
  text-align: center;
  padding: 48px 24px;
}

.checkbox-group {
  margin: 16px 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: var(--text-sm);
  color: var(--ink);
  cursor: pointer;
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
</style>
