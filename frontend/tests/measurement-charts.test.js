import { test } from 'node:test'
import assert from 'node:assert/strict'
import { measurementPoints, chartGeometry } from '../src/utils/measurementCharts.js'

test('drafts are excluded and unable results make gaps, while arms-used zeros remain', () => {
  const points = measurementPoints([
    { status: 'completed', assessed_on: '2026-01-01', results: [{ exercise: 'chair', outcome: 'measured', value: '12.00' }] },
    { status: 'draft', assessed_on: '2026-01-02', results: [{ exercise: 'chair', outcome: 'measured', value: '100.00' }] },
    { status: 'completed', assessed_on: '2026-02-01', results: [{ exercise: 'chair', outcome: 'unable', value: null }] },
    { status: 'completed', assessed_on: '2026-03-01', results: [{ exercise: 'chair', outcome: 'arms_used', value: '0.00' }] },
  ], 'chair')
  assert.deepEqual(points.map(p => p.value), [12, null, 0])
  const chart = chartGeometry(points)
  assert.equal(chart.segments.length, 2)
  assert.equal(chart.plotted[2].y, 165)
})
test('date spacing reflects elapsed time and single measurements do not divide by zero', () => {
  const chart = chartGeometry([{ date: '2026-01-01', value: 1 }, { date: '2026-01-02', value: 2 }, { date: '2026-01-11', value: 3 }])
  assert.equal(chart.plotted[1].x, 108)
  assert.equal(chartGeometry([{ date: '2026-01-01', value: 0 }]).plotted[0].x, 320)
  assert.equal(chartGeometry([]).hasData, false)
  assert.equal(chartGeometry([{ date: '2026-01-01', value: null }]).hasData, false)
})
