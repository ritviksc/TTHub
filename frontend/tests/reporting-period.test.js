import { test } from 'node:test'
import assert from 'node:assert/strict'
import { recentReportPeriod } from '../src/utils/reporting.js'

test('new NZ quarter still includes sessions from the previous quarter', () => {
  assert.deepEqual(recentReportPeriod(new Date('2026-09-30T12:00:00Z')), {
    start_date: '2026-07-01', end_date: '2026-10-01',
  })
})

test('recent reporting period crosses a year boundary', () => {
  assert.deepEqual(recentReportPeriod(new Date('2026-01-15T00:00:00Z')), {
    start_date: '2025-10-15', end_date: '2026-01-15',
  })
})

test('month-end subtraction clamps to February in ordinary and leap years', () => {
  for (const [year, day] of [[2026, 28], [2024, 29]]) {
    assert.deepEqual(recentReportPeriod(new Date(`${year}-05-31T00:00:00Z`)), {
      start_date: `${year}-02-${day}`, end_date: `${year}-05-31`,
    })
  }
})
