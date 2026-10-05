<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import ModelSelector from './ModelSelector.vue'
import MarkdownResponse from '@/components/MarkdownResponse.vue'
import { waitForAnalysis } from '@/utils/analysisJobs.js'
import { physicalError } from '@/utils/physicalTests.js'
const props = defineProps({ scope: Object, start: Function, getStatus: Function, hasData: Boolean, disabled: Boolean })
const emit = defineEmits(['complete', 'busy'])
const busy = ref(false)
const status = ref('queued')
const narrative = ref('')
const selectedModel = ref(''), usedModel = ref('')
watch(selectedModel, () => { narrative.value = ''; error.value = '' })
const error = ref('')
let controller
onBeforeUnmount(() => controller?.abort())
async function analyse() {
  if (busy.value || props.disabled || !props.hasData || !selectedModel.value) return
  controller = new AbortController()
  const signal = controller.signal
  busy.value = true
  emit('busy', true)
  error.value = ''
  narrative.value = ''
  status.value = 'queued'
  try {
    const job = await props.start({ ...props.scope, model: selectedModel.value })
    if (signal.aborted) return
    const result = job.status === 'succeeded' ? job : await waitForAnalysis(
      () => props.getStatus(job.job_id, signal), { signal, onStatus: value => { status.value = value } },
    )
    if (signal.aborted) return
    narrative.value = result.narrative
    usedModel.value = result.model
    emit('complete', result)
  } catch (e) { if (!signal.aborted) error.value = e.response ? physicalError(e) : e.message }
  finally { busy.value = false; emit('busy', false) }
}
</script>

<template>
  <section class="card" aria-live="polite">
    <h2>AI explanation</h2>
    <p>Request an explanation of the calculated figures. Only aggregate statistics are sent for analysis.</p>
    <ModelSelector v-model="selectedModel" :disabled="busy || disabled" />
    <button class="btn-primary" :disabled="busy || disabled || !hasData || !selectedModel" @click="analyse">{{ busy ? 'Analysing…' : 'Analyse physical testing' }}</button>
    <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    <p v-if="busy" class="loading-note">{{ status === 'queued' ? 'Queued — waiting for a worker…' : 'Generating the explanation…' }}</p>
    <p v-if="narrative && usedModel" class="loading-note">Model: {{ usedModel }}</p>
    <MarkdownResponse v-if="narrative" :text="narrative" />
    <p v-if="narrative" class="loading-note">AI-generated explanations may vary between requests. Check the figures before using this in a report. This is not a clinical assessment.</p>
  </section>
</template>
