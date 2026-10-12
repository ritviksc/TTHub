<script setup>
import { ref } from 'vue'
import { auth } from '@/stores/auth.js'
import { saveReportNarrative } from '@/apis.js'
import MarkdownResponse from '@/components/MarkdownResponse.vue'

const props = defineProps({ text: String, jobId: String, reportType: String })
const emit = defineEmits(['saved', 'busy'])
const editing = ref(false), saving = ref(false), draft = ref(''), error = ref(''), saved = ref(false)

function edit() {
  draft.value = props.text
  error.value = ''
  saved.value = false
  editing.value = true
  emit('busy', true)
}
function cancel() {
  editing.value = false
  error.value = ''
  emit('busy', false)
}
async function save() {
  if (saving.value || !draft.value.trim()) return
  saving.value = true
  error.value = ''
  try {
    const result = await saveReportNarrative(props.reportType, props.jobId, draft.value)
    emit('saved', result.narrative)
    cancel()
    saved.value = true
  } catch (e) {
    error.value = e.response?.data?.narrative?.[0] || e.response?.data?.detail || 'Could not save your changes. Your edits are still here; please try again.'
  } finally { saving.value = false }
}
</script>

<template>
  <div>
    <form v-if="editing" @submit.prevent="save">
      <div class="form-group">
        <label :for="`${reportType}-narrative`">Edit report explanation (Markdown supported)</label>
        <textarea :id="`${reportType}-narrative`" v-model="draft" rows="16" maxlength="100000" required :disabled="saving" />
      </div>
      <div class="editor-actions">
        <button class="btn-primary" :disabled="saving || !draft.trim()">{{ saving ? 'Saving…' : 'Save changes' }}</button>
        <button class="btn-cancel" type="button" :disabled="saving" @click="cancel">Cancel</button>
      </div>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    </form>
    <template v-else>
      <MarkdownResponse :text="text" />
      <button v-if="auth.user?.role === 'super_admin' && jobId" class="btn-cancel" type="button" @click="edit">Edit report</button>
      <p v-if="saved" class="loading-note" role="status">Changes saved.</p>
    </template>
  </div>
</template>

<style scoped>
textarea { width: 100%; resize: vertical; }
.editor-actions { display: flex; gap: 12px; }
</style>
