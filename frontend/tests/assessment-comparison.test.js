import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { computed, ref, createSSRApp, compile, h } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { parse, compileScript } from '@vue/compiler-sfc'
import { assessmentRoute, assessmentComparison, LABELS, resultText, physicalError } from '../src/utils/physicalTests.js'

const { descriptor } = parse(readFileSync(new URL('../src/components/physicalTests/AssessmentHistory.vue', import.meta.url), 'utf8'))
const compiled = compileScript(descriptor, { id: 'assessment-comparison-test' }).content
  .replace(/^import .*$/gm, '').replace('export default', 'const component =')
const baseline = { id: 'baseline', status: 'completed', assessed_on: '2026-01-01', completed_at: '2026-01-01T10:00:00Z', results: [
  { exercise: 'tug', outcome: 'measured', value: '12.40' },
  { exercise: 'chair', outcome: 'arms_used', value: '0.00' },
  { exercise: 'feet_together', outcome: 'measured', value: '10.00' },
] }
const latest = { id: 'latest', status: 'completed', assessed_on: '2026-03-01', completed_at: '2026-03-01T10:00:00Z', results: [
  { exercise: 'tug', outcome: 'measured', value: '10.10' },
  { exercise: 'chair', outcome: 'measured', value: '5.00' },
  { exercise: 'feet_together', outcome: 'unable', value: null },
] }

async function render(assessments, role) {
  const participant = { id: 'person', is_active: true }
  const context = vm.createContext({
    computed, ref, watch() {}, useRouter: () => ({ push() {} }),
    assessmentRoute, assessmentComparison, LABELS, resultText, physicalError, AssessmentTrend: {},
    auth: { user: { role } }, listPhysicalAssessments: async id => {
      assert.equal(id, participant.id)
      return assessments
    }, startPhysicalAssessment() { assert.fail('Comparing must not start a new assessment') },
  })
  vm.runInContext(compiled + '\nthis.component = component', context)
  const page = context.component.setup({ participant }, { expose() {} })
  await page.load()
  const app = createSSRApp({ props: ['participant'], setup: () => ({ ...page }), render: compile(descriptor.template.content) }, { participant })
  app.component('RouterLink', { props: ['to'], setup: (props, { slots }) => () => h('a', { href: `#${props.to.name}/${props.to.params.id}` }, slots.default()) })
  app.component('AssessmentTrend', { render: () => h('figure', 'Existing graph') })
  return renderToString(app)
}

for (const [role, prefix] of [['branch_manager', 'bm'], ['instructor', 'in']]) {
  test(`${role} sees baseline/latest results above existing graphs and history`, async () => {
    const html = await render([latest, baseline], role)
    assert.ok(html.includes('Baseline and latest completed assessments'))
    assert.ok(html.includes(`#${prefix}-physical-assessment/baseline`))
    assert.ok(html.includes(`#${prefix}-physical-assessment/latest`))
    assert.ok(html.includes('-2.3 seconds'))
    assert.ok(html.includes('+5 stands'))
    assert.ok(html.includes('Unable / stopped for safety'))
    assert.ok(html.includes('Not comparable'))
    assert.ok(html.indexOf('Baseline and latest') < html.indexOf('Existing graph'))
    assert.ok(html.indexOf('Existing graph') < html.indexOf('Assessment history —'))
  })
}

test('one completed assessment shows baseline without an invented follow-up; drafts establish no baseline', async () => {
  const single = await render([baseline], 'instructor')
  assert.ok(single.includes('Complete a follow-up assessment to compare results.'))
  assert.equal(single.includes('/latest'), false)
  assert.equal(single.includes('+0 stands'), false)
  const draft = await render([{ ...baseline, status: 'draft' }], 'instructor')
  assert.ok(draft.includes('Complete an assessment to establish a baseline.'))
  assert.equal(draft.includes('Baseline and latest completed assessments'), false)
  assert.equal(draft.includes('Existing graph'), false)
})
