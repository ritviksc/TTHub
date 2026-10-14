import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { routeAccess } from '../src/router/access.js'
import { NAV, ADMIN_LABEL, HELP_LINK, isUnder } from '../src/utils/nav.js'

function loadRoutes() {
  const context = vm.createContext({
    createWebHistory() {}, createRouter: options => ({ ...options, beforeEach() {} }),
    LandingPage: {}, Login: {}, AboutUs: {}, ContactUs: {}, ComingSoon: {}, CreateStaff: {}, UserDetail: {}, StaffDetail: {},
    loadUser() {}, createAccessGuard() {},
  })
  const source = readFileSync(new URL('../src/router/index.js', import.meta.url), 'utf8')
    .replace(/^import .*$/gm, '').replace('export default router', 'this.router = router')
  vm.runInContext(source, context)
  return context.router.routes
}

const routes = loadRoutes()
const roles = ['super_admin', 'branch_manager', 'instructor']

function linksFor(role) {
  const { links, admin } = NAV[role]
  return [...links, ...(admin ? [{ label: ADMIN_LABEL, to: admin.to }, ...admin.children] : []), HELP_LINK]
}

for (const role of roles) {
  test(`${role} navigation only links to real pages that ${role} can open`, () => {
    for (const { label, to } of linksFor(role)) {
      const route = routes.find(route => route.path === to && route.component)
      assert.ok(route, `${label} (${to}) has no matching route`)
      assert.equal(routeAccess(route, { role }), true, `${role} cannot open ${to}`)
    }
    assert.ok(linksFor(role).some(item => item.to === '/documents'), `${role} has no way to reach Documents`)
  })
}

test('main rows stay short and only staff roles get an admin menu', () => {
  for (const role of roles) assert.ok(NAV[role].links.length <= 5)
  assert.ok(NAV.super_admin.admin && NAV.branch_manager.admin)
  assert.equal(NAV.instructor.admin, undefined)
  assert.ok(NAV.super_admin.admin.children.some(item => item.to === '/super-admin/users'))
  assert.ok(NAV.branch_manager.admin.children.some(item => item.to === '/branch-manager/instructors'))
})

test('both roles use the same label for reports', () => {
  for (const role of ['super_admin', 'branch_manager']) {
    assert.ok(NAV[role].links.some(item => item.label === 'Reports'))
  }
})

test('pages beneath a menu entry count as inside it', () => {
  assert.ok(isUnder('/super-admin/users/42', '/super-admin/users'))
  assert.ok(isUnder('/super-admin/administration/audit', '/super-admin/administration'))
  assert.ok(isUnder('/super-admin/users', '/super-admin/users'))
  assert.ok(!isUnder('/super-admin/users-archive', '/super-admin/users'))
})

test('the admin label is read from one constant', () => {
  const sources = ['../src/components/DashboardNav.vue', '../src/views/SuperAdmin/Administration.vue', '../src/views/BranchManager/Administration.vue']
    .map(path => readFileSync(new URL(path, import.meta.url), 'utf8'))
  for (const source of sources) {
    assert.ok(source.includes('ADMIN_LABEL'))
    assert.ok(!/>\s*Administration\s*</.test(source))
  }
})
