import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, computed, reactive, watch, createSSRApp, compile } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { parse, compileScript } from '@vue/compiler-sfc'
import { SESSION_PERIODS, formatSessionDate, isInPeriod, programmeToday } from '../src/utils/sessions.js'

const { descriptor } = parse(readFileSync(new URL('../src/views/Instructor/Sessions.vue', import.meta.url), 'utf8'))
const compiled = compileScript(descriptor, { id: 'session-creation-test' }).content
  .replace(/^import .*$/gm, '').replace('export default', 'const component =')

for (const [role, prefix] of [['instructor', 'in'], ['branch_manager', 'bm'], ['super_admin', 'sa']]) {
  test(`${role} can open session creation and navigate to the created session`, () => {
    const destinations = []
    const context = vm.createContext({
      ref, computed, onMounted() {}, RouterLink: {}, CreateSessionModal: {}, SessionCalendar: {},
      SESSION_PERIODS, formatSessionDate, isInPeriod, listSessions: async () => [], listBranches: async () => [],
      auth: reactive({ user: { role } }),
      useRouter: () => ({ push: route => destinations.push(route) }),
    })
    vm.runInContext(compiled + '\nthis.component = component', context)
    const page = context.component.setup({}, { expose() {} })
    page.loading.value = false
    assert.equal(page.canCreate.value, true)
    page.openCreateModal('2026-10-13')
    assert.equal(page.showCreate.value, true)
    assert.equal(page.createInitialDate.value, '2026-10-13')
    page.onCreated({ id: 'new-session' })
    assert.equal(page.showCreate.value, false)
    assert.equal(page.sessions.value[0].id, 'new-session')
    assert.equal(destinations[0].name, `${prefix}-session-detail`)
    assert.equal(destinations[0].params.id, 'new-session')
  })
}

const modalDescriptor = parse(readFileSync(new URL('../src/components/sessions/CreateSessionModal.vue', import.meta.url), 'utf8')).descriptor
const modalScript = compileScript(modalDescriptor, { id: 'session-create-modal-test' }).content
  .replace(/^import .*$/gm, '').replace('export default', 'const component =')

function mountModal(role, initialBranch = '') {
  const events = [], requests = []
  const control = { write: async payload => ({ id: 'created', ...payload }) }
  const props = { initialDate: programmeToday(), initialBranch, branches: [{ id: 'a', name: 'Harbour' }, { id: 'b', name: 'Hills' }] }
  const context = vm.createContext({
    ref, computed, watch, programmeToday, auth: { user: { role } },
    createSession: async payload => { requests.push(payload); return control.write(payload) },
  })
  vm.runInContext(modalScript + '\nthis.component = component', context)
  const page = context.component.setup(props, { expose() {}, emit: (...args) => events.push(args) })
  Object.assign(page.form.value, { time: '09:00', activity: 'Fitness test' })
  const render = () => renderToString(createSSRApp({ setup: () => ({ ...page, ...props }), render: compile(modalDescriptor.template.content) }))
  return { page, control, events, requests, render }
}

for (const role of ['super_admin', 'branch_manager', 'instructor']) {
  test(`${role} session form submits the correct branch payload and shows the branch picker only nationally`, async () => {
    const state = mountModal(role, 'b')
    assert.equal((await state.render()).includes('id="session-branch"'), role === 'super_admin')
    assert.equal(state.page.form.value.branch, 'b')
    await state.page.submit()
    assert.equal(state.requests.length, 1)
    assert.equal(state.requests[0].branch, role === 'super_admin' ? 'b' : undefined)
    assert.equal(state.requests[0].activity, 'Fitness test')
    assert.equal(state.events[0][0], 'created')
    assert.equal(state.events[0][1].id, 'created')
  })
}

test('national session creation requires a valid selected branch and preserves the draft on server failure', async () => {
  const state = mountModal('super_admin')
  for (const branch of ['', 'unknown']) {
    state.page.form.value.branch = branch
    await state.page.submit()
    assert.match(state.page.error.value, /Choose a branch/)
    assert.equal(state.requests.length, 0)
  }
  state.page.form.value.branch = 'a'
  state.control.write = async () => { throw { response: { data: { branch: ['That branch no longer exists.'] } } } }
  await state.page.submit()
  assert.equal(state.page.error.value, 'That branch no longer exists.')
  assert.equal(state.events.length, 0)
  assert.equal(state.page.form.value.branch, 'a')
  assert.equal(state.page.form.value.activity, 'Fitness test')
  assert.equal(state.page.saving.value, false)
  state.control.write = async payload => ({ id: 'retry', ...payload })
  await state.page.submit()
  assert.equal(state.events[0][1].id, 'retry')
})

test('session submission blocks duplicate writes and closing while creating, and still rejects past dates', async () => {
  const state = mountModal('super_admin', 'a')
  state.page.form.value.date = '2000-01-01'
  await state.page.submit()
  assert.match(state.page.error.value, /cannot be in the past/)
  assert.equal(state.requests.length, 0)
  state.page.form.value.date = programmeToday()
  let finish
  state.control.write = () => new Promise(resolve => { finish = resolve })
  const pending = state.page.submit()
  await state.page.submit()
  state.page.close()
  assert.equal(state.requests.length, 1)
  assert.equal(state.events.length, 0)
  assert.match(await state.render(), /<fieldset disabled/)
  finish({ id: 'created' })
  await pending
  assert.equal(state.events.length, 1)
  state.page.close()
  assert.equal(state.events[1][0], 'close')
})
