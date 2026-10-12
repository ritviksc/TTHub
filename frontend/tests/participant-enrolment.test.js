import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, computed, reactive } from 'vue'
import { parse, compileScript } from '@vue/compiler-sfc'
import { programmeToday } from '../src/utils/sessions.js'

// Execute the real component setup with API/navigation substitutes; no copied form logic.
const { descriptor } = parse(readFileSync(new URL('../src/components/participants/ParticipantList.vue', import.meta.url), 'utf8'))
const compiled = compileScript(descriptor, { id: 'participant-enrolment-test' }).content
  .replace(/^import .*$/gm, '').replace('export default', 'const component =')

function mount(role = 'instructor', create = async payload => ({ ...payload, id: 'new-person' })) {
  const requests = [], destinations = []
  let opens = 0, closes = 0
  const context = vm.createContext({
    ref, computed, onMounted: () => {}, RouterLink: {}, programmeToday,
    auth: reactive({ user: { role, branch: { id: 'own-branch', name: 'Our branch' } } }),
    useRouter: () => ({ push: async route => { destinations.push(route) } }),
    listParticipants: async () => [],
    createParticipant: async payload => { requests.push(payload); return create(payload) },
  })
  vm.runInContext(compiled + '\nthis.component = component', context)
  const page = context.component.setup({}, { expose() {} })
  page.enrolmentDialog.value = { showModal() { opens++ }, close() { closes++ } }
  page.openEnrolment()
  Object.assign(page.newParticipant.value, { first_name: ' Aroha ', last_name: 'Example' })
  return { page, requests, destinations, context, get opens() { return opens }, get closes() { return closes } }
}

for (const role of ['branch_manager', 'instructor']) {
  test(`${role} enrols in their own branch and opens the saved record`, async () => {
    const state = mount(role)
    state.page.newParticipant.value.branch = 'forged-branch'
    await state.page.submitEnrolment()
    assert.equal(state.requests.length, 1)
    assert.equal(state.requests[0].first_name, 'Aroha')
    assert.equal(state.requests[0].date_of_birth, null)
    assert.equal(state.requests[0].joined_on, programmeToday())
    assert.equal('branch' in state.requests[0], false)
    assert.equal('gp_consent_given' in state.requests[0], role === 'branch_manager')
    assert.equal(state.page.canRecordGpConsent.value, role === 'branch_manager')
    assert.equal(state.destinations[0].name, 'participant-detail')
    assert.equal(state.destinations[0].params.id, 'new-person')
    assert.equal(state.closes, 1)
    assert.equal(state.page.saving.value, false)
  })
}

test('only managers submit GP consent, and unchecked consent discards an old date', async () => {
  for (const role of ['branch_manager', 'instructor']) {
    const state = mount(role)
    Object.assign(state.page.newParticipant.value, { gp_consent_given: true, gp_consent_date: programmeToday() })
    await state.page.submitEnrolment()
    assert.equal(state.requests[0].gp_consent_date, role === 'branch_manager' ? programmeToday() : undefined)
  }
  const state = mount('branch_manager')
  state.page.newParticipant.value.gp_consent_date = '2020-01-01'
  await state.page.submitEnrolment()
  assert.equal(state.requests[0].gp_consent_date, null)
})

test('validation failure retains entered details and exposes field errors without navigating', async () => {
  const state = mount('branch_manager', async () => { throw { response: { data: { email: ['Enter a valid email address.'] } } } })
  state.page.newParticipant.value.email = 'bad-email'
  await state.page.submitEnrolment()
  assert.equal(state.page.newParticipant.value.email, 'bad-email')
  assert.equal(state.page.fieldErrors.value.email, 'Enter a valid email address.')
  assert.equal(state.destinations.length, 0)
  assert.equal(state.closes, 0)
  assert.equal(state.page.saving.value, false)
})

test('saving prevents duplicate submissions and closing the dialog mid-request', async () => {
  let finish
  const state = mount('instructor', () => new Promise(resolve => { finish = resolve }))
  const pending = state.page.submitEnrolment()
  await state.page.submitEnrolment()
  state.page.closeEnrolment()
  assert.equal(state.requests.length, 1)
  assert.equal(state.closes, 0)
  finish({ id: 'new-person' })
  await pending
  assert.equal(state.closes, 1)
})

test('missing branch blocks submission and network errors preserve the form', async () => {
  const state = mount()
  state.context.auth.user.branch = null
  await state.page.submitEnrolment()
  assert.equal(state.requests.length, 0)
  assert.match(state.page.createError.value, /assigned to a branch/)
  const failed = mount('instructor', async () => { throw Error('offline') })
  await failed.page.submitEnrolment()
  assert.match(failed.page.createError.value, /Could not enrol/)
  assert.equal(failed.closes, 0)
  assert.equal(failed.page.newParticipant.value.first_name, ' Aroha ')
})
