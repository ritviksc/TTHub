import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref } from 'vue'
import { parse, compileScript } from '@vue/compiler-sfc'

const { descriptor } = parse(readFileSync(new URL('../src/components/reporting/ReportNarrative.vue', import.meta.url), 'utf8'))
const compiled = compileScript(descriptor, { id: 'report-narrative-test' }).content
  .replace(/^import .*$/gm, '').replace('export default', 'const component =')

test('both report editors save, cancel, and retain drafts after a failed save', async () => {
  for (const reportType of ['attendance', 'physical']) {
    const events = [], requests = []
    let fail = true
    const context = vm.createContext({
      ref, auth: { user: { role: 'super_admin' } }, MarkdownResponse: {},
      saveReportNarrative: async (...args) => {
        requests.push(args)
        if (fail) throw new Error('Offline')
        return { narrative: args[2] }
      },
    })
    vm.runInContext(compiled + '\nthis.component = component', context)
    const editor = context.component.setup({ text: 'Original', jobId: 'job-id', reportType }, {
      expose() {}, emit: (...args) => events.push(args),
    })
    editor.edit()
    assert.equal(editor.draft.value, 'Original')
    editor.draft.value = 'Reviewed'
    await editor.save()
    assert.equal(editor.editing.value, true)
    assert.equal(editor.draft.value, 'Reviewed')
    assert.ok(editor.error.value)
    assert.equal(editor.saving.value, false)
    fail = false
    await editor.save()
    assert.deepEqual(requests.at(-1), [reportType, 'job-id', 'Reviewed'])
    assert.deepEqual(events, [['busy', true], ['saved', 'Reviewed'], ['busy', false]])
    assert.equal(editor.editing.value, false)
    assert.equal(editor.saved.value, true)
    editor.edit()
    editor.draft.value = 'Discard me'
    editor.cancel()
    editor.edit()
    assert.equal(editor.draft.value, 'Original')
    editor.draft.value = '   '
    await editor.save()
    assert.equal(requests.length, 2)
  }
})
