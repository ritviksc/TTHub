import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, computed, reactive } from 'vue'
import { parse, compileScript } from '@vue/compiler-sfc'
import { SESSION_PERIODS, formatSessionDate, isInPeriod } from '../src/utils/sessions.js'

const { descriptor } = parse(readFileSync(new URL('../src/views/Instructor/Sessions.vue', import.meta.url), 'utf8'))
const compiled = compileScript(descriptor, { id: 'session-creation-test' }).content
  .replace(/^import .*$/gm, '').replace('export default', 'const component =')

for (const [role, prefix] of [['instructor', 'in'], ['branch_manager', 'bm']]) {
  test(`${role} can open session creation and navigate to the created session`, () => {
    const destinations = []
    const context = vm.createContext({
      ref, computed, onMounted() {}, RouterLink: {}, CreateSessionModal: {}, SessionCalendar: {},
      SESSION_PERIODS, formatSessionDate, isInPeriod, listSessions: async () => [],
      auth: reactive({ user: { role } }),
      useRouter: () => ({ push: route => destinations.push(route) }),
    })
    vm.runInContext(compiled + '\nthis.component = component', context)
    const page = context.component.setup({}, { expose() {} })
    assert.equal(page.canCreate.value, true)
    page.openCreateModal('2026-10-13')
    assert.equal(page.showCreate.value, true)
    assert.equal(page.createInitialDate.value, '2026-10-13')
    page.onCreated({ id: 'new-session' })
    assert.equal(page.showCreate.value, false)
    assert.equal(page.sessions.value[0].id, 'new-session')
    assert.equal(destinations[0].name, `${prefix}-session-detail`)
    assert.equal(destinations[0].params.id, 'new-session')
  })
}
