// Calendar utility functions for Taurite Tū programme sessions.

import { programmeToday } from './sessions.js'

export const WEEKDAYS = [
  { short: 'Mon', full: 'Monday', maori: 'Rāhina' },
  { short: 'Tue', full: 'Tuesday', maori: 'Rātū' },
  { short: 'Wed', full: 'Wednesday', maori: 'Rāapa' },
  { short: 'Thu', full: 'Thursday', maori: 'Rāpare' },
  { short: 'Fri', full: 'Friday', maori: 'Rāmere' },
  { short: 'Sat', full: 'Saturday', maori: 'Rāhoroi' },
  { short: 'Sun', full: 'Sunday', maori: 'Rātapu' },
]

export const MONTH_NAMES = [
  { name: 'January', maori: 'Kohi-tātea' },
  { name: 'February', maori: 'Hui-tanguru' },
  { name: 'March', maori: 'Poutū-te-rangi' },
  { name: 'April', maori: 'Paenga-whāwhā' },
  { name: 'May', maori: 'Haratua' },
  { name: 'June', maori: 'Pipiri' },
  { name: 'July', maori: 'Hōngongoi' },
  { name: 'August', maori: 'Here-turi-kōkā' },
  { name: 'September', maori: 'Mahuru' },
  { name: 'October', maori: 'Whiringa-ā-nuku' },
  { name: 'November', maori: 'Whiringa-ā-rangi' },
  { name: 'December', maori: 'Hakihea' },
]

export function pad2(n) {
  return String(n).padStart(2, '0')
}

export function formatDateKey(year, monthIndex, day) {
  return `${year}-${pad2(monthIndex + 1)}-${pad2(day)}`
}

export function parseDateKey(dateStr) {
  if (!dateStr || typeof dateStr !== 'string') return null
  const [y, m, d] = dateStr.split('-').map(Number)
  if (!y || !m || !d) return null
  return { year: y, monthIndex: m - 1, day: d }
}

export function getDaysInMonth(year, monthIndex) {
  return new Date(year, monthIndex + 1, 0).getDate()
}

// 0 for Monday ... 6 for Sunday
export function getFirstDayOfWeek(year, monthIndex) {
  const day = new Date(year, monthIndex, 1).getDay() // 0 = Sun, 1 = Mon ...
  return (day + 6) % 7
}

export function generateCalendarGrid(year, monthIndex, todayStr = programmeToday()) {
  const daysInMonth = getDaysInMonth(year, monthIndex)
  const firstDay = getFirstDayOfWeek(year, monthIndex)
  
  const prevMonthIndex = monthIndex === 0 ? 11 : monthIndex - 1
  const prevYear = monthIndex === 0 ? year - 1 : year
  const daysInPrevMonth = getDaysInMonth(prevYear, prevMonthIndex)
  
  const nextMonthIndex = monthIndex === 11 ? 0 : monthIndex + 1
  const nextYear = monthIndex === 11 ? year + 1 : year

  const cells = []

  // Trailing days from previous month
  for (let i = firstDay - 1; i >= 0; i--) {
    const day = daysInPrevMonth - i
    const dateKey = formatDateKey(prevYear, prevMonthIndex, day)
    cells.push({
      date: dateKey,
      dayNumber: day,
      isCurrentMonth: false,
      isToday: dateKey === todayStr,
      isPast: dateKey < todayStr,
    })
  }

  // Days in current month
  for (let day = 1; day <= daysInMonth; day++) {
    const dateKey = formatDateKey(year, monthIndex, day)
    cells.push({
      date: dateKey,
      dayNumber: day,
      isCurrentMonth: true,
      isToday: dateKey === todayStr,
      isPast: dateKey < todayStr,
    })
  }

  // Leading days from next month to complete grid
  const remaining = (7 - (cells.length % 7)) % 7
  const targetTotal = cells.length + remaining < 35 ? 35 : cells.length + remaining
  const neededFromNext = targetTotal - cells.length

  for (let day = 1; day <= neededFromNext; day++) {
    const dateKey = formatDateKey(nextYear, nextMonthIndex, day)
    cells.push({
      date: dateKey,
      dayNumber: day,
      isCurrentMonth: false,
      isToday: dateKey === todayStr,
      isPast: dateKey < todayStr,
    })
  }

  return cells
}

export function groupSessionsByDate(sessions = []) {
  const map = {}
  for (const session of sessions) {
    if (!session?.date) continue
    if (!map[session.date]) {
      map[session.date] = []
    }
    map[session.date].push(session)
  }
  for (const date in map) {
    map[date].sort((a, b) => (a.time || '').localeCompare(b.time || ''))
  }
  return map
}

export function formatMonthYear(year, monthIndex) {
  const m = MONTH_NAMES[monthIndex] || { name: '', maori: '' }
  return {
    title: `${m.name} ${year}`,
    maori: `${m.maori} ${year}`,
  }
}

export function formatFullDate(dateStr) {
  if (!dateStr) return ''
  const parsed = parseDateKey(dateStr)
  if (!parsed) return dateStr
  const dateObj = new Date(parsed.year, parsed.monthIndex, parsed.day)
  return dateObj.toLocaleDateString('en-NZ', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

export function formatTimeDisplay(timeStr) {
  if (!timeStr) return ''
  const [h, m] = timeStr.split(':')
  const hour = parseInt(h, 10)
  if (isNaN(hour)) return timeStr
  const ampm = hour >= 12 ? 'pm' : 'am'
  const displayHour = hour % 12 === 0 ? 12 : hour % 12
  return `${displayHour}:${m} ${ampm}`
}
