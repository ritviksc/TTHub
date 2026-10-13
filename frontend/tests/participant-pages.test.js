import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, createSSRApp, compile, h } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { parse, compileScript } from '@vue/compiler-sfc'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createAccessGuard } from '../src/router/access.js'
import { initials, programmeToday } from '../src/utils/sessions.js'

test('branch manager participant links and bookmarks navigate between protected details and attendance pages', async () => {
  const context = vm.createContext({
    createWebHistory() {}, createRouter: options => ({ ...options, beforeEach() {} }),
    LandingPage: {}, Login: {}, AboutUs: {}, ContactUs: {}, ComingSoon: {}, CreateStaff: {}, UserDetail: {}, StaffDetail: {},
    loadUser() {}, createAccessGuard() {},
  })
  const source = readFileSync(new URL('../src/router/index.js', import.meta.url), 'utf8')
    .replace(/^import .*$/gm, '').replace('export default router', 'this.router = router')
  vm.runInContext(source, context)
  const router = createRouter({ history: createMemoryHistory(),
    routes: context.router.routes.map(route => ({ ...route, component: { render: () => null } })),
  })
  router.beforeEach(createAccessGuard(async () => ({ role: 'branch_manager' })))
  await router.push('/participants/person')
  assert.equal(router.currentRoute.value.name, 'bm-participant-detail')
  assert.equal(router.currentRoute.value.params.id, 'person')
  await router.push({ name: 'bm-participant-attendance', params: { id: 'person' } })
  assert.equal(router.currentRoute.value.path, '/branch-manager/participants/person/attendance')
  await router.push({ name: 'bm-participant-detail', params: { id: 'person' } })
  assert.equal(router.currentRoute.value.path, '/branch-manager/participants/person')
  await router.push({ name: 'sa-participant-attendance', params: { id: 'person' } })
  assert.equal(router.currentRoute.value.name, 'not-authorised')
})

test('branch manager pages render both navigation buttons and separate details from attendance', async () => {
  const { descriptor } = parse(readFileSync(new URL('../src/components/participants/ParticipantDetail.vue', import.meta.url), 'utf8'))
  const compiled = compileScript(descriptor, { id: 'participant-pages-test' }).content
    .replace(/^import .*$/gm, '').replace('export default', 'const component =')
  for (const page of ['details', 'attendance']) {
    const mounted = []
    const props = { participantId: 'person', page, routePrefix: 'bm', canRecordGpConsent: page === 'details' }
    const context = vm.createContext({
      ref, onMounted: callback => mounted.push(callback), RouterLink: {}, initials, programmeToday,
      ParticipantAttendance: {}, AssessmentHistory: {}, DocumentList: {},
      getParticipant: async id => {
        assert.equal(id, props.participantId)
        return { id, full_name: 'Aroha Example', first_name: 'Aroha', last_name: 'Example',
          branch_name: 'Our branch', is_active: true, gp_consent_given: false, photo_consent_given: false }
      },
      updateParticipant() {}, deactivateParticipant() {}, reactivateParticipant() {}, downloadGpDocument() {},
    })
    vm.runInContext(compiled + '\nthis.component = component', context)
    const state = context.component.setup(props, { expose() {} })
    for (const callback of mounted) await callback()
    const app = createSSRApp({ props: Object.keys(props), setup: () => ({ ...state }), render: compile(descriptor.template.content) }, props)
    app.component('RouterLink', { props: ['to'], setup: (props, { slots }) => () => h('a', { href: `#${props.to.name}/${props.to.params.id}` }, slots.default()) })
    app.component('ParticipantAttendance', { render: () => h('section', 'Attendance records') })
    app.component('AssessmentHistory', { render: () => h('section', 'Physical assessments') })
    app.component('DocumentList', { render: () => h('section', 'Participant files') })
    const html = await renderToString(app)
    assert.ok(html.includes('#bm-participant-detail/person'))
    assert.ok(html.includes('#bm-participant-attendance/person'))
    assert.ok(html.includes('>Details</a>'))
    assert.ok(html.includes('>Attendance history</a>'))
    assert.equal(html.includes('Save participant'), page === 'details')
    assert.equal(html.includes('Physical assessments'), page === 'details')
    assert.equal(html.includes('Participant files'), page === 'details')
    assert.equal(html.includes('Attendance records'), page === 'attendance')
  }
})
