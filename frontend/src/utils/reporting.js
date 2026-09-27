import { programmeToday } from './sessions.js'

function dateString(date) {
  // Keep local dates; UTC conversion can shift a New Zealand calendar date.
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

export function currentQuarter(today = new Date()) {
  const [year, calendarMonth] = programmeToday(today).split('-').map(Number)
  const month = Math.floor((calendarMonth - 1) / 3) * 3
  return {
    start_date: dateString(new Date(year, month, 1)),
    end_date: dateString(new Date(year, month + 3, 0)),
  }
}

export function formatReportNumber(value, suffix = '') {
  return value == null ? 'Not available' : `${value}${suffix}`
}

// TEMPORARY: Explicit preview fixture; replace with real API records for client demonstrations.
// This never seeds the database or substitutes for a failed live request.
export function demoAttendanceReport() {
  return {
    generated_at: new Date().toISOString(),
    scope: { start_date: '2026-01-01', end_date: '2026-03-31', branch_id: null },
    totals: {
      total_sessions: 4, finalised_sessions: 3, incomplete_sessions: 1, empty_sessions: 1,
      total_attendances: 10, total_roster_places: 24, distinct_attendees: 7,
      attendance_rate_percent: 41.67, average_attendance: 3.33,
    },
    monthly: [
      { month: '2026-01', finalised_sessions: 1, incomplete_sessions: 0, empty_sessions: 0,
        total_attendances: 6, total_roster_places: 8, attendance_rate_percent: 75,
        attendances_change: null, attendance_rate_change_percentage_points: null },
      { month: '2026-02', finalised_sessions: 1, incomplete_sessions: 0, empty_sessions: 1,
        total_attendances: 0, total_roster_places: 8, attendance_rate_percent: 0,
        attendances_change: -6, attendance_rate_change_percentage_points: -75 },
      { month: '2026-03', finalised_sessions: 1, incomplete_sessions: 1, empty_sessions: 0,
        total_attendances: 4, total_roster_places: 8, attendance_rate_percent: 50,
        attendances_change: 4, attendance_rate_change_percentage_points: 50 },
    ],
    limitations: [
      'Fictional preview data for January–March 2026; no real participant records are shown.',
      'Incomplete registers are excluded from attendance calculations; finalised empty sessions are included.',
      'Attendances count visits; distinct attendees count people.',
    ],
  }
}

// TEMPORARY: Example wording for the preview; live mode must use the analysis API.
export const DEMO_NARRATIVE = 'Example only — not AI-generated. Three finalised sessions recorded 10 attendances by 7 distinct attendees. One finalised session was empty and one unfinished register was excluded. Recorded attendance fell from 6 visits in January to zero in February, then rose to 4 in March. These figures do not establish why attendance changed.'
