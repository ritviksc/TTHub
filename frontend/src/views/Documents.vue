<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { auth } from '@/stores/auth.js'
import { listBranches } from '@/apis.js'
import FileExplorer from '@/components/documents/FileExplorer.vue'

const isSuperAdmin = computed(() => auth.user?.role === 'super_admin')

// Super Admin sees every branch; everyone else sees only their own.
const branches = ref([])
// Wait for the branch list before opening the explorer, so a branch named in
// the URL is opened directly rather than after a detour via Organisation.
const ready = ref(!isSuperAdmin.value)

onMounted(async () => {
  if (!isSuperAdmin.value) return
  try {
    branches.value = await listBranches()
  } catch {
    branches.value = []
  } finally {
    ready.value = true
  }
})

// The sidebar's top-level locations. Anyone can read the organisation area,
// but only a Super Admin uploads to or organises it. In a branch, all staff
// can upload and a Branch Manager (or Super Admin) can organise.
const scopes = computed(() => {
  const list = [{
    key: 'organisation', label: 'Organisation', branchId: null,
    canUpload: isSuperAdmin.value, canManage: isSuperAdmin.value,
  }]
  if (isSuperAdmin.value) {
    for (const b of branches.value) {
      list.push({ key: b.id, label: b.name, region: b.region, branchId: b.id, canUpload: true, canManage: true })
    }
  } else if (auth.user?.branch) {
    const b = auth.user.branch
    list.push({
      key: b.id, label: b.name, region: b.region, branchId: b.id,
      canUpload: true, canManage: auth.user.role === 'branch_manager',
    })
  }
  return list
})

// Open the branch named in the URL (so refresh, and links shared between staff,
// land in the same place); otherwise staff start in their own branch.
const route = useRoute()
const router = useRouter()
const initialKey = route.query.branch ?? auth.user?.branch?.id ?? 'organisation'

function syncUrl(key) {
  const query = key === 'organisation' ? {} : { branch: key }
  if (route.query.branch !== query.branch) router.replace({ query })
}
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <h1>Documents</h1>
      <p class="page-subtitle">Organisation-wide files, and files for each branch.</p>
      <FileExplorer v-if="ready" :scopes="scopes" :initial-key="initialKey" @scope-change="syncUrl" />
      <p v-else class="loading-note">Loading…</p>
    </main>
  </div>
</template>
