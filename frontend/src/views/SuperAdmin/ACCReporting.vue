<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getACCSources, generateACCReport, getACCAnalysisJob, listBranches } from '@/apis.js'
import { recentReportPeriod } from '@/utils/reporting.js'
import { physicalError } from '@/utils/physicalTests.js'
import { waitForAnalysis } from '@/utils/analysisJobs.js'
import QuarterPeriod from '@/components/reporting/QuarterPeriod.vue'
import ModelSelector from '@/components/reporting/ModelSelector.vue'
import ACCReport from '@/components/reporting/ACCReport.vue'
import { feedbackSpeakerLabel } from '@/utils/feedback.js'

const dates = recentReportPeriod()
const startDate = ref(dates.start_date), endDate = ref(dates.end_date), branchId = ref('')
const branches = ref([]), branchError = ref(''), error = ref(''), candidates = ref(null), page = ref(1)
const selected = ref({}), approved = ref(false), model = ref(''), result = ref(null)
const loading = ref(false), generating = ref(false), editing = ref(false), status = ref('')
const busy = computed(() => loading.value || generating.value || editing.value)
const sources = computed(() => Object.values(selected.value))
const characters = computed(() => sources.value.reduce((count, source) => count + source.text.length, 0))
const ready = computed(() => candidates.value && sources.value.length > 0 && sources.value.length <= 100 && characters.value <= 40000 && sources.value.every(source => source.text.trim() && source.text.length <= 4000) && approved.value && model.value)
const scope = () => ({ start_date: startDate.value, end_date: endDate.value, ...(branchId.value ? { branch_id: branchId.value } : {}) })
let controller, requestId = 0
onBeforeUnmount(() => { controller?.abort(); requestId++ })
watch([startDate, endDate, branchId], () => {
  requestId++
  candidates.value = null; selected.value = {}; approved.value = false; result.value = null; error.value = ''; loading.value = false
})
watch(selected, () => { approved.value = false }, { deep: true })

async function load(pageNumber = 1) {
  if (busy.value) return
  error.value = ''
  if (!startDate.value || !endDate.value || startDate.value > endDate.value) { error.value = 'Choose valid reporting dates.'; return }
  const id = ++requestId
  loading.value = true
  try {
    const data = await getACCSources(scope(), pageNumber)
    if (id !== requestId) return
    candidates.value = data; page.value = pageNumber
  } catch (e) { if (id === requestId) error.value = physicalError(e) }
  finally { if (id === requestId) loading.value = false }
}
function select(source, checked) {
  if (checked) selected.value[source.id] = { ...source }
  else delete selected.value[source.id]
}
async function generate() {
  if (busy.value || !ready.value) return
  controller = new AbortController()
  const signal = controller.signal
  generating.value = true; error.value = ''; status.value = 'queued'; result.value = null
  try {
    const job = await generateACCReport({ ...scope(), model: model.value, approved_for_acc_and_ai: approved.value,
      sources: sources.value.map(({ id, text }) => ({ id, text })) })
    if (signal.aborted) return
    const completed = job.status === 'succeeded' ? job : await waitForAnalysis(
      () => getACCAnalysisJob(job.job_id, signal), { signal, onStatus: value => { status.value = value } },
    )
    if (!signal.aborted) result.value = completed
  } catch (e) { if (!signal.aborted) error.value = e.response ? physicalError(e) : e.message }
  finally { generating.value = false }
}
onMounted(async () => {
  load()
  try { branches.value = await listBranches() }
  catch { branchError.value = 'Could not load branch options. Reporting across all branches is still available.' }
})
</script>

<template>
  <div class="dash-page"><main class="content">
    <RouterLink class="back-link" :to="{ name: 'sa-reporting' }">← Reporting options</RouterLink>
    <p><RouterLink :to="{ name: 'sa-acc-history' }">View past ACC reports</RouterLink></p>
    <div class="page-header"><h1>Prepare an ACC report</h1></div>
    <p class="page-subtitle">Select a reporting period and consented feedback. Review the text before generating a draft with recorded participation and testing figures.</p>
    <form @submit.prevent="load(1)"><fieldset :disabled="busy">
      <legend>Reporting period and scope</legend>
      <div class="form-row">
        <div class="form-group"><label for="acc-from">From (inclusive)</label><input id="acc-from" v-model="startDate" type="date" required /></div>
        <div class="form-group"><label for="acc-to">To (inclusive)</label><input id="acc-to" v-model="endDate" type="date" required /></div>
      </div>
      <div class="form-group"><label for="acc-branch">Branch</label><select id="acc-branch" v-model="branchId"><option value="">All branches</option><option v-for="branch in branches" :key="branch.id" :value="branch.id">{{ branch.name }}</option></select></div>
      <QuarterPeriod :branch-id="branchId" @select="startDate = $event.start_date; endDate = $event.end_date" />
      <button class="btn-primary">Load feedback</button>
    </fieldset></form>
    <p v-if="branchError" class="form-error" role="alert">{{ branchError }}</p>
    <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    <p v-if="loading" class="loading-note" role="status">Loading consented feedback…</p>
    <p v-if="!candidates && !loading" class="loading-note">Load feedback for the selected dates before generating a draft.</p>
    <template v-if="candidates">
      <section class="card report-section"><h2>Select feedback</h2>
        <p>Only feedback with recorded reporting consent appears here. Select a representative mix, including challenges and requests for improvement.</p>
        <p v-if="!candidates.count">No consented feedback was recorded for this period and scope.</p>
        <fieldset :disabled="busy">
          <label v-for="source in candidates.results" :key="source.id" class="feedback-option">
            <input type="checkbox" :checked="!!selected[source.id]" @change="select(source, $event.target.checked)" />
            <span><strong>{{ source.branch }} · {{ source.date }} · {{ feedbackSpeakerLabel(source.speaker) }}</strong><span class="source-text">{{ source.text }}</span></span>
          </label>
          <div v-if="candidates.count" class="actions">
            <button type="button" class="btn-cancel" :disabled="!candidates.previous" @click="load(page - 1)">Previous</button>
            <span>Page {{ page }} · {{ candidates.count }} items</span>
            <button type="button" class="btn-cancel" :disabled="!candidates.next" @click="load(page + 1)">Next</button>
          </div>
        </fieldset>
      </section>
      <form @submit.prevent="generate"><fieldset :disabled="busy">
        <section v-if="sources.length" class="card report-section">
          <details class="feedback-review">
            <summary><h2>Review selected text ({{ sources.length }} selected)</h2></summary>
            <p>{{ sources.length }} selected · {{ characters.toLocaleString() }} / 40,000 characters. Maximum 100 items and 4,000 characters per item.</p>
            <p>Remove names and other identifying details from each reporting copy. Keep the original meaning. Speaker types are carried through from the recorded feedback automatically.</p>
            <details v-for="source in sources" :key="source.id" class="source-editor">
              <summary>{{ source.branch }} · {{ source.date }} · {{ feedbackSpeakerLabel(source.speaker) }}</summary>
              <div class="form-group"><label :for="`copy-${source.id}`">Reporting copy (redact identifying details only)</label><textarea :id="`copy-${source.id}`" v-model="source.text" rows="5" maxlength="4000" required /></div>
              <button type="button" class="btn-cancel" @click="delete selected[source.id]">Remove from draft</button>
            </details>
          </details>
          <label class="feedback-option"><input v-model="approved" type="checkbox" /><span>I confirm the selected reporting copies are approved for ACC reporting and AI processing, and I have removed unnecessary identifying details.</span></label>
        </section>
        <ModelSelector v-model="model" :disabled="busy" />
        <button class="btn-primary" :disabled="!ready">{{ generating ? 'Generating…' : 'Generate ACC draft' }}</button>
      </fieldset></form>
    </template>
    <p v-if="generating" class="loading-note" role="status">{{ status === 'queued' ? 'Queued — waiting for a worker…' : 'Drafting the report and checking its source references…' }}</p>
    <ACCReport v-if="result" :key="result.job_id" :saved-report="result" @busy="editing = $event" />
  </main></div>
</template>

<style scoped>
fieldset { border: 0; padding: 0; margin: 0 0 24px; min-width: 0; }
legend { margin-bottom: 12px; }
.report-section { margin-bottom: 24px; }
.feedback-option { display: flex; align-items: flex-start; gap: 12px; padding: 12px 0; }
.feedback-option input { width: auto; flex-shrink: 0; margin-top: 4px; }
.source-text { display: block; white-space: pre-wrap; overflow-wrap: anywhere; }
.source-editor { border-top: 1px solid var(--border); padding: 16px 0; }
.feedback-review > summary, .source-editor > summary { cursor: pointer; font-weight: 600; }
.feedback-review > summary h2 { display: inline; }
.feedback-review[open] > summary, .source-editor[open] > summary { margin-bottom: 12px; }
textarea { width: 100%; resize: vertical; }
.actions { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
</style>
