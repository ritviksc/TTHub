import assert from 'node:assert/strict'
import { test } from 'node:test'
import { BALANCE, emptyResult, resultPayload, balanceBlocked, resultText, assessmentReady, assessmentComparison } from '../src/utils/physicalTests.js'

test('balance stop clears later numeric measurements rather than recording zeros', () => {
  const rows = BALANCE.map(exercise => ({ ...emptyResult(exercise), value: 10 }))
  rows[1].value = '4.50'
  const payload = resultPayload(rows, 'balance')
  assert.equal(payload[1].value, '4.50')
  assert.equal(payload[2].outcome, 'skipped')
  assert.equal(payload[2].value, null)
  assert.equal(payload[3].outcome, 'skipped')
  assert.equal(rows[2].value, 10) // Building a payload does not mutate the form.
})
test('only a measured ten-second hold unlocks the next balance position', () => {
  for (const row of [{ outcome: 'unable', value: 10 }, { outcome: 'measured', value: '' }, { outcome: 'measured', value: 9 }]) {
    assert.equal(balanceBlocked([row], 1), true)
  }
  assert.equal(balanceBlocked([{ outcome: 'measured', value: '10.00' }], 1), false)
})
test('arms used forces zero while inability preserves a null measurement', () => {
  assert.equal(resultPayload([{ exercise: 'chair', outcome: 'arms_used', value: 8 }], 'chair')[0].value, 0)
  assert.equal(resultPayload([{ exercise: 'tug', outcome: 'unable', value: 8 }], 'tug')[0].value, null)
})
test('completion needs every exercise and excludes intentionally unattempted tests', () => {
  const rows = ['tug', 'chair', ...BALANCE].map(exercise => ({ exercise, outcome: 'measured' }))
  assert.equal(assessmentReady(rows), true)
  assert.equal(assessmentReady(rows.slice(1)), false)
  rows[0].outcome = 'not_attempted'
  assert.equal(assessmentReady(rows), false)
})
test('history distinguishes missing measurements, zero and skipped outcomes', () => {
  assert.equal(resultText(undefined), 'Not recorded')
  assert.match(resultText({ exercise: 'chair', outcome: 'arms_used', value: '0.00' }), /0.00 stands.*arms needed/)
  assert.equal(resultText({ exercise: 'one_foot', outcome: 'skipped', value: null }), 'Not attempted — balance test stopped')
})

test('comparison selects first and latest completed assessments without changing history order', () => {
  const assessment = (id, date, time, value, status = 'completed') => ({ id, assessed_on: date,
    completed_at: `${date}T${time}Z`, status, results: [{ exercise: 'tug', outcome: 'measured', value }] })
  const assessments = [
    assessment('latest', '2026-03-01', '11:00:00', '10.10'),
    assessment('baseline', '2026-01-01', '10:00:00', '12.40'),
    assessment('earlier-same-day', '2026-03-01', '10:00:00', '11.00'),
    assessment('draft', '2026-04-01', '10:00:00', '99.00', 'draft'),
  ]
  const comparison = assessmentComparison(assessments)
  assert.equal(comparison.baseline.id, 'baseline')
  assert.equal(comparison.latest.id, 'latest')
  assert.equal(comparison.rows[0].change, -2.3)
  assert.deepEqual(assessments.map(row => row.id), ['latest', 'baseline', 'earlier-same-day', 'draft'])
})

test('no completed assessment or only one cannot produce a change', () => {
  for (const assessments of [[], [{ status: 'draft', results: [] }]]) {
    const comparison = assessmentComparison(assessments)
    assert.equal(comparison.baseline, null)
    assert.equal(comparison.latest, null)
    assert.ok(comparison.rows.every(row => row.change === null))
  }
  const baseline = { id: 'only', status: 'completed', assessed_on: '2026-01-01', completed_at: '2026-01-01T10:00:00Z',
    results: [{ exercise: 'chair', outcome: 'measured', value: '12.00' }] }
  const comparison = assessmentComparison([baseline])
  assert.equal(comparison.baseline, baseline)
  assert.equal(comparison.latest, null)
  assert.ok(comparison.rows.every(row => row.change === null))
})

test('comparison preserves zero and unmeasured outcomes, using the latest assessment even when results are missing', () => {
  const assessments = [
    { id: 'first', status: 'completed', assessed_on: '2026-01-01', completed_at: '2026-01-01T10:00:00Z', results: [
      { exercise: 'chair', outcome: 'arms_used', value: '0.00' },
      { exercise: 'tug', outcome: 'measured', value: '12.40' },
      { exercise: 'feet_together', outcome: 'measured', value: '10.00' },
      { exercise: 'heel_to_toe', outcome: 'unable', value: null },
      { exercise: 'one_foot', outcome: 'skipped', value: null },
    ] },
    { id: 'last', status: 'completed', assessed_on: '2026-02-01', completed_at: '2026-02-01T10:00:00Z', results: [
      { exercise: 'chair', outcome: 'measured', value: '5.00' },
      { exercise: 'tug', outcome: 'unable', value: null },
      { exercise: 'feet_together', outcome: 'measured', value: '10.00' },
      { exercise: 'heel_to_toe', outcome: 'measured', value: '8.00' },
      { exercise: 'one_foot', outcome: 'skipped', value: null },
    ] },
  ]
  const rows = assessmentComparison(assessments).rows
  assert.equal(rows.find(row => row.exercise === 'chair').change, 5)
  assert.equal(rows.find(row => row.exercise === 'feet_together').change, 0)
  assert.equal(rows.find(row => row.exercise === 'tug').change, null)
  assert.equal(resultText(rows.find(row => row.exercise === 'tug').latest), 'Unable / stopped for safety')
  assert.equal(rows.find(row => row.exercise === 'heel_to_toe').change, null)
  assert.equal(rows.find(row => row.exercise === 'one_foot').change, null)
  assert.equal(rows.find(row => row.exercise === 'semi_tandem').change, null)
})
