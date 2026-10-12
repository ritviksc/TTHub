<script setup>
import { ref, computed, onMounted } from 'vue'
import { auth } from '@/stores/auth.js'
import { listParticipants, listSessions, listFeedback, createFeedback } from '@/apis.js'
import { programmeToday } from '@/utils/sessions.js'

const activeFilter = ref('all')
const search = ref('')
const showModal = ref(false)
const participants = ref([])
const sessions = ref([])
const feedbackList = ref([])
const loading = ref(true)
const loadError = ref(null)
const saving = ref(false)
const newEntryError = ref(null)

const branchName = computed(() => auth.user?.branch?.name ?? 'Your branch')

const emptyEntry = () => ({
  quote: '',
  participant: '',
  session: '',
  date: programmeToday(),
  consent: false,
})

const newEntry = ref(emptyEntry())

async function loadFeedback() {
  loading.value = true
  loadError.value = null
  try {
    const [entries, people, classes] = await Promise.all([
      listFeedback().catch(() => []),
      listParticipants().catch(() => []),
      listSessions().catch(() => []),
    ])
    feedbackList.value = entries
    participants.value = people
    sessions.value = classes
  } catch {
    loadError.value = 'Could not load feedback. Please try again.'
  } finally {
    loading.value = false
  }
}

function openModal() {
  newEntry.value = emptyEntry()
  // If there are sessions, pre-select the most recent session
  if (sessions.value.length > 0) {
    newEntry.value.session = sessions.value[0].id
  }
  newEntryError.value = null
  showModal.value = true
}

function closeModal() {
  if (saving.value) return
  showModal.value = false
  newEntryError.value = null
}

async function handleAddFeedback() {
  if (saving.value) return
  newEntryError.value = null

  if (!newEntry.value.quote.trim()) {
    newEntryError.value = 'Please enter quote or feedback text.'
    return
  }

  if (!newEntry.value.participant && !newEntry.value.session) {
    newEntryError.value = 'Choose a participant or session to associate this feedback with.'
    return
  }

  saving.value = true
  try {
    const entry = await createFeedback({
      quote: newEntry.value.quote.trim(),
      date: newEntry.value.date,
      consent: !!newEntry.value.consent,
      participant: newEntry.value.participant || null,
      session: newEntry.value.session || null,
    })
    feedbackList.value.unshift(entry)
    showModal.value = false
  } catch (error) {
    const data = error.response?.data
    newEntryError.value = data
      ? Object.values(data).flat().join(' ')
      : 'Could not save feedback. Please try again.'
  } finally {
    saving.value = false
  }
}

const filteredFeedback = computed(() => {
  const query = search.value.toLowerCase().trim()
  return feedbackList.value.filter(f => {
    if (activeFilter.value === 'with' && !f.consent) return false
    if (activeFilter.value === 'without' && f.consent) return false
    return !query || [f.quote, f.source, f.recordedBy].some(val =>
      (val || '').toLowerCase().includes(query)
    )
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
          <h1>Kaumātua Feedback</h1>
          <p class="page-subtitle">
            Participant voice, personal stories, and observations recorded during sessions at {{ branchName }}.
          </p>
        </div>
        <button class="btn-primary" :disabled="loading" @click="openModal">
          + Record feedback
        </button>
      </div>

      <!-- Controls: Filters & Search -->
      <div class="controls-row">
        <div class="pills" role="tablist" aria-label="Feedback filters">
          <button
            :class="['pill', { active: activeFilter === 'all' }]"
            role="tab"
            :aria-selected="activeFilter === 'all'"
            @click="activeFilter = 'all'"
          >
            All ({{ feedbackList.length }})
          </button>
          <button
            :class="['pill', { active: activeFilter === 'with' }]"
            role="tab"
            :aria-selected="activeFilter === 'with'"
            @click="activeFilter = 'with'"
          >
            With quote consent ({{ feedbackList.filter(f => f.consent).length }})
          </button>
          <button
            :class="['pill', { active: activeFilter === 'without' }]"
            role="tab"
            :aria-selected="activeFilter === 'without'"
            @click="activeFilter = 'without'"
          >
            Without consent ({{ feedbackList.filter(f => !f.consent).length }})
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
      <div v-if="loading" class="loading-state">
        <p>Loading feedback records…</p>
      </div>

      <div v-else-if="loadError" class="form-error" role="alert">
        {{ loadError }}
        <button class="btn-cancel" style="margin-left: 12px;" @click="loadFeedback">Retry</button>
      </div>

      <div v-else-if="filteredFeedback.length === 0" class="card empty-card">
        <h3>No feedback recorded yet</h3>
        <p v-if="search">No quotes match "{{ search }}".</p>
        <p v-else>Share participant reflections from your classes to capture the impact of Taurite Tū.</p>
        <button class="btn-primary" style="margin-top: 14px;" @click="openModal">
          + Record feedback
        </button>
      </div>

      <div v-else class="feedback-grid">
        <div
          v-for="item in filteredFeedback"
          :key="item.id"
          class="card feedback-card"
        >
          <blockquote class="quote-text">
            “{{ item.quote }}”
          </blockquote>

          <div class="feedback-meta">
            <span class="feedback-source">
              <strong>{{ item.source }}</strong> · {{ item.date }}
              <span v-if="item.recordedBy" class="recorded-by">· by {{ item.recordedBy }}</span>
            </span>

            <span
              :class="['consent-badge', item.consent ? 'consent-yes' : 'consent-no']"
            >
              {{ item.consent ? 'Consent for reports ✓' : 'Internal reflection' }}
            </span>
          </div>
        </div>
      </div>

      <!-- New Feedback Entry Modal -->
      <div v-if="showModal" class="modal-backdrop" @click.self="closeModal">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div class="modal-header">
            <h2 id="modal-title">Record Kaumātua Feedback</h2>
            <button class="modal-close" aria-label="Close" @click="closeModal">&times;</button>
          </div>

          <form @submit.prevent="handleAddFeedback">
            <fieldset :disabled="saving" class="feedback-fields">
              <p class="modal-desc">
                Record a quote, whānau reflection, or observation from your class.
              </p>

              <div v-if="newEntryError" class="form-error" style="margin-bottom: 16px;" role="alert">
                {{ newEntryError }}
              </div>

              <div class="form-group">
                <label for="feedback-quote">Quote / Feedback</label>
                <textarea
                  id="feedback-quote"
                  v-model="newEntry.quote"
                  rows="4"
                  required
                  placeholder="What did the participant share? e.g. 'I was able to get up from my chair without needing my stick this morning…'"
                ></textarea>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="feedback-participant">Kaumātua / Participant</label>
                  <select id="feedback-participant" v-model="newEntry.participant">
                    <option value="">Choose a participant (or session below)</option>
                    <option v-for="p in participants" :key="p.id" :value="p.id">
                      {{ p.full_name }}
                    </option>
                  </select>
                </div>

                <div class="form-group">
                  <label for="feedback-session">Class Session</label>
                  <select id="feedback-session" v-model="newEntry.session">
                    <option value="">No specific session</option>
                    <option v-for="s in sessions" :key="s.id" :value="s.id">
                      {{ s.date }} · {{ s.activity }}
                    </option>
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
                  <span>Kaumātua has given consent for this quote to be included in reports</span>
                </label>
              </div>

              <div class="modal-actions">
                <button type="button" class="btn-cancel" @click="closeModal">Cancel</button>
                <button type="submit" class="btn-primary">
                  {{ saving ? 'Saving…' : 'Save entry' }}
                </button>
              </div>
            </fieldset>
          </form>
        </div>
      </div>

    </main>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
}

.controls-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.pills {
  display: flex;
  gap: 6px;
  background: var(--surface-sunken);
  padding: 4px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border);
}

.pill {
  background: transparent;
  border: none;
  border-radius: var(--radius-pill);
  padding: 6px 14px;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.pill:hover {
  color: var(--text);
}

.pill.active {
  background: var(--surface);
  color: var(--teal);
  box-shadow: var(--shadow-xs);
}

.search-wrap {
  min-width: 260px;
}

.search-input {
  width: 100%;
  padding: 8px 14px;
  font-size: var(--text-sm);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  color: var(--text);
  outline: none;
  transition: border-color 0.15s ease;
}

.search-input:focus {
  border-color: var(--teal);
}

.feedback-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.feedback-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-card);
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease;
}

.feedback-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-panel);
}

.quote-text {
  margin: 0 0 18px 0;
  font-size: var(--text-base);
  font-style: italic;
  line-height: 1.6;
  color: var(--text);
}

.feedback-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-xs);
  color: var(--text-muted);
  gap: 12px;
  flex-wrap: wrap;
  border-top: 1px solid var(--border);
  padding-top: 14px;
}

.feedback-source strong {
  color: var(--text);
}

.recorded-by {
  color: var(--text-secondary);
}

.consent-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.consent-yes {
  background: var(--success-bg, #ecfdf5);
  color: var(--success, #10b981);
  border: 1px solid var(--success, #10b981);
}

.consent-no {
  background: var(--sand-light, #f1f5f9);
  color: var(--bark, #64748b);
  border: 1px solid var(--border);
}

.empty-card {
  text-align: center;
  padding: 48px 24px;
  background: var(--surface);
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-lg);
}

.empty-card h3 {
  font-size: var(--text-lg);
  margin-bottom: 8px;
  color: var(--text);
}

.empty-card p {
  color: var(--text-muted);
  max-width: 440px;
  margin: 0 auto;
}

.loading-state {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

/* Modal styles */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(11, 19, 43, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 16px;
}

.dash-page .modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-modal);
  width: 100%;
  max-width: 600px;
  padding: 28px;
  box-sizing: border-box;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.modal-header h2 {
  font-size: var(--text-xl);
  font-weight: 700;
  margin: 0;
  color: var(--text);
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-muted);
}

.modal-close:hover {
  color: var(--text);
}

.modal-desc {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: 18px;
}

.feedback-fields {
  border: none;
  margin: 0;
  padding: 0;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.form-group textarea,
.form-group select,
.form-group input {
  width: 100%;
  padding: 10px 12px;
  font-size: var(--text-sm);
  background: var(--surface);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  color: var(--text);
  box-sizing: border-box;
}

.form-group textarea:focus,
.form-group select:focus,
.form-group input:focus {
  border-color: var(--teal);
  outline: none;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.checkbox-group {
  margin: 16px 0 24px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  cursor: pointer;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid var(--border);
  padding-top: 18px;
}

.btn-cancel {
  background: transparent;
  border: 1px solid var(--border-strong);
  color: var(--text);
  border-radius: var(--radius);
  padding: 9px 16px;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
}

.btn-cancel:hover {
  background: var(--surface-sunken);
}

.btn-primary {
  background: var(--primary);
  color: var(--text-on-ink);
  border: none;
  border-radius: var(--radius);
  padding: 9px 18px;
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-dark);
  box-shadow: 0 2px 8px var(--shadow-glow, rgba(37, 99, 235, 0.35));
}

.form-error {
  background: var(--danger-bg, #fef2f2);
  border: 1px solid var(--danger, #ef4444);
  color: var(--danger, #ef4444);
  padding: 10px 14px;
  border-radius: var(--radius);
  font-size: var(--text-sm);
}

@media (max-width: 600px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  .feedback-grid {
    grid-template-columns: 1fr;
  }
}
</style>
