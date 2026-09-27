import { test } from 'node:test'
import assert from 'node:assert/strict'
import { finalisedAttendance, countByStatus, isInPeriod } from '../src/utils/sessions.js'
import { currentQuarter } from '../src/utils/reporting.js'

test('unfinished default absences cannot reduce participant attendance rate', () => {
  const rows = [{ status: 'present', attendance_finalised: true }, { status: 'absent', attendance_finalised: false }, { status: 'absent' }]
  assert.deepEqual(countByStatus(finalisedAttendance(rows)), { present: 1, absent: 0, total: 1, rate: 100 })
  rows[0].attendance_finalised = false
  assert.equal(finalisedAttendance(rows).length, 0)
})
test('month and quarter filters use New Zealand dates at the UTC boundary', () => {
  const now = new Date('2026-03-31T12:00:00Z') // April 1 in New Zealand.
  assert.deepEqual(currentQuarter(now), { start_date: '2026-04-01', end_date: '2026-06-30' })
  assert.equal(isInPeriod('2026-04-01', 'This month', now), true)
  assert.equal(isInPeriod('2026-03-31', 'This quarter', now), false)
})
