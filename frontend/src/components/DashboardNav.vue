<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import logoSrc from '@/assets/logo-mark.png'
import { auth, clearUser } from '@/stores/auth.js'
import { logout } from '@/apis.js'
import { initials } from '@/utils/sessions.js'
import { NAV, ADMIN_LABEL, HELP_LINK, ROLE_LABELS, isUnder } from '@/utils/nav.js'
import { THEMES, currentTheme } from '@/utils/theme.js'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import NavMenu from '@/components/NavMenu.vue'

const router = useRouter()
const route = useRoute()
const loggingOut = ref(false)
const logoutError = ref(null)
const mobileOpen = ref(false)
const themeOpen = ref(false)

const activeTheme = computed(() => THEMES.find(t => t.id === currentTheme.value) ?? THEMES[0])

const navItems  = computed(() => NAV[auth.user?.role]?.links ?? [])
const adminMenu = computed(() => NAV[auth.user?.role]?.admin ?? null)
const roleLabel = computed(() => ROLE_LABELS[auth.user?.role] ?? '')

// Administration stays highlighted on the pages it links to, e.g. Users.
const adminActive = computed(() => {
  const admin = adminMenu.value
  if (!admin || !route?.path) return false
  return [admin.to, ...admin.children.map(item => item.to)].some(to => isUnder(route.path, to))
})

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

watch(() => route?.fullPath, () => { mobileOpen.value = false })

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

    <div class="nav-links nav-links--collapsible">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-link"
      >
        {{ item.label }}
      </RouterLink>
      <RouterLink
        v-if="adminMenu"
        :to="adminMenu.to"
        :class="['nav-link', { 'nav-link--active': adminActive }]"
      >
        {{ ADMIN_LABEL }}
      </RouterLink>
    </div>

    <div class="nav-right">
      <RouterLink :to="HELP_LINK.to" class="nav-icon-btn nav-help">{{ HELP_LINK.label }}</RouterLink>

      <NavMenu
        :aria-label="`Account: ${userName}`"
        align="right"
        trigger-class="nav-user-pill"
        hover
      >
        <template #trigger>
          <span class="user-avatar">{{ initials(userName) }}</span>
          <span class="nav-user">{{ shortName }}</span>
        </template>
        <div class="nav-account">
          <span class="nav-account__name">{{ userName }}</span>
          <span class="nav-account__meta">{{ roleLabel }} · {{ scope }}</span>
        </div>
        <span v-if="logoutError" class="logout-error" role="alert">{{ logoutError }}</span>
        <button
          type="button"
          class="nav-menu__item nav-menu__item--logout"
          role="menuitem"
          :disabled="loggingOut"
          @click="handleLogout"
        >
          <span class="logout-icon">⎋</span>
          {{ loggingOut ? 'Logging out…' : 'Log out' }}
        </button>
        <div class="nav-submenu" @pointerenter="themeOpen = true" @pointerleave="themeOpen = false">
          <button
            type="button"
            class="nav-menu__item nav-submenu__trigger"
            role="menuitem"
            aria-haspopup="menu"
            :aria-expanded="themeOpen"
            @click.stop="themeOpen = !themeOpen"
          >
            <span class="nav-submenu__swatch" :style="{ backgroundColor: activeTheme.color }"></span>
            Theme
            <span class="nav-submenu__value">{{ activeTheme.name }}</span>
            <span class="nav-submenu__arrow" aria-hidden="true">‹</span>
          </button>
          <div v-if="themeOpen" class="nav-menu__panel nav-submenu__panel" role="menu">
            <ThemeSwitcher variant="list" />
          </div>
        </div>
      </NavMenu>

      <button
        type="button"
        class="nav-icon-btn nav-hamburger"
        :aria-expanded="mobileOpen"
        aria-controls="nav-mobile-panel"
        aria-label="Menu"
        @click="mobileOpen = !mobileOpen"
      >
        {{ mobileOpen ? '✕' : '☰' }}
      </button>
    </div>

    <div v-if="mobileOpen" id="nav-mobile-panel" class="nav-mobile">
      <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="nav-menu__item">
        {{ item.label }}
      </RouterLink>
      <RouterLink v-if="adminMenu" :to="adminMenu.to" class="nav-menu__item">{{ ADMIN_LABEL }}</RouterLink>
    </div>
  </nav>
</template>
