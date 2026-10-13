// Procedures condensed from the client-supplied CDC / bpacnz assessment sheets.
export const BALANCE = ['feet_together', 'semi_tandem', 'heel_to_toe', 'one_foot']
export const LABELS = {
  tug: 'Timed up and go', chair: '30-second chair stand',
  feet_together: 'Feet together', semi_tandem: 'Half step (semi-tandem)',
  heel_to_toe: 'Heel to toe', one_foot: 'One foot',
}
export const OUTCOMES = {
  measured: 'Measured', unable: 'Unable / stopped for safety', arms_used: 'Arms needed to stand',
  not_attempted: 'Not attempted', skipped: 'Not attempted — balance test stopped',
}
export const GROUPS = [
  {
    key: 'tug', title: 'Timed up and go', exercises: ['tug'], guide: 'tug.pdf',
    setup: 'Use a standard armchair, a stopwatch and a mark 3 metres away. Wear regular footwear; a walking aid may be used.',
    steps: ['Begin seated with the back against the chair.', 'On “Go”, stand, walk to the mark at normal pace, turn, walk back and sit down.', 'Start timing on “Go”. Stop when the participant sits back down. Record seconds.'],
    safety: 'Always stay beside the participant for safety.',
  },
  {
    key: 'chair', title: '30-second chair stand', exercises: ['chair'], guide: 'chair-stand.pdf',
    setup: 'Use a straight-backed chair without armrests, against a wall so it cannot move, and a stopwatch.',
    steps: ['Sit in the middle of the chair with feet flat, back straight and hands on opposite shoulders, arms held against the chest.', 'On “Go”, rise fully and sit down again. Repeat for 30 seconds.', 'Count full stands. Count the last stand if more than halfway up when time ends.', 'If arms are needed to stand, stop and select “Arms needed to stand”; the recorded count is zero.'],
    safety: 'Stop if you feel the participant may fall.',
  },
  {
    key: 'balance', title: 'Four-stage balance', exercises: BALANCE, guide: 'balance.pdf',
    setup: 'Use a stopwatch. Eyes stay open; do not use a walking aid. Arms and body may move for balance, but feet must stay in position.',
    steps: ['Demonstrate each position. Stand beside the participant and hold their arm to help them get into position.', 'When steady, release support, say “Ready, begin” and start timing. Remain ready to assist if balance is lost.', 'Say “Stop” at 10 seconds. Proceed only if held for 10 seconds without moving feet or needing support; otherwise stop the test.', 'Feet together: feet side by side. Half step: instep of one foot touches the big toe of the other.', 'Heel to toe: one foot directly in front, heel touching toe. One foot: stand on one foot.'],
    safety: 'Do not perform this test if the participant appears unstable or at high risk of falling, or if you cannot safely catch them.',
  },
]
export function assessmentRoute(role) {
  return ({ super_admin: 'sa', branch_manager: 'bm', instructor: 'in' })[role] + '-physical-assessment'
}
export function resultText(row) {
  if (!row) return 'Not recorded'
  const label = OUTCOMES[row.outcome]
  return row.value === null || row.value === undefined ? label : `${row.value} ${row.exercise === 'chair' ? 'stands' : 'seconds'}${row.outcome === 'arms_used' ? ' — arms needed' : ''}`
}
export function assessmentComparison(assessments) {
  const completed = assessments.filter(row => row.status === 'completed').sort((a, b) =>
    a.assessed_on.localeCompare(b.assessed_on) || a.completed_at.localeCompare(b.completed_at),
  )
  const baseline = completed[0] || null
  const latest = completed.length > 1 ? completed.at(-1) : null
  const rows = Object.keys(LABELS).map(exercise => {
    const first = baseline?.results.find(row => row.exercise === exercise)
    const last = latest?.results.find(row => row.exercise === exercise)
    const comparable = [first, last].every(row => row &&
      ['measured', 'arms_used'].includes(row.outcome) && row.value !== null && row.value !== undefined,
    )
    return { exercise, baseline: first, latest: last,
      change: comparable ? Number((last.value - first.value).toFixed(2)) : null }
  })
  return { baseline, latest, rows }
}
export function emptyResult(exercise) {
  return { exercise, outcome: 'measured', value: null, notes: '', walking_aid: '' }
}
// A stopped balance stage makes subsequent measurements inapplicable, not zero.
export function balanceBlocked(rows, index) {
  return rows.slice(0, index).some(row => row.outcome !== 'measured' || row.value === null || row.value === '' || Number(row.value) !== 10)
}
export function resultPayload(rows, group) {
  return rows.map((row, index) => {
    if (group === 'balance' && balanceBlocked(rows, index)) {
      return { exercise: row.exercise, outcome: 'skipped', value: null, notes: '', walking_aid: '' }
    }
    return {
      exercise: row.exercise, outcome: row.outcome,
      value: row.outcome === 'arms_used' ? 0 : row.outcome === 'measured' ? row.value : null,
      notes: row.notes || '', walking_aid: row.exercise === 'tug' ? row.walking_aid || '' : '',
    }
  })
}
export function assessmentReady(results) {
  return Object.keys(LABELS).every(exercise => results.some(row => row.exercise === exercise && row.outcome !== 'not_attempted'))
}
export function physicalError(error) {
  const flatten = value => typeof value === 'string' ? value : Array.isArray(value)
    ? value.map(flatten).filter(Boolean).join(' ') : value && typeof value === 'object'
      ? Object.values(value).map(flatten).filter(Boolean).join(' ') : ''
  return flatten(error.response?.data) || 'Could not save or load the assessment. Please try again.'
}
