import assert from 'node:assert/strict'
import { test } from 'node:test'
import { BALANCE, emptyResult, resultPayload, balanceBlocked, resultText, assessmentReady } from '../src/utils/physicalTests.js'

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
