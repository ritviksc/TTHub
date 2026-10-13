import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, computed, reactive, createSSRApp, compile } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { parse, compileScript } from '@vue/compiler-sfc'
import { ABSENCE_REASONS, countByStatus, formatSessionDate, initials } from '../src/utils/sessions.js'

const { descriptor } = parse(readFileSync(new URL('../src/views/Instructor/AttendanceMode.vue', import.meta.url), 'utf8'))
const compiled = compileScript(descriptor, { id: 'attendance-mode-test' }).content
  .replace(/^import .*$/gm, '').replace('export default', 'const component =')

async function mount({ finalised = false, fail = false, role = 'instructor', review = false, failFinalise = false } = {}) {
  const requests = [], events = [], destinations = []
  const record = { id: 'record', name: 'Example', status: 'absent', absence_reason: '', absence_reason_other: '' }
  const context = vm.createContext({
    ref, computed, onMounted() {}, RouterLink: {}, ABSENCE_REASONS, countByStatus, formatSessionDate, initials,
    auth: reactive({ user: { role } }),
    useRoute: () => ({ params: { id: 'session' }, query: review ? { review: '1' } : {} }),
    useRouter: () => ({ push: async route => { destinations.push(route); events.push('navigate') } }), confirm: () => true,
    getSession: async () => ({ attendance_finalised: finalised, attendance: [record] }),
    updateAttendance: async (session, id, changes) => {
      requests.push(changes)
      if (fail) throw new Error('Network failure')
      events.push('save')
      return { ...record, ...changes }
    },
    setAttendanceFinalised: async (id, value) => {
      if (failFinalise) throw Error('Network failure')
      events.push('finalise')
      return { attendance_finalised: value }
    },
  })
  vm.runInContext(compiled + '\nthis.component = component', context)
  const page = context.component.setup({}, { expose() {} })
  await page.load()
  return { page, record: page.session.value.attendance[0], requests, events, destinations }
}

test('review saves absence reasons without reopening finalised attendance', async () => {
  const { page, record, requests, events } = await mount({ review: true, finalised: true })
  page.reasonDrafts.value.record.absence_reason = 'transport_issue'
  await page.saveReason(record)
  assert.equal(requests[0].absence_reason, 'transport_issue')
  assert.equal(record.status, 'absent')
  assert.equal(record.absence_reason, 'transport_issue')
  assert.equal(page.session.value.attendance_finalised, true)
  assert.deepEqual(events, ['save'])
})

test('Done saves Other and its explanation before finalising', async () => {
  const { page, events, requests } = await mount({ review: true, finalised: true })
  Object.assign(page.reasonDrafts.value.record, { absence_reason: 'other', absence_reason_other: ' Family commitment ' })
  await page.setFinalised(true)
  assert.equal(requests[0].absence_reason_other, 'Family commitment')
  assert.deepEqual(events, ['save', 'finalise', 'navigate'])
})

test('missing explanation and failed saves prevent finalisation and retain drafts', async () => {
  for (const fail of [false, true]) {
    const { page, events } = await mount({ fail, review: true, finalised: true })
    Object.assign(page.reasonDrafts.value.record, { absence_reason: 'other', absence_reason_other: fail ? 'Explanation' : '' })
    await page.setFinalised(true)
    assert.deepEqual(events, [])
    assert.ok(page.saveError.value)
    assert.equal(page.reasonDrafts.value.record.absence_reason, 'other')
    assert.equal(page.saving.value, false)
  }
})

test('marking mode hides reason editing and Done does not save reason drafts', async () => {
  const { page, record, requests, events } = await mount()
  assert.equal(page.reviewing.value, false)
  page.reasonDrafts.value.record.absence_reason = 'no_show'
  await page.saveReason(record)
  await page.setFinalised(true)
  assert.equal(requests.length, 0)
  assert.deepEqual(events, ['finalise', 'navigate'])
})

test('failed finalisation stays on attendance mode and reports the error', async () => {
  const { page, events, destinations } = await mount({ failFinalise: true })
  await page.setFinalised(true)
  assert.deepEqual(events, [])
  assert.equal(destinations.length, 0)
  assert.equal(page.session.value.attendance_finalised, false)
  assert.ok(page.saveError.value)
  assert.equal(page.saving.value, false)
})

test('review does not save an absence reason for present participants', async () => {
  const { page, record, requests } = await mount({ review: true, finalised: true })
  record.status = 'present'
  await page.saveReason(record)
  assert.equal(requests.length, 0)
})

test('rendered marking rows have no reason form; review shows forms only for absences', async () => {
  for (const review of [false, true]) {
    const { page, record } = await mount({ review, finalised: review })
    const render = async () => {
      const app = createSSRApp({ setup: () => ({ ...page }), render: compile(descriptor.template.content) })
      app.component('RouterLink', { render: () => null })
      return renderToString(app)
    }
    const html = await render()
    assert.equal(html.includes('class="absence-form"'), review)
    assert.equal(html.includes('Save reason'), review)
    assert.ok(html.includes('person-row absent'))
    if (review) {
      await page.setFinalised(false)
      const reopened = await render()
      assert.equal(reopened.includes('class="absence-form"'), false)
      assert.ok(reopened.includes('<h1>Attendance mode</h1>'))
      assert.ok(reopened.includes('Tap to mark present'))
    }
    record.status = 'present'
    assert.equal((await render()).includes('class="absence-form"'), false)
  }
})

for (const [role, prefix] of [['instructor', 'in'], ['branch_manager', 'bm']]) {
  test(`${role} reopens attendance, marks present, and returns to their session page`, async () => {
    const { page, record, destinations, events } = await mount({ role, finalised: true, review: true })
    assert.equal(page.detailRoute.value.name, `${prefix}-session-detail`)
    page.reasonDrafts.value.record.absence_reason = 'transport_issue'
    await page.setFinalised(false)
    assert.deepEqual(events, ['save', 'finalise'])
    assert.equal(record.absence_reason, 'transport_issue')
    assert.equal(page.reviewing.value, false)
    assert.equal(page.session.value.attendance_finalised, false)
    await page.toggle(record)
    assert.equal(record.status, 'present')
    await page.setFinalised(true)
    assert.equal(destinations[0].name, `${prefix}-session-detail`)
    assert.equal(destinations[0].params.id, 'session')
  })
}

test('failed reason saves keep attendance finalised and review drafts visible when reopening', async () => {
  for (const fail of [false, true]) {
    const { page, events } = await mount({ review: true, finalised: true, fail })
    Object.assign(page.reasonDrafts.value.record, { absence_reason: 'other', absence_reason_other: fail ? 'Family commitment' : '' })
    await page.setFinalised(false)
    assert.deepEqual(events, [])
    assert.equal(page.session.value.attendance_finalised, true)
    assert.equal(page.reviewing.value, true)
    assert.equal(page.reasonDrafts.value.record.absence_reason, 'other')
    assert.ok(page.saveError.value)
    assert.equal(page.saving.value, false)
  }
})
