import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, computed, reactive, createSSRApp, compile } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { parse, compileScript } from '@vue/compiler-sfc'
import { routeAccess } from '../src/router/access.js'
import { ATTENDANCE_STATUSES, ABSENCE_REASONS, countByStatus, formatSessionDate, initials } from '../src/utils/sessions.js'

const { descriptor } = parse(readFileSync(new URL('../src/views/Instructor/SessionDetail.vue', import.meta.url), 'utf8'))
const compiled = compileScript(descriptor, { id: 'session-attendance-access-test' }).content
  .replace(/^import[\s\S]*?from ['"][^'"]+['"];?$/gm, '').replace('export default', 'const component =')

for (const [role, prefix] of [['instructor', 'in'], ['branch_manager', 'bm']]) {
  test(`${role} can enter attendance mode and sees each absence reason once`, async () => {
    const context = vm.createContext({
      ref, computed, onMounted() {}, RouterLink: {}, ATTENDANCE_STATUSES, ABSENCE_REASONS,
      countByStatus, formatSessionDate, initials, auth: reactive({ user: { role } }),
      useRoute: () => ({ params: { id: 'session' } }), useRouter: () => ({ push() {} }),
      getSession: async () => ({}), updateAttendance: async () => ({}), deleteSession: async () => {},
    })
    vm.runInContext(compiled + '\nthis.component = component', context)
    const page = context.component.setup({}, { expose() {} })
    assert.equal(page.canRecordAttendance.value, true)
    assert.equal(page.attendanceModeRoute.value.name, `${prefix}-attendance-mode`)
    assert.equal(page.attendanceModeRoute.value.params.id, 'session')
    assert.equal(page.listRouteName.value, `${prefix}-sessions`)
    assert.equal(page.attendanceModeRoute.value.query.review, undefined)
    page.session.value = { attendance_finalised: true }
    assert.equal(page.attendanceModeRoute.value.query.review, '1')
    const record = { id: 'record', participant_id: 'person', name: 'Example', status: 'absent', absence_reason: 'transport_issue', absence_reason_other: '' }
    page.loading.value = false
    page.session.value = { attendance_finalised: true, activity: 'Class', date: '2026-10-13', time: '09:00', attendance: [record] }
    for (const finalised of [true, false]) {
      page.session.value.attendance_finalised = finalised
      const app = createSSRApp({ setup: () => ({ ...page }), render: compile(descriptor.template.content) })
      app.component('RouterLink', { render: () => null })
      const html = await renderToString(app)
      assert.equal(html.split('Transport issue').length - 1, 1)
      assert.ok(html.includes('Status for Example'))
      assert.ok(html.includes('Absence reason for Example'))
      assert.equal(html.includes('class="not-applicable"'), false)
    }
  })
}

test('actual attendance routes restrict each role to its own pages', () => {
  const context = vm.createContext({
    createWebHistory() {}, createRouter: options => ({ ...options, beforeEach() {} }),
    LandingPage: {}, Login: {}, AboutUs: {}, ContactUs: {}, ComingSoon: {}, CreateStaff: {}, UserDetail: {}, StaffDetail: {},
    loadUser() {}, createAccessGuard() {},
  })
  const source = readFileSync(new URL('../src/router/index.js', import.meta.url), 'utf8')
    .replace(/^import .*$/gm, '').replace('export default router', 'this.router = router')
  vm.runInContext(source, context)
  for (const [role, prefix, path] of [['branch_manager', 'bm', 'branch-manager'], ['instructor', 'in', 'instructor']]) {
    const route = context.router.routes.find(route => route.name === `${prefix}-attendance-mode`)
    assert.equal(route.path, `/${path}/sessions/:id/attendance`)
    assert.equal(route.meta.requiresAuth, true)
    for (const viewer of ['branch_manager', 'instructor', 'super_admin']) {
      const result = routeAccess(route, { role: viewer })
      if (viewer === role) assert.equal(result, true)
      else assert.equal(result.name, 'not-authorised')
    }
    assert.equal(routeAccess(route, null).name, 'home')
  }
})
