import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, computed, createSSRApp, compile, h } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { parse, compileScript } from '@vue/compiler-sfc'
import { initials, programmeToday } from '../src/utils/sessions.js'

const screens = [
  ['components/participants/ParticipantDetail.vue', 'participant', 'changeStatus', false],
  ['views/StaffDetail.vue', 'staff', 'handleToggleActive', false],
  ['views/SuperAdmin/UserDetail.vue', 'user', 'handleToggleActive', false],
  ['views/SuperAdmin/Users.vue', 'users', 'handleToggleActive', true],
  ['views/BranchManager/Instructors.vue', 'instructors', 'handleToggleActive', true],
]

function mount([file, recordKey, handler, list]) {
  const { descriptor } = parse(readFileSync(new URL(`../src/${file}`, import.meta.url), 'utf8'))
  const compiled = compileScript(descriptor, { id: 'reactivation-test' }).content
    .replace(/^import[\s\S]*?from\s+['"][^'"]+['"];?\s*$/gm, '')
    .replace('export default', 'const component =')
  const calls = [], alerts = []
  const control = { confirmed: true, write: async active => ({ is_active: active }) }
  const write = active => async id => { calls.push({ id, active }); return control.write(active) }
  const context = vm.createContext({
    ref, computed, onMounted() {}, initials, programmeToday,
    RouterLink: {}, ParticipantAttendance: {}, AssessmentHistory: {}, DocumentList: {},
    auth: { user: { role: 'super_admin', branch: null } },
    useRoute: () => ({ params: { id: 'record' } }), useRouter: () => ({ push() {} }),
    confirm: () => control.confirmed, alert: message => alerts.push(message),
    listStaff() {}, listBranches() {}, getStaff() {}, updateStaff() {}, createStaffAccount() {}, listSessions() {},
    getParticipant() {}, updateParticipant() {}, downloadGpDocument() {},
    deactivateStaff: write(false), reactivateStaff: write(true),
    deactivateParticipant: write(false), reactivateParticipant: write(true),
  })
  vm.runInContext(compiled + '\nthis.component = component', context)
  const props = { participantId: 'record', page: 'details', routePrefix: 'sa', canRecordGpConsent: true }
  const page = context.component.setup(props, { expose() {} })
  const record = { id: 'record', is_active: false, first_name: 'Aroha', last_name: 'Example',
    full_name: 'Aroha Example', email: 'staff@example.nz', role: 'instructor', branch_name: 'Harbour' }
  page[recordKey].value = list ? [record] : record
  page.loading.value = false
  const toggle = () => page[handler](...(list ? [page[recordKey].value[0]] : []))
  const current = () => list ? page[recordKey].value[0] : page[recordKey].value
  const error = () => page.error?.value || page.actionError?.value || page.saveError?.value || alerts[0]
  const render = async () => {
    const app = createSSRApp({ setup: () => ({ ...page, ...props }), render: compile(descriptor.template.content) })
    for (const name of ['RouterLink', 'ParticipantAttendance', 'AssessmentHistory', 'DocumentList']) {
      app.component(name, { setup: (_, { slots }) => () => h('span', slots.default?.()) })
    }
    return renderToString(app)
  }
  return { page, calls, control, toggle, current, error, render }
}

for (const screen of screens) {
  test(`${screen[0]} offers reactivation and updates status only after a successful response`, async () => {
    const state = mount(screen)
    assert.match(await state.render(), /Reactivate/)
    await state.toggle()
    assert.deepEqual(state.calls, [{ id: 'record', active: true }])
    assert.equal(state.current().is_active, true)
    assert.match(await state.render(), /Deactivate/)
    await state.toggle()
    assert.deepEqual(state.calls[1], { id: 'record', active: false })
    assert.equal(state.current().is_active, false)
  })

  test(`${screen[0]} prevents duplicate requests and preserves inactive status on failure for retry`, async () => {
    const state = mount(screen)
    let reject
    state.control.write = () => new Promise((_, fail) => { reject = fail })
    const pending = state.toggle()
    await state.toggle()
    assert.equal(state.calls.length, 1)
    assert.equal(state.current().is_active, false)
    assert.match(await state.render(), /disabled/)
    reject(new Error('Offline'))
    await pending
    assert.equal(state.current().is_active, false)
    assert.match(state.error(), /Could not reactivate/)
    state.control.write = async () => ({ is_active: true })
    await state.toggle()
    assert.equal(state.current().is_active, true)
  })

  if (screen[0].startsWith('views/')) {
    test(`${screen[0]} cancels reactivation without submitting`, async () => {
      const state = mount(screen)
      state.control.confirmed = false
      await state.toggle()
      assert.equal(state.calls.length, 0)
      assert.equal(state.current().is_active, false)
    })
  }
}
