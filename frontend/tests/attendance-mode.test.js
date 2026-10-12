import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, computed } from 'vue'
import { parse, compileScript } from '@vue/compiler-sfc'
import { ABSENCE_REASONS, countByStatus, formatSessionDate, initials } from '../src/utils/sessions.js'

const { descriptor } = parse(readFileSync(new URL('../src/views/Instructor/AttendanceMode.vue', import.meta.url), 'utf8'))
const compiled = compileScript(descriptor, { id: 'attendance-mode-test' }).content
  .replace(/^import .*$/gm, '').replace('export default', 'const component =')

async function mount({ finalised = false, fail = false } = {}) {
  const requests = [], events = []
  const record = { id: 'record', name: 'Example', status: 'absent', absence_reason: '', absence_reason_other: '' }
  const context = vm.createContext({
    ref, computed, onMounted() {}, RouterLink: {}, ABSENCE_REASONS, countByStatus, formatSessionDate, initials,
    useRoute: () => ({ params: { id: 'session' } }),
    useRouter: () => ({ push: async () => events.push('navigate') }), confirm: () => true,
    getSession: async () => ({ attendance_finalised: finalised, attendance: [record] }),
    updateAttendance: async (session, id, changes) => {
      requests.push(changes)
      if (fail) throw new Error('Network failure')
      events.push('save')
      return { ...record, ...changes }
    },
    setAttendanceFinalised: async (id, value) => { events.push('finalise'); return { attendance_finalised: value } },
  })
  vm.runInContext(compiled + '\nthis.component = component', context)
  const page = context.component.setup({}, { expose() {} })
  await page.load()
  return { page, record: page.session.value.attendance[0], requests, events }
}

test('absence reasons persist without toggling attendance', async () => {
  const { page, record, requests } = await mount()
  page.reasonDrafts.value.record.absence_reason = 'transport_issue'
  await page.saveReason(record)
  assert.equal(requests[0].absence_reason, 'transport_issue')
  assert.equal(record.status, 'absent')
  assert.equal(record.absence_reason, 'transport_issue')
})

test('Done saves Other and its explanation before finalising', async () => {
  const { page, events, requests } = await mount()
  Object.assign(page.reasonDrafts.value.record, { absence_reason: 'other', absence_reason_other: ' Family commitment ' })
  await page.setFinalised(true)
  assert.equal(requests[0].absence_reason_other, 'Family commitment')
  assert.deepEqual(events, ['save', 'finalise', 'navigate'])
})

test('missing explanation and failed saves prevent finalisation and retain drafts', async () => {
  for (const fail of [false, true]) {
    const { page, events } = await mount({ fail })
    Object.assign(page.reasonDrafts.value.record, { absence_reason: 'other', absence_reason_other: fail ? 'Explanation' : '' })
    await page.setFinalised(true)
    assert.deepEqual(events, [])
    assert.ok(page.saveError.value)
    assert.equal(page.reasonDrafts.value.record.absence_reason, 'other')
    assert.equal(page.saving.value, false)
  }
})

test('finalised attendance cannot edit reasons', async () => {
  const { page, record, requests } = await mount({ finalised: true })
  page.reasonDrafts.value.record.absence_reason = 'no_show'
  await page.saveReason(record)
  assert.equal(requests.length, 0)
})
