<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import logoSrc from '@/assets/logo.png'
 
const router = useRouter()
 
// Current tab — controls which page content is shown
const activeNav = ref('Administration')
const navItems = ['National overview', 'Kapa', 'Reporting', 'Users', 'Administration']
 
// Logged-in super admin info (placeholder — replace with API call later)
const adminName = ref('Anahera M.')
 
// ── Users page data ──────────────────────────────────────────────────────────
// Filter for the users table ('All', 'Branch Managers', 'Instructors', 'Super Admins', 'Pending')
const activeFilter = ref('All')
const filters = ['All', 'Branch Managers', 'Instructors', 'Super Admins', 'Pending']
 
// Hardcoded user list — replace with GET /api/users/ when backend is ready
const users = ref([
  { name: 'Materoa Ngātai',   role: 'Branch Manager', kapa: 'Ngā Hau e Whā', status: 'Active' },
  { name: 'Rāhera Tuhi',      role: 'Branch Manager', kapa: 'Te Puna Ora',    status: 'Active' },
  { name: 'Piripi Kereama',   role: 'Branch Manager', kapa: 'Te Rerenga',     status: 'Active' },
  { name: 'Wikitōria Paraone',role: 'Instructor',     kapa: 'Ngā Hau e Whā', status: 'Active' },
  { name: 'Ngaire Wharekura', role: 'Instructor',     kapa: 'Waiora Kapa',   status: 'Pending' },
  { name: 'Anahera Mihaka',   role: 'Super Admin',    kapa: null,             status: 'Active' },
])
 
// Filter users based on the active pill button
const filteredUsers = computed(() => {
  if (activeFilter.value === 'All') return users.value
  if (activeFilter.value === 'Pending') return users.value.filter(u => u.status === 'Pending')
  if (activeFilter.value === 'Branch Managers') return users.value.filter(u => u.role === 'Branch Manager')
  if (activeFilter.value === 'Instructors') return users.value.filter(u => u.role === 'Instructor')
  if (activeFilter.value === 'Super Admins') return users.value.filter(u => u.role === 'Super Admin')
  return users.value
})
</script>
 
<template>
  <div class="sa-dashboard">
 
    <!-- ── Navbar ─────────────────────────────────────────────────────────── -->
    <nav class="navbar">
      <div class="nav-left">
        <img :src="logoSrc" class="logo" alt="Taurite Tū logo" />
        <span class="brand">Taurite Tū</span>
        <span class="scope">National</span>
      </div>
      <div class="nav-links">
        <button
          v-for="item in navItems"
          :key="item"
          :class="['nav-link', { active: activeNav === item }]"
          @click="activeNav = item"
        >
          {{ item }}
        </button>
      </div>
      <div class="nav-right">{{ adminName }} · Super Admin</div>
    </nav>
 
    <!-- ════════════════════════════════════════════════════════════════════
         ADMINISTRATION TAB
    ════════════════════════════════════════════════════════════════════════ -->
    <main v-if="activeNav === 'Administration'" class="content">
      <h1>Administration</h1>
      <p class="page-subtitle">Low-frequency national settings and records.</p>
 
      <!-- Three action cards -->
      <div class="admin-cards">
        <div class="admin-card">
          <h3>Vocabularies</h3>
          <p>The shared absence reasons and physical-test measures every kapa selects from.</p>
          <a href="#">Open →</a>
        </div>
        <div class="admin-card">
          <h3>Audit log</h3>
          <p>Every write and cross-kapa read, append-only and enforced in the database.</p>
          <a href="#">Open →</a>
        </div>
        <div class="admin-card">
          <h3>Exports</h3>
          <p>De-identified research data, ready for external analysis.</p>
          <a href="#">Open →</a>
        </div>
      </div>
 
      <p class="demo-note">Demonstration data only. All names, kapa and quotes are fictional.</p>
    </main>
 
    <!-- ════════════════════════════════════════════════════════════════════
         USERS TAB
    ════════════════════════════════════════════════════════════════════════ -->
    <main v-else-if="activeNav === 'Users'" class="content">
      <div class="page-header">
        <h1>Users</h1>
        <!-- Add user button — will open a form/modal once that's built -->
        <button class="btn-primary">Add user</button>
      </div>
 
      <!-- Filter pills -->
      <div class="pills">
        <button
          v-for="f in filters"
          :key="f"
          :class="['pill', { active: activeFilter === f }]"
          @click="activeFilter = f"
        >
          {{ f }}
        </button>
      </div>
 
      <!-- Users table -->
      <table class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Role</th>
            <th>Kapa</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.name">
            <td>{{ user.name }}</td>
            <td><span :class="['role-badge', user.role.toLowerCase().replace(' ', '-')]">{{ user.role }}</span></td>
            <td>{{ user.kapa ?? '—' }}</td>
            <td><span :class="['status-badge', user.status.toLowerCase()]">{{ user.status }}</span></td>
            <td class="edit-cell"><a href="#">Edit</a></td>
          </tr>
        </tbody>
      </table>
 
      <p class="demo-note">Demonstration data only. All names, kapa and quotes are fictional.</p>
    </main>
 
    <!-- ════════════════════════════════════════════════════════════════════
         OTHER TABS (placeholder until those pages are built)
    ════════════════════════════════════════════════════════════════════════ -->
    <main v-else class="content">
      <div class="placeholder-page">
        <h2>{{ activeNav }}</h2>
        <p>This page is coming soon.</p>
      </div>
    </main>
 
  </div>
</template>
 
<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }
 
.sa-dashboard {
  min-height: 100vh;
  background: #f0ede6;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
 
/* Navbar */
.navbar {
  display: flex; align-items: center; justify-content: space-between;
  background: #1a1a1a; color: white; padding: 0 24px; height: 52px; gap: 16px;
}
.nav-left { display: flex; align-items: center; gap: 8px; }
.logo { height: 30px; width: auto; filter: brightness(0) invert(1); }
.brand { font-weight: 700; font-size: 15px; }
.scope { font-size: 12px; color: #4D9298; font-weight: 500; }
.nav-links { display: flex; gap: 4px; }
.nav-link {
  background: none; border: none; color: rgba(255,255,255,0.7);
  padding: 6px 14px; border-radius: 20px; font-size: 13px; cursor: pointer;
}
.nav-link:hover { color: white; }
.nav-link.active { background: #333; color: white; border-radius: 20px; }
.nav-right { font-size: 12px; opacity: 0.7; white-space: nowrap; }
 
/* Content */
.content { max-width: 1100px; margin: 0 auto; padding: 48px 24px; }
 
h1 { font-size: 28px; font-weight: 700; color: #1a1a1a; margin-bottom: 6px; }
.page-subtitle { font-size: 13px; color: #888; margin-bottom: 32px; }
 
/* Administration cards */
.admin-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 48px; }
.admin-card {
  background: white; border-radius: 10px; padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.admin-card h3 { font-size: 16px; font-weight: 700; margin-bottom: 10px; color: #1a1a1a; }
.admin-card p { font-size: 13px; color: #777; line-height: 1.5; margin-bottom: 16px; }
.admin-card a { font-size: 13px; font-weight: 600; color: #1a1a1a; text-decoration: none; }
.admin-card a:hover { text-decoration: underline; }
 
/* Users page */
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.btn-primary {
  background: #7a2e2e; color: white; border: none; border-radius: 6px;
  padding: 10px 18px; font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-primary:hover { background: #6a2424; }
 
/* Filter pills */
.pills { display: flex; gap: 8px; margin-bottom: 20px; }
.pill {
  padding: 6px 16px; border: 1.5px solid #ccc; border-radius: 20px;
  font-size: 13px; background: white; cursor: pointer; color: #444;
}
.pill:hover { border-color: #888; }
.pill.active { background: #1a1a1a; color: white; border-color: #1a1a1a; }
 
/* Table */
.data-table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }
.data-table th {
  text-align: left; padding: 12px 16px; font-size: 12px; font-weight: 600;
  color: #888; background: #f7f4ef; border-bottom: 1px solid #e8e2d8;
}
.data-table td { padding: 14px 16px; font-size: 13px; border-bottom: 1px solid #f0ede6; color: #333; }
.data-table tr:last-child td { border-bottom: none; }
 
/* Role badges */
.role-badge {
  display: inline-block; padding: 3px 10px; border-radius: 20px;
  font-size: 11px; font-weight: 500; background: #e8e2d8; color: #555;
}
 
/* Status badges */
.status-badge {
  display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600;
}
.status-badge.active  { background: #e6f4ec; color: #2a7a4a; }
.status-badge.pending { background: #e0f2f3; color: #2a7a7a; }
 
.edit-cell a { color: #7a2e2e; font-size: 13px; font-weight: 600; text-decoration: none; }
.edit-cell a:hover { text-decoration: underline; }
 
/* Demo note */
.demo-note { text-align: center; font-size: 12px; color: #aaa; margin-top: 48px; }
 
/* Placeholder */
.placeholder-page { text-align: center; padding: 80px; color: #aaa; }
.placeholder-page h2 { font-size: 20px; margin-bottom: 8px; color: #888; }
</style>
 
