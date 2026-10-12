import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  getDaysInMonth,
  getFirstDayOfWeek,
  generateCalendarGrid,
  groupSessionsByDate,
  formatMonthYear,
  formatDateKey,
  parseDateKey,
  formatFullDate,
  formatTimeDisplay,
} from '../src/utils/calendar.js'

test('getDaysInMonth returns correct days for leap and non-leap years', () => {
  assert.equal(getDaysInMonth(2024, 1), 29) // Feb 2024 (leap)
  assert.equal(getDaysInMonth(2025, 1), 28) // Feb 2025
  assert.equal(getDaysInMonth(2026, 9), 31) // Oct 2026
  assert.equal(getDaysInMonth(2026, 10), 30) // Nov 2026
})

test('getFirstDayOfWeek returns 0 for Monday through 6 for Sunday', () => {
  // 1 Oct 2026 is a Thursday -> Monday=0, Tue=1, Wed=2, Thu=3
  assert.equal(getFirstDayOfWeek(2026, 9), 3)
})

test('generateCalendarGrid creates complete grid with 35 or 42 cells', () => {
  const grid = generateCalendarGrid(2026, 9, '2026-10-05')
  assert.ok(grid.length === 35 || grid.length === 42)
  assert.equal(grid.length % 7, 0)

  // Current month days should all be present
  const currentMonthDays = grid.filter(c => c.isCurrentMonth)
  assert.equal(currentMonthDays.length, 31)

  // Today marker
  const todayCell = grid.find(c => c.isToday)
  assert.ok(todayCell)
  assert.equal(todayCell.date, '2026-10-05')

  // Past dates relative to today
  const pastCell = grid.find(c => c.date === '2026-10-01')
  assert.ok(pastCell.isPast)
  const futureCell = grid.find(c => c.date === '2026-10-15')
  assert.equal(futureCell.isPast, false)
})

test('groupSessionsByDate clusters sessions by date and sorts by time', () => {
  const sessions = [
    { id: '1', date: '2026-10-10', time: '14:00', activity: 'Fitness test' },
    { id: '2', date: '2026-10-10', time: '09:30', activity: 'Morning training' },
    { id: '3', date: '2026-10-12', time: '10:00', activity: 'Standard class' },
  ]
  const grouped = groupSessionsByDate(sessions)
  assert.equal(Object.keys(grouped).length, 2)
  assert.equal(grouped['2026-10-10'].length, 2)
  assert.equal(grouped['2026-10-10'][0].id, '2') // 09:30 comes before 14:00
  assert.equal(grouped['2026-10-10'][1].id, '1')
  assert.equal(grouped['2026-10-12'].length, 1)
})

test('formatMonthYear returns both English and te reo Māori names', () => {
  const oct = formatMonthYear(2026, 9)
  assert.equal(oct.title, 'October 2026')
  assert.equal(oct.maori, 'Whiringa-ā-nuku 2026')
})

test('formatDateKey and parseDateKey roundtrip correctly', () => {
  const key = formatDateKey(2026, 9, 8)
  assert.equal(key, '2026-10-08')
  const parsed = parseDateKey(key)
  assert.deepEqual(parsed, { year: 2026, monthIndex: 9, day: 8 })
})

test('formatTimeDisplay formats 24hr strings nicely', () => {
  assert.equal(formatTimeDisplay('09:30:00'), '9:30 am')
  assert.equal(formatTimeDisplay('14:15'), '2:15 pm')
  assert.equal(formatTimeDisplay('12:00'), '12:00 pm')
  assert.equal(formatTimeDisplay('00:30'), '12:30 am')
})
