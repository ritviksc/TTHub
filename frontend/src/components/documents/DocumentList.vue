<script setup>
import { ref, onMounted, watch } from 'vue'
import { listDocuments, uploadDocument, updateDocument, downloadDocument, deleteDocument } from '@/apis.js'

// A flat list of one participant's documents. Branch and organisation files,
// which have folders, are shown by FileExplorer instead.
const props = defineProps({
  participantId: { type: String, required: true },
  canUpload: { type: Boolean, default: false },
})

const documents = ref([])
const loading = ref(true)
const loadError = ref('')
const error = ref('')
const uploading = ref(false)
const busyId = ref(null)
const fileInput = ref(null)

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    documents.value = await listDocuments({ participant: props.participantId })
  } catch {
    loadError.value = 'Could not load documents.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => props.participantId, load)

function sizeLabel(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function upload() {
  const file = fileInput.value?.files[0]
  if (!file) return

  uploading.value = true
  error.value = ''
  const formData = new FormData()
  formData.append('file', file)
  formData.append('participant', props.participantId)

  try {
    const created = await uploadDocument(formData)
    documents.value = [created, ...documents.value]
    fileInput.value.value = ''
  } catch (e) {
    error.value = e.response?.data?.file?.[0] ?? e.response?.data?.detail ?? 'Could not upload that file.'
  } finally {
    uploading.value = false
  }
}

async function download(entry) {
  error.value = ''
  try {
    const blob = await downloadDocument(entry.id)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = entry.name
    link.click()
    // Give the browser time to start the download before releasing its blob.
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch {
    error.value = `Could not download ${entry.name}.`
  }
}

async function remove(entry) {
  if (!confirm(`Delete ${entry.name}? This cannot be undone.`)) return

  busyId.value = entry.id
  error.value = ''
  try {
    await deleteDocument(entry.id)
    documents.value = documents.value.filter(d => d.id !== entry.id)
  } catch (e) {
    error.value = e.response?.data?.detail ?? `Could not delete ${entry.name}.`
  } finally {
    busyId.value = null
  }
}

/* ---- rename ---- */

const renaming = ref(null)
const renameName = ref('')
const renameError = ref('')
const renameBusy = ref(false)

function startRename(entry) {
  renaming.value = entry
  renameName.value = entry.name
  renameError.value = ''
}

async function confirmRename() {
  if (!renameName.value.trim()) return
  renameBusy.value = true
  renameError.value = ''
  try {
    const updated = await updateDocument(renaming.value.id, { name: renameName.value.trim() })
    const index = documents.value.findIndex(d => d.id === updated.id)
    if (index !== -1) documents.value[index] = updated
    renaming.value = null
  } catch (e) {
    renameError.value = e.response?.data?.name?.[0] ?? e.response?.data?.detail ?? 'Could not rename that document.'
  } finally {
    renameBusy.value = false
  }
}
</script>

<template>
  <div class="document-list">
    <div v-if="canUpload" class="upload-row">
      <input ref="fileInput" type="file" accept=".pdf,.jpg,.jpeg,.png,.docx,.xlsx" :disabled="uploading" />
      <button type="button" class="btn-primary" :disabled="uploading" @click="upload">
        {{ uploading ? 'Uploading…' : 'Upload' }}
      </button>
    </div>
    <p class="upload-help">PDF, JPG, PNG, Word or Excel, up to 10 MB.</p>

    <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    <p v-if="loading" class="loading-note">Loading documents…</p>
    <p v-else-if="loadError" class="form-error" role="alert">{{ loadError }}</p>
    <table v-else-if="documents.length" class="data-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Size</th>
          <th>Uploaded</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="entry in documents" :key="entry.id">
          <td>{{ entry.name }}</td>
          <td>{{ sizeLabel(entry.size) }}</td>
          <td>
            {{ new Date(entry.uploaded_at).toLocaleDateString('en-NZ') }}
            <template v-if="entry.uploaded_by_name"> — {{ entry.uploaded_by_name }}</template>
          </td>
          <td class="document-actions">
            <button type="button" class="link-action" @click="download(entry)">Download</button>
            <template v-if="entry.can_manage">
              <button type="button" class="link-action" @click="startRename(entry)">Rename</button>
              <button
                type="button"
                class="link-danger"
                :disabled="busyId === entry.id"
                @click="remove(entry)"
              >
                {{ busyId === entry.id ? 'Deleting…' : 'Delete' }}
              </button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="empty-note">No documents yet.</p>

    <!-- Rename -->
    <div v-if="renaming" class="modal-backdrop" @click.self="renaming = null">
      <div class="modal">
        <h2>Rename document</h2>
        <div class="form-group">
          <label for="document-rename">Name</label>
          <input id="document-rename" v-model="renameName" :disabled="renameBusy" @keyup.enter="confirmRename" />
        </div>
        <p v-if="renameError" class="form-error">{{ renameError }}</p>
        <div class="modal-actions">
          <button type="button" class="btn-cancel" @click="renaming = null">Cancel</button>
          <button type="button" class="btn-primary" :disabled="renameBusy" @click="confirmRename">
            {{ renameBusy ? 'Saving…' : 'Save' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.upload-help { font-size: var(--text-sm); color: var(--text-faint); margin: 8px 0 16px; }

.upload-row input[type="file"] {
  font-size: var(--text-base);
  color: var(--text-secondary);
}
.upload-row input[type="file"]::file-selector-button {
  background: var(--surface);
  color: var(--text);
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius-sm);
  padding: 8px 18px;
  font-size: var(--text-base);
  font-weight: 600;
  margin-right: 12px;
  cursor: pointer;
}
.upload-row input[type="file"]::file-selector-button:hover {
  border-color: var(--text-muted);
}
.document-actions { display: flex; gap: 16px; white-space: nowrap; }
.link-action, .link-danger {
  background: none; border: none; padding: 0;
  font-size: var(--text-base); font-weight: 600;
}
.link-action { color: var(--text); }
.link-danger { color: var(--danger); }
.link-action:hover:not(:disabled), .link-danger:hover:not(:disabled) { text-decoration: underline; }
.empty-note { color: var(--text-faint); font-size: var(--text-base); }

/* dashboard.css fixes the modal at 480px; keep it inside the screen on phones. */
.modal { max-width: calc(100% - 32px); }
</style>
