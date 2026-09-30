import { programmeToday } from './sessions.js'

export function programmeQuarter(now = new Date()) {
  const [year, month] = programmeToday(now).split('-').map(Number)
  const firstMonth = Math.floor((month - 1) / 3) * 3 + 1
  const lastMonth = firstMonth + 2
  const lastDay = new Date(Date.UTC(year, lastMonth, 0)).getUTCDate()
  return {
    start_date: `${year}-${String(firstMonth).padStart(2, '0')}-01`,
    end_date: `${year}-${String(lastMonth).padStart(2, '0')}-${lastDay}`,
  }
}

export function attendanceRate(report) {
  const rate = report?.totals?.attendance_rate_percent
  return rate == null ? null : Math.round(rate)
}

// Reject the load when any required source fails: missing data is not zero.
export async function loadBranchOverview(api, scope) {
  const [participants, sessions, instructors, report] = await Promise.all([
    api.listParticipants(), api.listSessions(), api.listStaff(), api.getAttendanceReport(scope),
  ])
  return { participants, sessions, instructors, report }
}
