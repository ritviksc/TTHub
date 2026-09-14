// Shared helpers for the instructor session pages. Plain functions, no Vue.

export const ATTENDANCE_STATUSES = [
  { value: 'present', label: 'Present' },
  { value: 'absent', label: 'Absent' },
  { value: 'excused', label: 'Excused' },
]

export const ABSENCE_REASONS = [
  'Sick',
  'Family commitment',
  'Transport issue',
  'Work commitment',
  'Other',
]

export const SESSION_PERIODS = ['This month', 'This quarter', 'All']

export function initials(name = '') {
  return name.trim().charAt(0).toUpperCase()
}

// "YYYY-MM-DD" on its own parses as UTC midnight, which can land on the wrong day.
function toLocalDate(date) {
  return new Date(`${date}T00:00`)
}

export function formatSessionDate(date) {
  if (!date) return ''

  return toLocalDate(date).toLocaleDateString('en-NZ', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function isInPeriod(date, period) {
  if (period === 'All') return true

  const day = toLocalDate(date)
  const today = new Date()
  if (day.getFullYear() !== today.getFullYear()) return false

  if (period === 'This month') return day.getMonth() === today.getMonth()
  if (period === 'This quarter') return Math.floor(day.getMonth() / 3) === Math.floor(today.getMonth() / 3)
  return true
}

export function countByStatus(attendance = []) {
  const counts = { present: 0, absent: 0, excused: 0 }
  for (const record of attendance) counts[record.status]++

  const total = attendance.length
  const rate = total ? Math.round((counts.present / total) * 100) : 0

  return { ...counts, total, rate }
}
