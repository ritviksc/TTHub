import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, computed, watch } from 'vue'
import { parse, compileScript } from '@vue/compiler-sfc'
import { recentReportPeriod } from '../src/utils/reporting.js'

test('saved attendance and physical reports mount without requesting fresh statistics', async () => {
  for (const name of ['AttendanceReport', 'PhysicalReport']) {
    const { descriptor } = parse(readFileSync(new URL(`../src/components/reporting/${name}.vue`, import.meta.url), 'utf8'))
    const compiled = compileScript(descriptor, { id: name }).content
      .replace(/^import[\s\S]*?from ['"][^'"]+['"];?\s*$/gm, '').replace('export default', 'const component =')
    const mounted = []
    const context = vm.createContext({
      ref, computed, watch, recentReportPeriod, onMounted: callback => mounted.push(callback), onBeforeUnmount() {},
      ModelSelector: {}, QuarterPeriod: {}, ReportNarrative: {}, ReportAnalysis: {}, MeasurementChart: {}, AssessmentTrend: {},
      getAttendanceReport() { assert.fail('History must use its saved snapshot') },
      getPhysicalReport() { assert.fail('History must use its saved snapshot') },
      listBranches() { assert.fail('History must not load live filters') },
    })
    vm.runInContext(compiled + '\nthis.component = component', context)
    const savedReport = { job_id: 'saved-id', statistics: { totals: { count: 4 } }, narrative: 'Previously edited', model: 'saved-model' }
    const page = context.component.setup({ savedReport, showBranchFilter: true }, { expose() {} })
    for (const callback of mounted) await callback()
    assert.deepEqual(page.report.value, savedReport.statistics)
    assert.equal(page.narrative.value, savedReport.narrative)
  }
})
