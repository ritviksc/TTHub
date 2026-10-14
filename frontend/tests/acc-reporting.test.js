import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, computed, watch, nextTick } from 'vue'
import { parse, compileScript } from '@vue/compiler-sfc'
import { recentReportPeriod } from '../src/utils/reporting.js'
import { renderMarkdown } from '../src/utils/markdown.js'

const { descriptor } = parse(readFileSync(new URL('../src/views/SuperAdmin/ACCReporting.vue', import.meta.url), 'utf8'))
const compiled = compileScript(descriptor, { id: 'acc-reporting-test' }).content
  .replace(/^import .*$/gm, '').replace('export default', 'const component =')

test('ACC selection requires renewed approval after edits, retains drafts on failure, and resets when scope changes', async () => {
  const requests = []
  let fail = true
  const completed = { job_id: 'job', status: 'succeeded', narrative: 'Draft', statistics: {} }
  const context = vm.createContext({
    ref, computed, watch, recentReportPeriod, AbortController,
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
  const original = { id: 'feedback-id', text: 'PRIVATE says classes help.', speaker: 'unknown', branch: 'Branch', date: '2026-01-01' }
  page.select(original, true)
  await nextTick()
  assert.equal(page.approved.value, false)
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
  const context = vm.createContext({ ref, computed, ReportNarrative: {}, LABELS: {}, formatReportNumber() {} })
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
