<script setup>
import { computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import logoSrc from '@/assets/logo-mark.png'
import { auth, clearUser } from '@/stores/auth.js'
import { logout } from '@/apis.js'

const router = useRouter()

const NAV_ITEMS = {
  super_admin: [
    { label: 'National overview', to: '/super-admin/overview' },
    { label: 'Branch',            to: '/super-admin/branches' },
    { label: 'Participants',      to: '/super-admin/participants' },
    { label: 'Users',             to: '/super-admin/users' },
    { label: 'Reporting',         to: '/super-admin/reporting' },
    { label: 'Administration',    to: '/super-admin/administration' },
  ],
  branch_manager: [
    { label: 'Overview',     to: '/branch-manager/overview' },
    { label: 'Sessions',     to: '/branch-manager/sessions' },
    { label: 'Participants', to: '/branch-manager/participants' },
    { label: 'Instructors',  to: '/branch-manager/instructors' },
    { label: 'Feedback',     to: '/branch-manager/feedback' },
    { label: 'Reports',      to: '/branch-manager/reports' },
  ],
  instructor: [
    { label: 'Home',         to: '/instructor/home' },
    { label: 'Sessions',     to: '/instructor/sessions' },
    { label: 'Participants', to: '/instructor/participants' },
    { label: 'Feedback',     to: '/instructor/feedback' },
  ],
}

const ROLE_LABELS = {
  super_admin: 'Super Admin',
  branch_manager: 'Branch Manager',
  instructor: 'Instructor',
}

const navItems  = computed(() => NAV_ITEMS[auth.user?.role] ?? [])
const roleLabel = computed(() => ROLE_LABELS[auth.user?.role] ?? '')

// Super Admin works nationally; the other two are scoped to their branch.
const scope = computed(() =>
  auth.user?.role === 'super_admin'
    ? 'National'
    : `Branch: ${auth.user?.branch?.name ?? '—'}`
)

const userName = computed(() => {
  const u = auth.user
  if (!u) return ''
  return `${u.first_name ?? ''} ${u.last_name ?? ''}`.trim() || u.email
})

async function handleLogout() {
  try { await logout() } catch (e) {}
  clearUser()
  router.push('/login')
}
</script>

<template>
  <nav class="app-nav">
    <div class="nav-left">
      <img :src="logoSrc" class="nav-logo" alt="" />
      <span class="nav-brand">Taurite Tū</span>
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
      <button class="nav-btn" @click="handleLogout">Log out</button>
    </div>
  </nav>
</template>
