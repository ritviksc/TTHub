import test from 'node:test'
import assert from 'node:assert/strict'
import { calendarQuarters } from '../src/utils/quarters.js'

test('calendar defaults cover the entire selected year with inclusive boundaries', () => {
  assert.deepEqual(calendarQuarters(2028), [
    { quarter: 1, start_date: '2028-01-01', end_date: '2028-03-31' },
    { quarter: 2, start_date: '2028-04-01', end_date: '2028-06-30' },
    { quarter: 3, start_date: '2028-07-01', end_date: '2028-09-30' },
    { quarter: 4, start_date: '2028-10-01', end_date: '2028-12-31' },
  ])
})
