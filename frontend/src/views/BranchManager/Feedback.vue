<script setup>
import { ref, computed, onMounted } from 'vue'
import { auth } from '@/stores/auth.js'
import { listParticipants } from '@/apis.js'

const activeFilter = ref('all') // 'all', 'with', 'without'
const search = ref('')
const showModal = ref(false)
const participants = ref([])
const loadingParticipants = ref(false)

const STORAGE_KEY = 'taurite_tu_bm_feedback'

const defaultFeedback = [
  {
    id: 'fb-1',
    quote: "I can now walk down to the marae without needing to stop for a breath on the hill. My balance has returned.",
    source: "Hinepare K.",
    date: "14 Sep 2026",
    recordedBy: "Rawiri T. (Instructor)",
    consent: true,
  },
  {
    id: 'fb-2',
    quote: "The exercises have helped so much with getting in and out of the car. I feel much steadier on my feet.",
    source: "Tāne M.",
    date: "8 Sep 2026",
    recordedBy: "Materoa N. (Branch Manager)",
    consent: true,
  },
  {
    id: 'fb-3',
    quote: "Struggled with the knee flex exercises today due to arthritis flare-up, but enjoyed the waiata and social aspect.",
    source: "Mereana R.",
    date: "2 Sep 2026",
    recordedBy: "Rawiri T. (Instructor)",
    consent: false,
  },
  {
    id: 'fb-4',
    quote: "My whānau noticed I'm standing taller and not holding onto furniture when I walk across the room.",
    source: "Wiremu P.",
    date: "28 Aug 2026",
    recordedBy: "Rawiri T. (Instructor)",
    consent: true,
  },
]

const feedbackList = ref([])

function loadFeedback() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      feedbackList.value = JSON.parse(saved)
      return
    } catch {
      // fallback if corrupted
    }
  }
  feedbackList.value = [...defaultFeedback]
  saveFeedback()
}

function saveFeedback() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(feedbackList.value))
}

const managerName = computed(() => {
  const u = auth.user
  if (!u) return 'Branch Manager'
  const name = `${u.first_name ?? ''} ${u.last_name ?? ''}`.trim()
  return name ? `${name} (Branch Manager)` : `${u.email} (Branch Manager)`
})

const branchName = computed(() => auth.user?.branch?.name ?? 'Your branch')

/* ---- new entry form ---- */
const newEntry = ref({
  quote: '',
  source: '',
  date: new Date().toISOString().split('T')[0],
  consent: true,
})

const newEntryError = ref(null)

function openModal() {
  newEntry.value = {
    quote: '',
    source: '',
    date: new Date().toISOString().split('T')[0],
    consent: true,
  }
  newEntryError.value = null
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  newEntryError.value = null
}

function handleAddFeedback() {
  if (!newEntry.value.quote.trim()) {
    newEntryError.value = 'Please enter a quote or feedback note.'
    return
  }
  if (!newEntry.value.source.trim()) {
    newEntryError.value = 'Please enter the participant or source name.'
    return
  }

  // Format date nicely
  const d = new Date(newEntry.value.date)
  const formattedDate = d.toLocaleDateString('en-NZ', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })

  feedbackList.value.unshift({
    id: 'fb-' + Date.now(),
    quote: newEntry.value.quote.trim(),
    source: newEntry.value.source.trim(),
    date: formattedDate,
    recordedBy: managerName.value,
    consent: Boolean(newEntry.value.consent),
  })

  saveFeedback()
  closeModal()
}

const filteredFeedback = computed(() => {
  const query = search.value.toLowerCase().trim()
  return feedbackList.value.filter(f => {
    // Consent filter
    if (activeFilter.value === 'with' && !f.consent) return false
    if (activeFilter.value === 'without' && f.consent) return false

    // Search query
    if (query) {
      const matchQuote = f.quote.toLowerCase().includes(query)
      const matchSource = f.source.toLowerCase().includes(query)
      const matchAuthor = f.recordedBy.toLowerCase().includes(query)
      if (!matchQuote && !matchSource && !matchAuthor) return false
    }

    return true
  })
})

onMounted(async () => {
  loadFeedback()
  loadingParticipants.value = true
  try {
    const data = await listParticipants()
    participants.value = Array.isArray(data) ? data : (data.results || [])
  } catch {
    participants.value = []
  } finally {
    loadingParticipants.value = false
  }
})
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
        <button class="btn-primary" @click="openModal">+ New entry</button>
      </div>

      <!-- Controls: Filters & Search -->
      <div class="controls-row">
        <div class="pills">
          <button
            :class="['pill', { active: activeFilter === 'all' }]"
            @click="activeFilter = 'all'"
          >
            All ({{ feedbackList.length }})
          </button>
          <button
            :class="['pill', { active: activeFilter === 'with' }]"
            @click="activeFilter = 'with'"
          >
            With quote consent ({{ feedbackList.filter(f => f.consent).length }})
          </button>
          <button
            :class="['pill', { active: activeFilter === 'without' }]"
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
          />
        </div>
      </div>

      <!-- Feedback Cards List -->
      <div v-if="filteredFeedback.length === 0" class="card empty-card">
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
      <div v-if="showModal" class="modal-backdrop" @click.self="closeModal">
        <div class="modal" role="dialog" aria-labelledby="modal-title">
          <div class="modal-header">
            <h2 id="modal-title">Record feedback entry</h2>
            <button class="modal-close" aria-label="Close" @click="closeModal">&times;</button>
          </div>

          <form @submit.prevent="handleAddFeedback">
            <p class="modal-desc">
              Record a participant quote or qualitative observation from a session or check-in.
            </p>

            <div v-if="newEntryError" class="form-error" style="margin-bottom: 16px;">
              {{ newEntryError }}
            </div>

            <div class="form-group">
              <label for="feedback-quote">Quote / Feedback text</label>
              <textarea
                id="feedback-quote"
                v-model="newEntry.quote"
                rows="4"
                required
                placeholder="What did the participant share? e.g. 'I was able to walk without my stick this week…'"
              ></textarea>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="feedback-source">Participant / Source name</label>
                <input
                  id="feedback-source"
                  v-model="newEntry.source"
                  list="participant-suggestions"
                  type="text"
                  required
                  placeholder="e.g. Hinepare K."
                />
                <datalist id="participant-suggestions">
                  <option
                    v-for="p in participants"
                    :key="p.id"
                    :value="p.preferred_name || p.full_name"
                  />
                </datalist>
              </div>

              <div class="form-group">
                <label for="feedback-date">Date recorded</label>
                <input
                  id="feedback-date"
                  v-model="newEntry.date"
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
                <span>Participant has given consent for this quote to be included in reports</span>
              </label>
            </div>

            <div class="modal-actions">
              <button type="button" class="btn-cancel" @click="closeModal">Cancel</button>
              <button type="submit" class="btn-primary">Save entry</button>
            </div>
          </form>
        </div>
      </div>

    </main>
  </div>
</template>

<style scoped>
.controls-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.search-wrap {
  flex: 1;
  min-width: 240px;
  max-width: 380px;
}

.search-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--ink);
  font-size: var(--text-sm);
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
