// Missing or unperformed results break a line; they are never plotted as zero.
export function measurementPoints(assessments, exercise) {
  return assessments.filter(row => !row.status || row.status === 'completed')
    .map(row => {
      const result = row.results.find(result => result.exercise === exercise)
      return { date: row.date || row.assessed_on,
        value: result && ['measured', 'arms_used'].includes(result.outcome) && result.value !== null ? Number(result.value) : null,
        note: result?.outcome || 'not recorded' }
    }).sort((a, b) => a.date.localeCompare(b.date))
}
export function chartGeometry(points) {
  const values = points.map(point => point.value).filter(value => value !== null && Number.isFinite(value))
  const maximum = Math.max(1, ...values)
  const dates = points.map(point => Date.parse(`${point.date}T00:00:00Z`))
  const first = Math.min(...dates), last = Math.max(...dates)
  const plotted = points.map((point, index) => ({ ...point,
    x: last === first ? 320 : 55 + 530 * (dates[index] - first) / (last - first),
    y: point.value === null ? null : 165 - 130 * point.value / maximum,
  }))
  const segments = []
  let segment = []
  for (const point of plotted) {
    if (point.y === null) { if (segment.length) segments.push(segment); segment = [] }
    else segment.push(point)
  }
  if (segment.length) segments.push(segment)
  return { maximum, plotted, segments, hasData: values.length > 0 }
}
