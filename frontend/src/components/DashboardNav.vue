<script setup>
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import logoSrc from '@/assets/logo.png'
import { auth, ui, clearUser } from '@/stores/auth.js'
import { logout } from '@/apis.js'

const router = useRouter()

const NAV_ITEMS = {
  super_admin:    ['National overview', 'Kapa', 'Reporting', 'Users', 'Administration'],
  branch_manager: ['Overview', 'Sessions', 'Participants', 'Instructors', 'Feedback', 'Reports'],
  instructor:     ['Home', 'Sessions', 'Participants', 'Feedback'],
}

const ROLE_LABELS = {
  super_admin: 'Super Admin',
  branch_manager: 'Branch Manager',
  instructor: 'Instructor',
}

const navItems  = computed(() => NAV_ITEMS[auth.user?.role] ?? [])
const roleLabel = computed(() => ROLE_LABELS[auth.user?.role] ?? '')

// Super Admin works nationally; the other two are scoped to their kapa.
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

// Keep the active tab valid when the signed-in user changes.
watch(navItems, (items) => {
  if (!items.includes(ui.activeNav)) ui.activeNav = items[0] ?? ''
}, { immediate: true })

async function handleLogout() {
  try { await logout() } catch (e) {}
  clearUser()
  router.push('/login')
}
</script>

<template>
  <nav class="navbar">
    <div class="nav-left">
      <img :src="logoSrc" class="logo" alt="Taurite Tū logo" />
      <span class="brand">Taurite Tū</span>
      <span class="scope">{{ scope }}</span>
    </div>

    <div class="nav-links">
      <button
        v-for="item in navItems"
        :key="item"
        :class="['nav-link', { active: ui.activeNav === item }]"
        @click="ui.activeNav = item"
      >
        {{ item }}
      </button>
    </div>

    <div class="nav-right">
      <span>{{ userName }} · {{ roleLabel }}</span>
      <button class="logout-btn" @click="handleLogout">Log out</button>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  display: flex; align-items: center; justify-content: space-between;
  background: #1a1a1a; color: white; padding: 0 24px; height: 52px; gap: 16px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.nav-left { display: flex; align-items: center; gap: 8px; }
.logo { height: 30px; width: auto; }
.brand { font-weight: 700; font-size: 15px; }
.scope { font-size: 12px; color: #4D9298; font-weight: 500; }

.nav-links { display: flex; gap: 4px; }
.nav-link {
  background: none; border: none; color: rgba(255,255,255,0.7);
  padding: 6px 14px; border-radius: 20px; font-size: 13px; cursor: pointer;
}
.nav-link:hover { color: white; background: none; }
.nav-link.active { background: #333; color: white; }

.nav-right {
  display: flex; align-items: center; gap: 12px;
  font-size: 12px; opacity: 0.85; white-space: nowrap;
}
.logout-btn {
  background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3);
  color: white; border-radius: 6px; padding: 4px 12px; font-size: 12px; cursor: pointer;
}
.logout-btn:hover { background: rgba(255,255,255,0.25); }
</style>
