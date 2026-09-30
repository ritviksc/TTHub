import assert from 'node:assert/strict'
import { test } from 'node:test'
import { programmeQuarter, attendanceRate, loadBranchOverview } from '../src/utils/branchOverview.js'

test('quarter uses programme dates, including NZ midnight across UTC boundaries', () => {
  assert.deepEqual(programmeQuarter(new Date('2026-09-30T00:00:00+13:00')), {
    start_date: '2026-07-01', end_date: '2026-09-30',
  })
  assert.deepEqual(programmeQuarter(new Date('2026-10-01T00:00:00+13:00')), {
    start_date: '2026-10-01', end_date: '2026-12-31',
  })
  assert.deepEqual(programmeQuarter(new Date('2027-01-01T00:00:00+13:00')), {
    start_date: '2027-01-01', end_date: '2027-03-31',
  })
})

test('uses the official rate and distinguishes no denominator from zero attendance', () => {
  assert.equal(attendanceRate({ totals: { attendance_rate_percent: 100 } }), 100)
  assert.equal(attendanceRate({ totals: { attendance_rate_percent: 0 } }), 0)
  assert.equal(attendanceRate({ totals: { attendance_rate_percent: null } }), null)
  assert.equal(attendanceRate(null), null)
})

test('failed overview sources cannot masquerade as empty data', async () => {
  const api = {
    listParticipants: async () => [], listSessions: async () => [],
    listStaff: async () => [], getAttendanceReport: async () => ({ totals: {} }),
  }
  for (const name of Object.keys(api)) {
    await assert.rejects(loadBranchOverview({ ...api, [name]: async () => { throw Error('offline') } }, {}), /offline/)
  }
  const result = await loadBranchOverview(api, {})
  assert.deepEqual(result.participants, [])
  assert.deepEqual(result.report, { totals: {} })
})
