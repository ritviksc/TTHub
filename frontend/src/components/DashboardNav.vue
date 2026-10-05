<script setup>
import { computed, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import logoSrc from '@/assets/logo-mark.png'
import { auth, clearUser } from '@/stores/auth.js'
import { logout } from '@/apis.js'

const router = useRouter()
const loggingOut = ref(false)
const logoutError = ref(null)

const NAV_ITEMS = {
  super_admin: [
    { label: 'National overview', to: '/super-admin/overview' },
    { label: 'Kapa',            to: '/super-admin/branches' },
    { label: 'Kaumātua',      to: '/super-admin/participants' },
    { label: 'Users',             to: '/super-admin/users' },
    { label: 'Reporting',         to: '/super-admin/reporting' },
    { label: 'Documents',         to: '/documents' },
    { label: 'Administration',    to: '/super-admin/administration' },
  ],
  branch_manager: [
    { label: 'Overview',     to: '/branch-manager/overview' },
    { label: 'Sessions',     to: '/branch-manager/sessions' },
    { label: 'Kaumātua', to: '/branch-manager/participants' },
    { label: 'Kaimahi',  to: '/branch-manager/instructors' },
    { label: 'Feedback',     to: '/branch-manager/feedback' },
    { label: 'Reports',      to: '/branch-manager/reports' },
    { label: 'Administration', to: '/branch-manager/administration' },
    { label: 'Documents',    to: '/documents' },
  ],
  instructor: [
    { label: 'Home',         to: '/instructor/home' },
    { label: 'Sessions',     to: '/instructor/sessions' },
    { label: 'Kaumātua', to: '/instructor/participants' },
    { label: 'Feedback',     to: '/instructor/feedback' },
    { label: 'Documents',    to: '/documents' },
  ],
}

const ROLE_LABELS = {
  super_admin: 'Super Admin',
  branch_manager: 'Branch Manager',
  instructor: 'Kaimahi',
}

const navItems  = computed(() => NAV_ITEMS[auth.user?.role] ?? [])
const roleLabel = computed(() => ROLE_LABELS[auth.user?.role] ?? '')

// Super Admin works nationally; the other two are scoped to their branch.
const scope = computed(() =>
  auth.user?.role === 'super_admin'
    ? 'National'
    : `Kapa: ${auth.user?.branch?.name ?? '—'}`
)

const userName = computed(() => {
  const u = auth.user
  if (!u) return ''
  return `${u.first_name ?? ''} ${u.last_name ?? ''}`.trim() || u.email
})

async function handleLogout() {
  if (loggingOut.value) return
  loggingOut.value = true
  logoutError.value = null
  try {
    await logout()
    clearUser()
    await router.replace({ name: 'home' })
  } catch {
    logoutError.value = 'Could not log out. Please try again.'
  } finally {
    loggingOut.value = false
  }
}
</script>

<template>
  <nav class="app-nav">
    <div class="nav-left">
      <img :src="logoSrc" class="nav-logo" alt="" />
<RouterLink :to="navItems[0]?.to ?? '/'" class="nav-brand">Taurite Tū</RouterLink>
 <span class="nav-scope">{{ scope }}</span>
    </div>

    <div class="nav-links">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-link"
      >
        {{ item.label }}
      </RouterLink>
    </div>

    <div class="nav-right">
      <span class="nav-user">{{ userName }} · {{ roleLabel }}</span>
      <span v-if="logoutError" role="alert">{{ logoutError }}</span>
      <button class="nav-btn" :disabled="loggingOut" @click="handleLogout">{{ loggingOut ? 'Logging out…' : 'Log out' }}</button>
    </div>
  </nav>
</template>
