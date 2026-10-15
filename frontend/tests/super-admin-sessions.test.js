import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, computed, reactive, createSSRApp, compile, h } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { parse, compileScript } from '@vue/compiler-sfc'
import { routeAccess } from '../src/router/access.js'
import { NAV } from '../src/utils/nav.js'
import * as sessionUtils from '../src/utils/sessions.js'
import * as calendarUtils from '../src/utils/calendar.js'

function setup(file, context, props = {}) {
  const { descriptor } = parse(readFileSync(new URL(`../src/${file}`, import.meta.url), 'utf8'))
  const compiled = compileScript(descriptor, { id: 'national-sessions-test' }).content
    .replace(/^import[\s\S]*?from ['"][^'"]+['"];?$/gm, '').replace('export default', 'const component =')
  vm.runInContext(compiled + '\nthis.component = component', context)
  const page = context.component.setup(props, { expose() {}, emit() {} })
  return { page, descriptor }
}

const branches = [{ id: 'a', name: 'Harbour' }, { id: 'b', name: 'Hills' }, { id: 'c', name: 'Empty branch' }]
const sessions = [
  { id: 'a-now', branch: 'a', branch_name: 'Harbour', activity: 'Movement', date: sessionUtils.programmeToday(), time: '09:00', present_count: 1, roster_count: 2 },
  { id: 'a-old', branch: 'a', branch_name: 'Harbour', activity: 'Old class', date: '2000-01-01', time: '10:00', present_count: 2, roster_count: 2 },
  { id: 'b-now', branch: 'b', branch_name: 'Hills', activity: 'Balance', date: sessionUtils.programmeToday(), time: '09:00', present_count: 0, roster_count: 2 },
]

async function mount(role = 'super_admin') {
  const control = { fail: '', branchReads: 0, destinations: [] }
  const context = vm.createContext({
    ref, computed, onMounted() {}, RouterLink: {}, CreateSessionModal: {}, SessionCalendar: {}, ...sessionUtils,
    auth: reactive({ user: { role } }),
    useRouter: () => ({ push: route => control.destinations.push(route) }),
    listSessions: async () => {
      if (control.fail === 'sessions') throw Error('Offline')
      return role === 'super_admin' ? sessions : sessions.filter(session => session.branch === 'a')
    },
    listBranches: async () => {
      control.branchReads++
      if (control.fail === 'branches') throw Error('Offline')
      return branches
    },
  })
  const { page, descriptor } = setup('views/Instructor/Sessions.vue', context)
  await page.load()
  const render = async () => {
    const app = createSSRApp({ setup: () => ({ ...page }), render: compile(descriptor.template.content) })
    app.component('CreateSessionModal', { props: ['initialBranch'], setup: props => () => h('div', { 'data-initial-branch': props.initialBranch }) })
    app.component('RouterLink', { props: ['to'], setup: (props, { slots }) => () => h('a', { href: `#${props.to.name}/${props.to.params.id}` }, slots.default()) })
    app.component('SessionCalendar', { props: ['sessions', 'showBranch', 'canCreate'],
      setup: props => () => h('div', { 'data-calendar': props.sessions.map(session => session.id).join(','),
        'data-show-branch': props.showBranch, 'data-can-create': props.canCreate }) })
    return renderToString(app)
  }
  return { page, control, render }
}

test('national branch filtering reaches both calendar and list, and combines with period filtering', async () => {
  const { page, control, render } = await mount()
  assert.equal(control.branchReads, 1)
  assert.equal(page.canCreate.value, true)
  assert.equal(page.branchSessions.value.length, 3)
  assert.match(await render(), /All branches/)
  page.branchFilter.value = 'a'
  page.openCreateModal()
  assert.match(await render(), /data-initial-branch="a"/)
  page.showCreate.value = false
  let html = await render()
  assert.match(html, /data-calendar="a-now,a-old"/)
  assert.match(html, /data-show-branch="true"/)
  assert.match(html, /data-can-create="true"/)
  assert.equal(html.includes('New session'), true)
  page.viewMode.value = 'list'
  page.period.value = 'This month'
  html = await render()
  assert.match(html, /<th>Branch<\/th>/)
  assert.match(html, /Harbour<\/td>/)
  assert.match(html, /#sa-session-detail\/a-now/)
  assert.equal(html.includes('#sa-session-detail/a-old'), false)
  assert.equal(html.includes('#sa-session-detail/b-now'), false)
  page.branchFilter.value = 'c'
  html = await render()
  assert.match(html, /No sessions yet/)
  assert.equal(html.includes('Create your first session'), false)
  page.branchFilter.value = ''
  page.period.value = 'All'
  assert.equal(page.visibleSessions.value.length, 3)
  page.openSession('b-now')
  assert.equal(control.destinations[0].name, 'sa-session-detail')
})

test('failed national reads show an error and retry instead of empty results', async () => {
  for (const read of ['sessions', 'branches']) {
    const { page, control, render } = await mount()
    control.fail = read
    await page.load()
    const html = await render()
    assert.match(html, /Could not load sessions/)
    assert.match(html, /Retry/)
    assert.equal(page.canCreate.value, false)
    page.openCreateModal()
    assert.equal(page.showCreate.value, false)
    assert.equal(html.includes('data-calendar'), false)
    assert.equal(html.includes('No sessions yet'), false)
    control.fail = ''
    await page.load()
    assert.equal(page.loadError.value, null)
    assert.equal(page.branchSessions.value.length, 3)
  }
})

test('branch staff keep their existing scoped session pages without fetching national branches', async () => {
  for (const [role, prefix] of [['branch_manager', 'bm'], ['instructor', 'in']]) {
    const { page, control, render } = await mount(role)
    assert.equal(control.branchReads, 0)
    assert.equal(page.canCreate.value, true)
    assert.equal(page.branchSessions.value.length, 2)
    assert.equal((await render()).includes('session-branch-filter'), false)
    assert.equal(page.sessionRoute('a-now').name, `${prefix}-session-detail`)
  }
})

test('national session details expose attendance and review with finalisation locks and no delete action', async () => {
  const context = vm.createContext({
    ref, computed, onMounted() {}, RouterLink: {}, ...sessionUtils,
    auth: { user: { role: 'super_admin' } },
    useRoute: () => ({ params: { id: 'b-now' } }), useRouter: () => ({ push() {} }),
    getSession() {}, updateAttendance() {}, deleteSession() {},
  })
  const { page, descriptor } = setup('views/Instructor/SessionDetail.vue', context)
  page.loading.value = false
  page.session.value = { ...sessions[2], attendance_finalised: false, attendance: [
    { id: 'r1', participant_id: 'p1', name: 'Participant One', status: 'absent', absence_reason: 'transport_issue' },
    { id: 'r2', participant_id: 'p2', name: 'Participant Two', status: 'absent', absence_reason: 'other', absence_reason_other: 'Family commitment' },
  ] }
  assert.equal(page.canRecordAttendance.value, true)
  assert.equal(page.listRouteName.value, 'sa-sessions')
  assert.equal(page.attendanceModeRoute.value.name, 'sa-attendance-mode')
  for (const finalised of [false, true]) {
    page.session.value.attendance_finalised = finalised
    const app = createSSRApp({ setup: () => ({ ...page }), render: compile(descriptor.template.content) })
    app.component('RouterLink', { render: () => null })
    const html = await renderToString(app)
    assert.match(html, /Hills/)
    assert.match(html, /Transport issue/)
    assert.match(html, /Family commitment/)
    assert.equal(html.includes('Review attendance'), finalised)
    assert.equal(html.includes('Attendance mode'), !finalised)
    assert.equal(html.includes('Delete session'), false)
    assert.equal(html.includes('<select disabled'), finalised)
    assert.equal(page.attendanceModeRoute.value.query.review, finalised ? '1' : undefined)
  }
})

test('national calendar identifies branches and offers no creation controls', async () => {
  const props = { sessions, canCreate: false, showBranch: true }
  const context = vm.createContext({ ref, computed, ...calendarUtils, ...sessionUtils })
  const { page, descriptor } = setup('components/sessions/SessionCalendar.vue', context, props)
  const html = await renderToString(createSSRApp({ setup: () => ({ ...page, ...props }), render: compile(descriptor.template.content) }))
  assert.match(html, /Harbour · Movement/)
  assert.match(html, /Hills · Balance/)
  assert.match(html, /class="card-branch">Harbour/)
  assert.equal(html.includes('btn-quick-add'), false)
  assert.equal(html.includes('Add session'), false)
})

test('empty calendar days offer one blue agenda create button without the duplicate gray button', async () => {
  const props = { sessions: [], canCreate: true, showBranch: false }
  const context = vm.createContext({ ref, computed, ...calendarUtils, ...sessionUtils })
  const { page, descriptor } = setup('components/sessions/SessionCalendar.vue', context, props)
  const html = await renderToString(createSSRApp({ setup: () => ({ ...page, ...props }), render: compile(descriptor.template.content) }))
  assert.equal(html.includes('Add session for this day'), false)
  assert.equal(html.split('btn-add-day').length - 1, 1)
  assert.match(html, /No sessions scheduled/)
})

test('national session routes and navigation are restricted to Super Admins', () => {
  const context = vm.createContext({
    createWebHistory() {}, createRouter: options => ({ ...options, beforeEach() {} }),
    LandingPage: {}, Login: {}, AboutUs: {}, ContactUs: {}, ComingSoon: {}, CreateStaff: {}, UserDetail: {}, StaffDetail: {},
    loadUser() {}, createAccessGuard() {},
  })
  const source = readFileSync(new URL('../src/router/index.js', import.meta.url), 'utf8')
    .replace(/^import .*$/gm, '').replace('export default router', 'this.router = router')
  vm.runInContext(source, context)
  for (const name of ['sa-sessions', 'sa-session-detail']) {
    const route = context.router.routes.find(route => route.name === name)
    assert.ok(route)
    assert.equal(routeAccess(route, { role: 'super_admin' }), true)
    for (const role of ['branch_manager', 'instructor']) assert.equal(routeAccess(route, { role }).name, 'not-authorised')
    assert.equal(routeAccess(route, null).name, 'home')
  }
  assert.ok(NAV.super_admin.links.some(link => link.label === 'Sessions' && link.to === '/super-admin/sessions'))
})
