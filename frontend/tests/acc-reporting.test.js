import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, computed, watch, nextTick } from 'vue'
import * as Vue from 'vue'
import { renderToString } from '@vue/server-renderer'
import { parse, compileScript } from '@vue/compiler-sfc'
import { recentReportPeriod, formatReportNumber } from '../src/utils/reporting.js'
import { renderMarkdown } from '../src/utils/markdown.js'
import { feedbackSpeakerLabel } from '../src/utils/feedback.js'

const { descriptor } = parse(readFileSync(new URL('../src/views/SuperAdmin/ACCReporting.vue', import.meta.url), 'utf8'))
const compiled = compileScript(descriptor, { id: 'acc-reporting-test' }).content
  .replace(/^import .*$/gm, '').replace('export default', 'const component =')

test('ACC selection requires renewed approval after edits, retains drafts on failure, and resets when scope changes', async () => {
  const requests = []
  let fail = true
  const completed = { job_id: 'job', status: 'succeeded', narrative: 'Draft', statistics: {} }
  const context = vm.createContext({
    ref, computed, watch, recentReportPeriod, AbortController, feedbackSpeakerLabel,
    onMounted() {}, onBeforeUnmount() {}, QuarterPeriod: {}, ModelSelector: {}, ACCReport: {},
    generateACCReport: async payload => {
      requests.push(payload)
      if (fail) throw new Error('Queue unavailable')
      return completed
    },
  })
  vm.runInContext(compiled + '\nthis.component = component', context)
  const page = context.component.setup({}, { expose() {} })
  page.candidates.value = { count: 1, results: [] }
  page.model.value = 'test-model'
  const original = { id: 'feedback-id', text: 'PRIVATE says classes help.', speaker: 'kaumātua', branch: 'Branch', date: '2026-01-01' }
  page.select(original, true)
  await nextTick()
  assert.equal(page.approved.value, false)
  assert.equal(page.sources.value[0].speaker, 'kaumātua')
  assert.ok(!page.ready.value)
  page.approved.value = true
  page.sources.value[0].text = 'Classes help.'
  await nextTick()
  assert.equal(page.approved.value, false)
  page.approved.value = true
  assert.ok(page.ready.value)
  await page.generate()
  assert.equal(page.error.value, 'Queue unavailable')
  assert.equal(page.sources.value[0].text, 'Classes help.')
  assert.equal(page.generating.value, false)
  fail = false
  await page.generate()
  assert.equal(page.result.value.job_id, 'job')
  assert.equal(requests.at(-1).sources[0].text, 'Classes help.')
  assert.equal(requests.at(-1).sources[0].branch, undefined)
  assert.equal(requests.at(-1).sources[0].speaker, undefined)
  assert.equal(original.text, 'PRIVATE says classes help.')
  page.branchId.value = 'different-branch'
  await nextTick()
  assert.equal(page.candidates.value, null)
  assert.equal(page.sources.value.length, 0)
  assert.equal(page.result.value, null)
  assert.equal(page.approved.value, false)
})

test('ACC reports hide saved citation lines while preserving narrative, quotations, and edits', () => {
  const { descriptor } = parse(readFileSync(new URL('../src/components/reporting/ACCReport.vue', import.meta.url), 'utf8'))
  const compiled = compileScript(descriptor, { id: 'acc-report-test' }).content
    .replace(/^import .*$/gm, '').replace('export default', 'const component =')
  const context = vm.createContext({ ref, computed, ReportNarrative: {}, LABELS: {}, formatReportNumber() {}, printReport() {}, feedbackSpeakerLabel })
  vm.runInContext(compiled + '\nthis.component = component', context)
  const narrative = '## Wellbeing\n\nOne participant reported walking without a stick.\n\nSources: [F-feedback](#acc-source-F-feedback), [S-attendance](#acc-source-S-attendance)\n\n## Supporting quotations\n\n> I walked without my stick.\n\n[F-feedback](#acc-source-F-feedback)\n\n[Useful context](https://example.com/report)'
  const report = context.component.setup({ savedReport: {
    narrative, statistics: { aggregates: { 'S-attendance': {}, 'S-physical': {} } },
  } }, { expose() {} })
  const html = renderMarkdown(report.displayNarrative.value)
  assert.doesNotMatch(html, /F-feedback|S-attendance|acc-source|Sources:/)
  assert.match(html, /One participant reported walking without a stick\./)
  assert.match(html, /<blockquote>\s*<p>I walked without my stick\.<\/p>/)
  assert.match(html, /href="https:\/\/example.com\/report"/)
  assert.equal(report.narrative.value, narrative)
  report.narrative.value = 'Reviewed narrative.\r\n\r\n[F-feedback](#acc-source-F-feedback)\r\n'
  assert.equal(report.displayNarrative.value.trim(), 'Reviewed narrative.')
})

test('ACC PDF export waits for saved edits and shows a recoverable popup error', () => {
  const { descriptor } = parse(readFileSync(new URL('../src/components/reporting/ACCReport.vue', import.meta.url), 'utf8'))
  const compiled = compileScript(descriptor, { id: 'acc-pdf-test' }).content
    .replace(/^import .*$/gm, '').replace('export default', 'const component =')
  const requests = []
  let blocked = true
  const context = vm.createContext({
    ref, computed, ReportNarrative: {}, LABELS: {}, formatReportNumber() {}, feedbackSpeakerLabel,
    printReport: (...args) => {
      requests.push(args)
      if (blocked) throw new Error('Allow pop-ups for this site, then try downloading the PDF again.')
    },
  })
  vm.runInContext(compiled + '\nthis.component = component', context)
  const report = context.component.setup({ savedReport: {
    narrative: 'Saved narrative', statistics: {
      scope_label: 'Taurite Tū', scope: { start_date: '2026-01-01', end_date: '2026-03-31' },
      aggregates: { 'S-attendance': {}, 'S-physical': {} },
    },
  } }, { expose() {} })
  report.reportElement.value = { renderedReport: true }
  report.editing.value = true
  report.downloadPDF()
  assert.equal(requests.length, 0)
  report.editing.value = false
  report.downloadPDF()
  assert.match(report.exportError.value, /Allow pop-ups/)
  blocked = false
  report.downloadPDF()
  assert.equal(report.exportError.value, '')
  assert.equal(requests.at(-1)[0], report.reportElement.value)
  assert.equal(requests.at(-1)[1], 'ACC report - Taurite Tū - 2026-01-01 to 2026-03-31')
})

test('ACC renders engagement first with registered counts, zero rates, missing data, and older snapshots', async () => {
  const { descriptor } = parse(readFileSync(new URL('../src/components/reporting/ACCReport.vue', import.meta.url), 'utf8'))
  const compiled = compileScript(descriptor, { id: 'acc-engagement-test', inlineTemplate: true }).content
    .replace(/^import \{(.+)\} from ['"]vue['"];?$/gm, (_, bindings) => `const {${bindings.replace(/ as /g, ':')}} = Vue`)
    .replace(/^import .*$/gm, '').replace('export default', 'const component =')
  const context = vm.createContext({ Vue, ReportNarrative: { render() {} }, LABELS: {}, formatReportNumber, printReport() {}, feedbackSpeakerLabel })
  vm.runInContext(compiled + '\nthis.component = component', context)
  const engagement = {
    branches: [
      { branch_id: 'a', entity: 'Taurite Tū', location: 'Ōtepoti', participants: 24, new_participants: 3, engagement_percent: 85.06 },
      { branch_id: 'b', entity: 'No attendance', location: null, participants: 2, new_participants: 0, engagement_percent: 0 },
      { branch_id: 'c', entity: '<img src=x onerror=alert(1)>', location: null, participants: 0, new_participants: 0, engagement_percent: null },
      { branch_id: 'd', entity: 'Halfway', location: 'Heretaunga', participants: 20, new_participants: 2, engagement_percent: 87.5 },
    ],
    limitations: ['Incomplete registers are excluded.'],
  }
  const savedReport = { job_id: 'saved', narrative: 'Saved narrative', statistics: {
    scope_label: 'All branches', scope: { start_date: '2026-01-01', end_date: '2026-03-31' }, sources: [], limitations: [],
    aggregates: { 'S-engagement': engagement, 'S-attendance': {}, 'S-enrolments': { new_enrolments: 3 },
      'S-physical': { totals: { tested_participants: 0, eligible_participants: 26, completed_assessments: 0 }, paired_changes: [], limitations: [] } },
  } }
  const html = await renderToString(Vue.createSSRApp(context.component, { savedReport }))
  assert.ok(html.indexOf('<h2>Engagement</h2>') < html.indexOf('<h2>Recorded physical testing</h2>'))
  assert.match(html, /# Participants/)
  assert.match(html, /# New Participants/)
  assert.match(html, /% Engagement/)
  assert.match(html, /Taurite Tū/)
  assert.match(html, /Ōtepoti/)
  assert.match(html, /<td>24<\/td><td>3<\/td><td>85%<\/td>/)
  assert.match(html, /<td>20<\/td><td>2<\/td><td>90%<\/td>/)
  assert.match(html, /<td>2<\/td><td>0<\/td><td>0%<\/td>/)
  assert.match(html, /<td>0<\/td><td>0<\/td><td>Not available<\/td>/)
  assert.match(html, /Not recorded/)
  assert.match(html, /&lt;img src=x onerror=alert\(1\)&gt;/)
  assert.doesNotMatch(html, /<img/)
  delete savedReport.statistics.aggregates['S-engagement']
  const legacy = await renderToString(Vue.createSSRApp(context.component, { savedReport }))
  assert.match(legacy, /Branch participation was not saved with this draft/)
  assert.doesNotMatch(legacy, /# Participants/)
})
