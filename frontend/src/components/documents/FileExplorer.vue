<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import {
  listFolders, createFolder, updateFolder, deleteFolder,
  listDocuments, uploadDocument, updateDocument, downloadDocument, deleteDocument,
} from '@/apis.js'
import { childrenOf, folderAndDescendantIds, folderTrail, pushRecent } from '@/utils/documents.js'
import BranchSwitcher from './BranchSwitcher.vue'
import FolderTree from './FolderTree.vue'

// Each scope is one top-level place: the organisation area or a branch.
// { key, label, region, branchId (null for organisation), canUpload, canManage }
// The sidebar shows the organisation plus one branch at a time; with more than
// one branch available, a switcher picks which.
const props = defineProps({
  scopes: { type: Array, required: true },
  initialKey: { type: String, default: null },
})
const emit = defineEmits(['scope-change'])

const ACCEPT = '.pdf,.jpg,.jpeg,.png,.docx,.xlsx'

/* ---- where we are ---- */

const activeKey = ref(null)
const scope = computed(() => props.scopes.find(s => s.key === activeKey.value) ?? null)
const currentFolderId = ref(null)

const orgScope = computed(() => props.scopes.find(s => !s.branchId) ?? null)
const branchScopes = computed(() => props.scopes.filter(s => s.branchId))
// The branch shown in the sidebar's branch slot, even while the organisation
// area is open, so switching back is one click.
const selectedBranchKey = ref(null)
const selectedBranch = computed(() => branchScopes.value.find(s => s.key === selectedBranchKey.value) ?? null)

// Recently opened branches, most recent first. Kept in this browser only: it
// is a convenience, so a blocked or empty store just means no recents.
const RECENT_STORAGE_KEY = 'documents.recentBranches'
function readRecent() {
  try {
    const stored = JSON.parse(localStorage.getItem(RECENT_STORAGE_KEY) ?? '[]')
    return Array.isArray(stored) ? stored : []
  } catch {
    return []
  }
}
const recentKeys = ref(readRecent())

// Once someone picks a location, a late-arriving scope list must not move them.
let userNavigated = false
const isBranchKey = key => branchScopes.value.some(s => s.key === key)

// Scopes can arrive late (a Super Admin's branch list loads after mount), so
// settle on the preferred scope once it exists.
watch(() => props.scopes, scopes => {
  const preferred = scopes.find(s => s.key === props.initialKey)?.key
  if (!userNavigated && preferred && activeKey.value !== preferred) activeKey.value = preferred
  else if (!scopes.some(s => s.key === activeKey.value)) activeKey.value = preferred ?? scopes[0]?.key ?? null

  if (!isBranchKey(selectedBranchKey.value)) {
    selectedBranchKey.value = (isBranchKey(activeKey.value) ? activeKey.value : null)
      ?? recentKeys.value.find(isBranchKey)
      ?? branchScopes.value[0]?.key
      ?? null
  }
}, { immediate: true })

const folders = ref([])
const documents = ref([])
const loadingDocuments = ref(false)
const error = ref('')

const subfolders = computed(() => childrenOf(folders.value, currentFolderId.value))
const trail = computed(() => folderTrail(folders.value, currentFolderId.value))
const currentName = computed(() => trail.value.at(-1)?.name ?? scope.value?.label ?? '')
const isEmpty = computed(() => !loadingDocuments.value && !subfolders.value.length && !documents.value.length)

function scopeParams() {
  return scope.value.branchId ? { branch: scope.value.branchId } : { scope: 'organisation' }
}

// Switching branches can outrun the network too, so only the latest lands.
let folderRequest = 0
async function loadFolders() {
  const request = ++folderRequest
  folders.value = []
  try {
    const result = await listFolders(scopeParams())
    if (request === folderRequest) folders.value = result
  } catch {
    if (request === folderRequest) error.value = 'Could not load folders.'
  }
}

// Folder clicks can outrun the network, so only the latest request may land.
let documentRequest = 0
async function loadDocuments() {
  const request = ++documentRequest
  loadingDocuments.value = true
  try {
    const result = await listDocuments({ ...scopeParams(), folder: currentFolderId.value ?? 'root' })
    if (request === documentRequest) documents.value = result
  } catch {
    if (request === documentRequest) {
      documents.value = []
      error.value = 'Could not load files.'
    }
  } finally {
    if (request === documentRequest) loadingDocuments.value = false
  }
}

watch(activeKey, () => {
  if (!scope.value) return
  error.value = ''
  currentFolderId.value = null
  if (scope.value.branchId) {
    selectedBranchKey.value = activeKey.value
    recentKeys.value = pushRecent(recentKeys.value, activeKey.value)
    try { localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(recentKeys.value)) } catch { /* no recents */ }
  }
  emit('scope-change', activeKey.value)
  loadFolders()
  loadDocuments()
}, { immediate: true })

watch(currentFolderId, () => {
  closeMenu()
  if (scope.value) loadDocuments()
})

function openFolder(id) {
  currentFolderId.value = id
}

/* ---- sidebar ---- */

const switcherOpen = ref(false)

function selectScope(key) {
  userNavigated = true
  if (key === activeKey.value) currentFolderId.value = null
  else activeKey.value = key
}

function chooseBranch(key) {
  switcherOpen.value = false
  selectScope(key)
}

/* ---- row menus ---- */

const openMenu = ref(null)

function toggleMenu(key) {
  openMenu.value = openMenu.value === key ? null : key
}

function closeMenu() {
  openMenu.value = null
}

function onKeydown(event) {
  if (event.key !== 'Escape') return
  closeMenu()
  switcherOpen.value = false
  if (!dialogBusy.value) dialog.value = null
}

onMounted(() => {
  document.addEventListener('click', closeMenu)
  document.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', closeMenu)
  document.removeEventListener('keydown', onKeydown)
})

/* ---- helpers ---- */

function sizeLabel(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function fileIcon(name) {
  const extension = name.split('.').pop().toLowerCase()
  if (['jpg', 'jpeg', 'png'].includes(extension)) return '🖼'
  if (extension === 'docx') return '📝'
  if (extension === 'xlsx') return '📊'
  return '📄'
}

function firstError(e, fallback) {
  const data = e.response?.data
  if (typeof data?.detail === 'string') return data.detail
  const first = data && Object.values(data).flat()[0]
  return typeof first === 'string' ? first : fallback
}

/* ---- upload: button or drag and drop ---- */

const fileInput = ref(null)
const uploadStatus = ref('')

async function uploadFiles(fileList) {
  const files = [...fileList]
  if (!files.length || !scope.value?.canUpload || uploadStatus.value) return

  // Pin the destination now, in case someone clicks elsewhere mid-upload.
  const folderId = currentFolderId.value
  const branchId = scope.value.branchId
  const failures = []
  error.value = ''

  for (const [index, file] of files.entries()) {
    uploadStatus.value = files.length > 1 ? `Uploading ${index + 1} of ${files.length}…` : 'Uploading…'
    const formData = new FormData()
    formData.append('file', file)
    if (folderId) formData.append('folder', folderId)
    else if (branchId) formData.append('branch', branchId)
    try {
      const created = await uploadDocument(formData)
      if ((created.folder ?? null) === currentFolderId.value) documents.value = [created, ...documents.value]
    } catch (e) {
      failures.push(`${file.name}: ${firstError(e, 'could not be uploaded.')}`)
    }
  }

  uploadStatus.value = ''
  if (failures.length) error.value = failures.join(' ')
}

function onFilesPicked(event) {
  uploadFiles(event.target.files)
  event.target.value = ''
}

// dragenter/dragleave fire for every child element, so count them rather than
// toggling, or the overlay flickers as the cursor crosses rows.
const dragDepth = ref(0)

function carriesFiles(event) {
  return [...(event.dataTransfer?.types ?? [])].includes('Files')
}

function onDragEnter(event) {
  if (scope.value?.canUpload && carriesFiles(event)) dragDepth.value++
}

function onDragLeave() {
  if (dragDepth.value) dragDepth.value--
}

function onDrop(event) {
  const wasDragging = dragDepth.value > 0
  dragDepth.value = 0
  if (wasDragging) uploadFiles(event.dataTransfer.files)
}

/* ---- file actions ---- */

async function download(entry) {
  closeMenu()
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

function replaceDocument(updated) {
  const index = documents.value.findIndex(d => d.id === updated.id)
  if (index !== -1) documents.value[index] = updated
}

function renameFile(entry) {
  openNameDialog('Rename file', entry.name, 'Save', async name => {
    replaceDocument(await updateDocument(entry.id, { name }))
  })
}

function moveFile(entry) {
  openMoveDialog(`Move "${entry.name}"`, entry.folder ?? null, new Set(), async target => {
    const updated = await updateDocument(entry.id, { folder: target })
    if ((updated.folder ?? null) === currentFolderId.value) replaceDocument(updated)
    else documents.value = documents.value.filter(d => d.id !== updated.id)
  })
}

async function deleteFile(entry) {
  closeMenu()
  if (!confirm(`Delete "${entry.name}"? This cannot be undone.`)) return
  error.value = ''
  try {
    await deleteDocument(entry.id)
    documents.value = documents.value.filter(d => d.id !== entry.id)
  } catch (e) {
    error.value = firstError(e, `Could not delete ${entry.name}.`)
  }
}

/* ---- folder actions ---- */

function replaceFolder(updated) {
  const index = folders.value.findIndex(f => f.id === updated.id)
  if (index !== -1) folders.value[index] = updated
}

function newFolder() {
  const parent = currentFolderId.value
  const branch = scope.value.branchId
  openNameDialog('New folder', '', 'Create', async name => {
    folders.value.push(await createFolder({ name, parent, branch }))
  })
}

function renameFolder(folder) {
  openNameDialog('Rename folder', folder.name, 'Save', async name => {
    replaceFolder(await updateFolder(folder.id, { name }))
  })
}

function moveFolder(folder) {
  const excluded = folderAndDescendantIds(folders.value, folder.id)
  openMoveDialog(`Move "${folder.name}"`, folder.parent ?? null, excluded, async target => {
    replaceFolder(await updateFolder(folder.id, { parent: target }))
  })
}

async function removeFolder(folder) {
  closeMenu()
  if (!confirm(`Delete the folder "${folder.name}"?`)) return
  error.value = ''
  try {
    await deleteFolder(folder.id)
    folders.value = folders.value.filter(f => f.id !== folder.id)
  } catch (e) {
    error.value = e.response?.status === 409
      ? `"${folder.name}" still has files or folders in it. Move or delete them first.`
      : firstError(e, `Could not delete "${folder.name}".`)
  }
}

/* ---- dialogs: one name dialog (new/rename) and one move dialog ---- */

const dialog = ref(null)
const dialogBusy = ref(false)
const dialogError = ref('')

function openNameDialog(title, name, submitLabel, onSubmit) {
  closeMenu()
  dialog.value = { kind: 'name', title, name, submitLabel, onSubmit }
  dialogError.value = ''
}

function openMoveDialog(title, target, excluded, onSubmit) {
  closeMenu()
  dialog.value = { kind: 'move', title, target, excluded, submitLabel: 'Move here', onSubmit }
  dialogError.value = ''
}

async function submitDialog() {
  const current = dialog.value
  const value = current.kind === 'name' ? current.name.trim() : current.target
  if (current.kind === 'name' && !value) return
  dialogBusy.value = true
  dialogError.value = ''
  try {
    await current.onSubmit(value)
    dialog.value = null
  } catch (e) {
    dialogError.value = firstError(e, 'Something went wrong. Please try again.')
  } finally {
    dialogBusy.value = false
  }
}

function closeDialog() {
  if (!dialogBusy.value) dialog.value = null
}
</script>

<template>
  <div v-if="scope" class="explorer">
    <aside class="explorer-sidebar" aria-label="Locations">
      <ul class="scope-list">
        <li v-if="orgScope">
          <button
            type="button"
            class="scope-row"
            :class="{ open: activeKey === orgScope.key, selected: activeKey === orgScope.key && !currentFolderId }"
            @click="selectScope(orgScope.key)"
          >
            <span aria-hidden="true">🏢</span>
            <span class="scope-label">{{ orgScope.label }}</span>
          </button>
          <FolderTree
            v-if="activeKey === orgScope.key && folders.length"
            class="scope-tree"
            :folders="folders"
            :selected-id="currentFolderId"
            @select="openFolder"
          />
        </li>
        <li v-if="selectedBranch" class="branch-slot">
          <div class="branch-row">
            <button
              type="button"
              class="scope-row"
              :class="{ open: activeKey === selectedBranch.key, selected: activeKey === selectedBranch.key && !currentFolderId }"
              @click="selectScope(selectedBranch.key)"
            >
              <span aria-hidden="true">📍</span>
              <span class="scope-label">{{ selectedBranch.label }}</span>
            </button>
            <button
              v-if="branchScopes.length > 1"
              type="button"
              class="switch-button"
              :aria-expanded="switcherOpen"
              title="Switch to another branch"
              @mousedown.stop
              @click="switcherOpen = !switcherOpen"
            >
              Change ▾
            </button>
            <BranchSwitcher
              v-if="switcherOpen"
              :branches="branchScopes"
              :selected-key="selectedBranch.key"
              :recent-keys="recentKeys"
              @select="chooseBranch"
              @close="switcherOpen = false"
            />
          </div>
          <FolderTree
            v-if="activeKey === selectedBranch.key && folders.length"
            class="scope-tree"
            :folders="folders"
            :selected-id="currentFolderId"
            @select="openFolder"
          />
        </li>
      </ul>
    </aside>

    <section
      class="explorer-main"
      :class="{ dragging: dragDepth > 0 }"
      @dragenter.prevent="onDragEnter"
      @dragover.prevent
      @dragleave="onDragLeave"
      @drop.prevent="onDrop"
    >
      <header class="explorer-toolbar">
        <nav class="breadcrumb" aria-label="Folder path">
          <button type="button" class="crumb" :class="{ current: !currentFolderId }" @click="openFolder(null)">
            {{ scope.label }}
          </button>
          <template v-for="crumb in trail" :key="crumb.id">
            <span class="crumb-sep" aria-hidden="true">›</span>
            <button type="button" class="crumb" :class="{ current: crumb.id === currentFolderId }" @click="openFolder(crumb.id)">
              {{ crumb.name }}
            </button>
          </template>
        </nav>
        <div class="toolbar-actions">
          <button v-if="scope.canManage" type="button" class="btn-cancel" @click="newFolder">+ New folder</button>
          <button
            v-if="scope.canUpload"
            type="button"
            class="btn-primary"
            :disabled="!!uploadStatus"
            @click="fileInput.click()"
          >
            {{ uploadStatus || 'Upload' }}
          </button>
          <input ref="fileInput" type="file" multiple :accept="ACCEPT" hidden @change="onFilesPicked" />
        </div>
      </header>

      <div v-if="error" class="explorer-error" role="alert">
        <span>{{ error }}</span>
        <button type="button" class="dismiss" aria-label="Dismiss" @click="error = ''">✕</button>
      </div>

      <table v-if="!isEmpty" class="explorer-table">
        <thead>
          <tr>
            <th>Name</th>
            <th class="col-modified">Modified</th>
            <th class="col-size">Size</th>
            <th class="col-menu"><span class="visually-hidden">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="folder in subfolders"
            :key="folder.id"
            class="explorer-row"
            tabindex="0"
            @click="openFolder(folder.id)"
            @keydown.enter="openFolder(folder.id)"
          >
            <td class="col-name"><span class="row-icon" aria-hidden="true">📁</span>{{ folder.name }}</td>
            <td class="col-modified">—</td>
            <td class="col-size">—</td>
            <td class="col-menu" @click.stop>
              <template v-if="folder.can_manage">
                <button
                  type="button"
                  class="menu-button"
                  :aria-label="`Actions for ${folder.name}`"
                  :aria-expanded="openMenu === `folder:${folder.id}`"
                  @click.stop="toggleMenu(`folder:${folder.id}`)"
                >⋯</button>
                <div v-if="openMenu === `folder:${folder.id}`" class="row-menu" role="menu">
                  <button type="button" role="menuitem" @click="openFolder(folder.id)">Open</button>
                  <button type="button" role="menuitem" @click="renameFolder(folder)">Rename</button>
                  <button type="button" role="menuitem" @click="moveFolder(folder)">Move</button>
                  <button type="button" role="menuitem" class="danger" @click="removeFolder(folder)">Delete</button>
                </div>
              </template>
            </td>
          </tr>
          <tr
            v-for="entry in documents"
            :key="entry.id"
            class="explorer-row"
            tabindex="0"
            :title="`Download ${entry.name}`"
            @click="download(entry)"
            @keydown.enter="download(entry)"
          >
            <td class="col-name"><span class="row-icon" aria-hidden="true">{{ fileIcon(entry.name) }}</span>{{ entry.name }}</td>
            <td class="col-modified">
              {{ new Date(entry.uploaded_at).toLocaleDateString('en-NZ') }}<template v-if="entry.uploaded_by_name"> · {{ entry.uploaded_by_name }}</template>
            </td>
            <td class="col-size">{{ sizeLabel(entry.size) }}</td>
            <td class="col-menu" @click.stop>
              <button
                type="button"
                class="menu-button"
                :aria-label="`Actions for ${entry.name}`"
                :aria-expanded="openMenu === `file:${entry.id}`"
                @click.stop="toggleMenu(`file:${entry.id}`)"
              >⋯</button>
              <div v-if="openMenu === `file:${entry.id}`" class="row-menu" role="menu">
                <button type="button" role="menuitem" @click="download(entry)">Download</button>
                <template v-if="entry.can_manage">
                  <button type="button" role="menuitem" @click="renameFile(entry)">Rename</button>
                  <button type="button" role="menuitem" @click="moveFile(entry)">Move</button>
                  <button type="button" role="menuitem" class="danger" @click="deleteFile(entry)">Delete</button>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="loadingDocuments && !documents.length" class="loading-note">Loading…</p>

      <div v-if="isEmpty" class="empty-state">
        <p class="empty-title">This folder is empty</p>
        <p v-if="scope.canUpload">Drag files here, or use Upload. PDF, JPG, PNG, Word or Excel, up to 10 MB each.</p>
      </div>

      <div v-if="dragDepth > 0" class="drop-overlay" aria-hidden="true">
        Drop to upload to <strong>{{ currentName }}</strong>
      </div>
    </section>

    <div v-if="dialog" class="modal-backdrop" @click.self="closeDialog">
      <form class="modal" @submit.prevent="submitDialog">
        <h2>{{ dialog.title }}</h2>
        <div v-if="dialog.kind === 'name'" class="form-group">
          <label for="explorer-name">Name</label>
          <input id="explorer-name" v-model="dialog.name" maxlength="100" required :disabled="dialogBusy" autofocus />
        </div>
        <div v-else class="move-picker">
          <FolderTree
            :folders="folders"
            :root-label="scope.label"
            :selected-id="dialog.target"
            :excluded="dialog.excluded"
            @select="id => (dialog.target = id)"
          />
        </div>
        <p v-if="dialogError" class="form-error">{{ dialogError }}</p>
        <div class="modal-actions">
          <button type="button" class="btn-cancel" :disabled="dialogBusy" @click="closeDialog">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="dialogBusy">
            {{ dialogBusy ? 'Saving…' : dialog.submitLabel }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.explorer {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  min-height: 420px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

/* ---- sidebar ---- */

.explorer-sidebar {
  border-right: 1px solid var(--border);
  background: var(--surface-sunken);
  border-radius: var(--radius-lg) 0 0 var(--radius-lg);
  padding: 12px 8px;
}
.scope-list { list-style: none; margin: 0; padding: 0; }
.scope-row {
  display: flex; align-items: center; gap: 8px;
  width: 100%; text-align: left;
  background: none; border: none; border-radius: var(--radius-sm);
  padding: 7px 8px;
  font-size: var(--text-base); color: var(--text-secondary);
}
.scope-row:hover { background: var(--border); }
.scope-row.open { color: var(--text); font-weight: 600; }
.scope-row.selected { background: var(--teal-tint); color: var(--teal-dark); }
.scope-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.scope-tree { margin: 2px 0 6px 12px; }
.branch-slot { margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border); }
.branch-row { position: relative; display: flex; align-items: center; gap: 4px; }
.branch-row .scope-row { flex: 1; min-width: 0; }
.switch-button {
  flex: none;
  background: none; border: 1px solid var(--border-strong); border-radius: var(--radius-pill);
  padding: 3px 9px;
  font-size: var(--text-xs); font-weight: 600; color: var(--text-secondary);
}
.switch-button:hover, .switch-button[aria-expanded="true"] { border-color: var(--text-muted); color: var(--text); background: var(--surface); }

/* ---- main pane ---- */

.explorer-main { position: relative; padding: 16px 20px 20px; min-width: 0; }
.explorer-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 12px;
  padding-bottom: 12px; margin-bottom: 4px;
  border-bottom: 1px solid var(--border);
}
.breadcrumb { display: flex; align-items: center; flex-wrap: wrap; gap: 2px; min-width: 0; }
.crumb {
  background: none; border: none; padding: 4px;
  font-size: var(--text-md); font-weight: 600; color: var(--text-muted);
}
.crumb:hover:not(.current) { color: var(--text); text-decoration: underline; }
.crumb.current { color: var(--text); cursor: default; }
.crumb-sep { color: var(--text-faint); }
.toolbar-actions { display: flex; gap: 8px; }

.explorer-error {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;
  margin: 12px 0 0; padding: 10px 14px;
  background: var(--danger-bg); color: var(--danger);
  border-radius: var(--radius-sm); font-size: var(--text-base);
}
.dismiss { background: none; border: none; padding: 0; color: inherit; font-size: var(--text-base); }

/* No overflow:hidden here (unlike .data-table) so row menus are not clipped. */
.explorer-table { width: 100%; border-collapse: collapse; }
.explorer-table th {
  text-align: left; padding: 10px 8px;
  font-size: var(--text-sm); font-weight: 600; color: var(--text-muted);
  border-bottom: 1px solid var(--border);
}
.explorer-table td {
  padding: 9px 8px;
  font-size: var(--text-base); color: var(--text-secondary);
  border-bottom: 1px solid var(--border-faint);
}
.explorer-row { cursor: pointer; }
.explorer-row:hover td, .explorer-row:focus-visible td { background: var(--surface-sunken); }
.explorer-row:focus-visible { outline: 2px solid var(--teal); outline-offset: -2px; }
.col-name { color: var(--text); font-weight: 500; word-break: break-word; }
.row-icon { margin-right: 10px; }
.col-modified { white-space: nowrap; }
.col-size { white-space: nowrap; width: 80px; }
.col-menu { position: relative; width: 44px; text-align: right; cursor: default; }

.menu-button {
  width: 30px; height: 28px;
  background: none; border: none; border-radius: var(--radius-sm);
  font-size: var(--text-md); line-height: 1; color: var(--text-muted);
}
.menu-button:hover, .menu-button[aria-expanded="true"] { background: var(--border); color: var(--text); }
.row-menu {
  position: absolute; right: 8px; top: calc(100% - 4px); z-index: 20;
  display: flex; flex-direction: column;
  min-width: 150px; padding: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-panel);
}
.row-menu button {
  background: none; border: none; border-radius: var(--radius-sm);
  padding: 8px 10px; text-align: left;
  font-size: var(--text-base); color: var(--text);
}
.row-menu button:hover { background: var(--surface-sunken); }
.row-menu .danger { color: var(--danger); }

.empty-state {
  margin-top: 16px; padding: 48px 16px;
  border: 1.5px dashed var(--border-strong); border-radius: var(--radius-lg);
  text-align: center; color: var(--text-muted); font-size: var(--text-base);
}
.empty-state p { margin: 4px 0; }
.empty-title { font-weight: 600; color: var(--text-secondary); }

.drop-overlay {
  position: absolute; inset: 8px;
  display: flex; align-items: center; justify-content: center; gap: 4px;
  border: 2px dashed var(--teal); border-radius: var(--radius-lg);
  background: var(--teal-tint); color: var(--teal-dark);
  font-size: var(--text-md);
  pointer-events: none;
}

.visually-hidden {
  position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); white-space: nowrap;
}

/* ---- dialogs ---- */

/* dashboard.css fixes the modal at 480px; keep it inside the screen on phones. */
.modal { max-width: calc(100% - 32px); }
.move-picker {
  max-height: 320px; overflow-y: auto;
  margin-bottom: 16px; padding: 6px;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
}

/* ---- narrow screens: sidebar stacks above the list ---- */

@media (max-width: 720px) {
  .explorer { grid-template-columns: 1fr; }
  .explorer-sidebar {
    border-right: none; border-bottom: 1px solid var(--border);
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  }
  .col-modified { display: none; }
}
</style>
