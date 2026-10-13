<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import logoSrc from '@/assets/logo-mark.png'
import { auth, clearUser } from '@/stores/auth.js'
import { logout } from '@/apis.js'
import { initials } from '@/utils/sessions.js'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'

const router = useRouter()
const loggingOut = ref(false)
const logoutError = ref(null)

const NAV_ITEMS = {
  super_admin: [
    { label: 'National overview', to: '/super-admin/overview' },
    { label: 'Kapa',            to: '/super-admin/branches' },
    { label: 'Kaumātua',        to: '/super-admin/participants' },
    { label: 'Users',           to: '/super-admin/users' },
    { label: 'Feedback',        to: '/super-admin/feedback' },
    { label: 'Reporting',       to: '/super-admin/reporting' },
    { label: 'Documents',       to: '/documents' },
    { label: 'Administration',  to: '/super-admin/administration' },
    { label: 'Help',            to: '/help' },
  ],
  branch_manager: [
    { label: 'Overview',        to: '/branch-manager/overview' },
    { label: 'Sessions',        to: '/branch-manager/sessions' },
    { label: 'Kaumātua',        to: '/branch-manager/participants' },
    { label: 'Kaimahi',         to: '/branch-manager/instructors' },
    { label: 'Feedback',        to: '/branch-manager/feedback' },
    { label: 'Reports',         to: '/branch-manager/reports' },
    { label: 'Administration',  to: '/branch-manager/administration' },
    { label: 'Documents',       to: '/documents' },
    { label: 'Help',            to: '/help' },
  ],
  instructor: [
    { label: 'Home',            to: '/instructor/home' },
    { label: 'Sessions',        to: '/instructor/sessions' },
    { label: 'Kaumātua',        to: '/instructor/participants' },
    { label: 'Feedback',        to: '/instructor/feedback' },
    { label: 'Documents',       to: '/documents' },
    { label: 'Help',            to: '/help' },
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
    : (auth.user?.branch?.name || '—')
)

const userName = computed(() => {
  const u = auth.user
  if (!u) return ''
  return `${u.first_name ?? ''} ${u.last_name ?? ''}`.trim() || u.email
})

const shortName = computed(() => {
  const u = auth.user
  if (!u) return ''
  const full = `${u.first_name ?? ''} ${u.last_name ?? ''}`.trim()
  if (full) return full
  if (u.email) return u.email.split('@')[0]
  return 'User'
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
const handleScroll = () => {
  const nav = document.querySelector('.app-nav')
  if (nav) nav.classList.toggle('scrolled', window.scrollY > 10)
}
onMounted(() => window.addEventListener('scroll', handleScroll))
onUnmounted(() => window.removeEventListener('scroll', handleScroll))
</script>

<template>
  <nav class="app-nav">
    <div class="nav-left">
      <img :src="logoSrc" class="nav-logo" alt="Taurite Tū logo" />
      <RouterLink :to="navItems[0]?.to ?? '/'" class="nav-brand">Taurite Tū</RouterLink>
      <span class="nav-scope" :title="auth.user?.role === 'super_admin' ? 'National scope' : `Kapa: ${auth.user?.branch?.name ?? '—'}`">
        <span class="live-pulse-dot"></span>
        {{ scope }}
      </span>
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
      <ThemeSwitcher />
      <div class="nav-user-pill" :title="`${userName} (${roleLabel})`">
        <span class="user-avatar">{{ initials(userName) }}</span>
        <span class="nav-user">{{ shortName }}</span>
      </div>
      <span v-if="logoutError" class="logout-error" role="alert">{{ logoutError }}</span>
      <button class="nav-btn nav-btn--logout" :disabled="loggingOut" :title="loggingOut ? 'Logging out…' : 'Log out'" @click="handleLogout">
        <span class="logout-icon">⎋</span>
        <span class="logout-text">{{ loggingOut ? 'Logging out…' : 'Log out' }}</span>
      </button>
    </div>
  </nav>
</template>
