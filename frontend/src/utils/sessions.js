// Shared helpers for the instructor session pages. Plain functions, no Vue.

export const ATTENDANCE_STATUSES = [
  { value: 'present', label: 'Present' },
  { value: 'absent', label: 'Absent' },
]

export const ABSENCE_REASONS = [
  { value: 'no_show', label: 'No show' },
  { value: 'medical_appointment', label: 'Medical appointment' },
  { value: 'transport_issue', label: 'Transport issue' },
  { value: 'other', label: 'Other' },
]

export const SESSION_PERIODS = ['This month', 'This quarter', 'All']

// Match Django's Pacific/Auckland day, even when the browser is abroad.
export function programmeToday(now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-NZ', {
    timeZone: 'Pacific/Auckland', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now)
  const values = Object.fromEntries(parts.map(part => [part.type, part.value]))
  return `${values.year}-${values.month}-${values.day}`
}

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
  const counts = { present: 0, absent: 0 }
  for (const record of attendance) counts[record.status]++

  const total = attendance.length
  const rate = total ? Math.round((counts.present / total) * 100) : 0

  return { ...counts, total, rate }
}
