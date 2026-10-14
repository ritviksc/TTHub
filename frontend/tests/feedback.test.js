import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import vm from 'node:vm'
import { ref, computed, reactive, watch, createSSRApp, compile } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { parse, compileScript } from '@vue/compiler-sfc'
import { routeAccess } from '../src/router/access.js'
import { programmeToday, initials } from '../src/utils/sessions.js'
import { NAV, ADMIN_LABEL, HELP_LINK, ROLE_LABELS, isUnder } from '../src/utils/nav.js'
import { FEEDBACK_SPEAKERS, feedbackSpeakerLabel } from '../src/utils/feedback.js'

const { descriptor } = parse(readFileSync(new URL('../src/views/Feedback.vue', import.meta.url), 'utf8'))
const compiled = compileScript(descriptor, { id: 'feedback-test' }).content
  .replace(/^import .*$/gm, '').replace('export default', 'const component =')
const branches = [{ id: 'a', name: 'Harbour' }, { id: 'b', name: 'Valley' }]
const people = [{ id: 'pa', full_name: 'Aroha Example', branch: 'a' }, { id: 'pb', full_name: 'Other Person', branch: 'b' }]
const sessions = [{ id: 'sa', branch: 'a', activity: 'Movement', date: '2026-01-12' }, { id: 'sb', branch: 'b', activity: 'Balance', date: '2026-01-13' }]
const entries = [
  { id: 'fa', branch: 'a', quote: 'Enjoyed movement', source: 'Aroha Example', recordedBy: 'Staff A', consent: true },
  { id: 'internal', branch: 'a', quote: 'Internal observation', source: 'Movement', recordedBy: 'Staff A', consent: false },
  { id: 'fb', branch: 'b', quote: 'Enjoyed balance', source: 'Other Person', recordedBy: 'Staff B', consent: true },
]

async function mount(role = 'instructor', options = {}) {
  const control = { failRead: options.failRead, create: options.create }
  const requests = [], stored = [...entries]
  let opens = 0, closes = 0, branchReads = 0
  const scoped = rows => role === 'super_admin' ? [...rows] : rows.filter(row => row.branch === 'a')
  const read = (name, rows) => {
    if (control.failRead === name) throw Error('Offline')
    return rows
  }
  const context = vm.createContext({
    ref, computed, reactive, watch, onMounted() {}, programmeToday, FEEDBACK_SPEAKERS, feedbackSpeakerLabel,
    auth: reactive({ user: { role, branch: role === 'super_admin' ? null : { id: 'a', name: 'Harbour' } } }),
    listFeedback: async () => read('feedback', scoped(stored)),
    listParticipants: async () => read('people', scoped(people)),
    listSessions: async () => read('sessions', scoped(sessions)),
    listBranches: async () => { branchReads++; assert.equal(role, 'super_admin'); return read('branches', branches) },
    createFeedback: async payload => {
      requests.push(payload)
      if (control.create) return control.create(payload)
      const subject = people.find(person => person.id === payload.participant) || sessions.find(session => session.id === payload.session)
      const saved = { ...payload, id: `saved-${requests.length}`, branch: subject.branch, source: subject.full_name || subject.activity, recordedBy: 'Recording staff' }
      stored.unshift(saved)
      return saved
    },
  })
  vm.runInContext(compiled + '\nthis.component = component', context)
  const page = context.component.setup({}, { expose() {} })
  page.feedbackDialog.value = { showModal() { opens++ }, close() { closes++ } }
  await page.loadFeedback()
  return { page, control, requests, context, get opens() { return opens }, get closes() { return closes }, get branchReads() { return branchReads } }
}

async function render(page) {
  return renderToString(createSSRApp({ setup: () => ({ ...page }), render: compile(descriptor.template.content) }))
}

for (const role of ['instructor', 'branch_manager', 'super_admin']) {
  test(`${role} records participant, session, and combined feedback without assuming a session`, async () => {
    for (const [participant, session] of [['pa', ''], ['', 'sa'], ['pa', 'sa']]) {
      const state = await mount(role)
      state.page.openModal()
      assert.equal(state.page.newEntry.value.session, '')
      if (role === 'super_admin') state.page.newEntry.value.branch = 'a'
      Object.assign(state.page.newEntry.value, { quote: '  A short story.  ', participant, session, recorded_by: 'forged' })
      await state.page.handleAddFeedback()
      assert.equal(state.requests.length, 1)
      assert.equal(state.requests[0].quote, 'A short story.')
      assert.equal(state.requests[0].participant, participant || null)
      assert.equal(state.requests[0].session, session || null)
      assert.equal(state.requests[0].consent, false)
      assert.equal(state.requests[0].speaker, 'unknown')
      assert.equal(state.requests[0].date, programmeToday())
      assert.equal('branch' in state.requests[0], false)
      assert.equal('recorded_by' in state.requests[0], false)
      assert.equal(state.closes, 1)
      await state.page.loadFeedback()
      assert.equal(state.page.feedbackList.value[0].quote, 'A short story.')
      assert.equal(state.branchReads, role === 'super_admin' ? 2 : 0)
    }
  })
}

test('national branch filtering, search, and consent filters work together', async () => {
  const { page } = await mount('super_admin')
  assert.equal(page.filteredFeedback.value.length, 3)
  page.branchFilter.value = 'a'
  assert.equal(page.scopedFeedback.value.length, 2)
  page.activeFilter.value = 'with'
  assert.equal(page.filteredFeedback.value[0].id, 'fa')
  page.activeFilter.value = 'without'
  assert.equal(page.filteredFeedback.value[0].id, 'internal')
  page.branchFilter.value = ''
  page.activeFilter.value = 'all'
  page.search.value = 'valley'
  assert.equal(page.filteredFeedback.value.length, 1)
  assert.equal(page.filteredFeedback.value[0].id, 'fb')
  page.search.value = 'staff a'
  assert.equal(page.filteredFeedback.value.length, 2)
})

test('national recording requires a branch and branch changes clear old subjects but preserve the story', async () => {
  const state = await mount('super_admin')
  state.page.openModal()
  assert.equal(state.page.entryParticipants.value.length, 0)
  state.page.newEntry.value.quote = 'Keep this story.'
  await state.page.handleAddFeedback()
  assert.match(state.page.newEntryError.value, /Choose a branch/)
  assert.equal(state.requests.length, 0)
  state.page.newEntry.value.branch = 'a'
  assert.equal(state.page.entryParticipants.value[0].id, 'pa')
  assert.equal(state.page.entrySessions.value[0].id, 'sa')
  Object.assign(state.page.newEntry.value, { participant: 'pa', session: 'sa', consent: true })
  state.page.newEntry.value.branch = 'b'
  assert.equal(state.page.newEntry.value.participant, '')
  assert.equal(state.page.newEntry.value.session, '')
  assert.equal(state.page.newEntry.value.quote, 'Keep this story.')
  assert.equal(state.page.entryParticipants.value[0].id, 'pb')
  assert.equal(state.page.entrySessions.value[0].id, 'sb')
  state.page.newEntry.value.participant = 'pa'
  await state.page.handleAddFeedback()
  assert.match(state.page.newEntryError.value, /selected branch/)
  assert.equal(state.requests.length, 0)
  state.page.newEntry.value.participant = 'pb'
  await state.page.handleAddFeedback()
  assert.equal(state.requests[0].consent, true)
  assert.equal(state.page.feedbackList.value[0].branch, 'b')
})

test('every failed required read is shown as an error and blocks recording until retry succeeds', async () => {
  for (const role of ['instructor', 'branch_manager', 'super_admin']) {
    for (const failRead of ['feedback', 'people', 'sessions', ...(role === 'super_admin' ? ['branches'] : [])]) {
      const state = await mount(role, { failRead })
      assert.match(state.page.loadError.value, /Could not load feedback/)
      const html = await render(state.page)
      assert.ok(html.includes('Could not load feedback'))
      assert.equal(html.includes('No feedback found'), false)
      state.page.openModal()
      assert.equal(state.opens, 0)
      await state.page.handleAddFeedback()
      assert.equal(state.requests.length, 0)
      state.control.failRead = null
      await state.page.loadFeedback()
      assert.equal(state.page.loadError.value, null)
      state.page.openModal()
      assert.equal(state.opens, 1)
    }
  }
})

test('failed saves retain entered text and consent, and duplicate submissions cannot close a pending form', async () => {
  const state = await mount('instructor', { create: async () => { throw { response: { data: { quote: ['Could not save this entry.'] } } } } })
  state.page.openModal()
  Object.assign(state.page.newEntry.value, { quote: 'Keep my story.', participant: 'pa', consent: true, speaker: 'kaimahi' })
  await state.page.handleAddFeedback()
  assert.equal(state.closes, 0)
  assert.equal(state.page.newEntry.value.quote, 'Keep my story.')
  assert.equal(state.page.newEntry.value.consent, true)
  assert.equal(state.page.newEntry.value.speaker, 'kaimahi')
  assert.equal(state.page.newEntryError.value, 'Could not save this entry.')
  let finish
  state.control.create = () => new Promise(resolve => { finish = resolve })
  const pending = state.page.handleAddFeedback()
  await state.page.handleAddFeedback()
  state.page.closeModal()
  assert.equal(state.requests.length, 2)
  assert.equal(state.closes, 0)
  finish({ id: 'saved', branch: 'a', quote: 'Keep my story.' })
  await pending
  assert.equal(state.closes, 1)
  assert.equal(state.page.saving.value, false)
})

test('feedback captures the speaker type once and displays it after reloading', async () => {
  for (const [speaker, label] of Object.entries(FEEDBACK_SPEAKERS)) {
    const state = await mount('instructor')
    state.page.openModal()
    assert.equal(state.page.newEntry.value.speaker, 'unknown')
    Object.assign(state.page.newEntry.value, { quote: 'A recorded experience.', participant: 'pa', speaker })
    await state.page.handleAddFeedback()
    assert.equal(state.requests[0].speaker, speaker)
    await state.page.loadFeedback()
    assert.equal(state.page.feedbackList.value[0].speaker, speaker)
    const html = await render(state.page)
    assert.ok(html.includes(`value="${speaker}"`))
    assert.ok(html.includes(label))
    assert.ok(html.includes('Who gave this feedback?'))
    state.page.openModal()
    assert.equal(state.page.newEntry.value.speaker, 'unknown')
  }
})

test('empty text and missing subjects are rejected, and branch staff cannot select foreign subjects', async () => {
  const state = await mount('branch_manager')
  state.page.openModal()
  state.page.newEntry.value.quote = '   '
  await state.page.handleAddFeedback()
  assert.match(state.page.newEntryError.value, /Enter a quote/)
  state.page.newEntry.value.quote = 'Story'
  await state.page.handleAddFeedback()
  assert.match(state.page.newEntryError.value, /kaumātua or session/)
  state.page.newEntry.value.participant = 'pb'
  await state.page.handleAddFeedback()
  assert.match(state.page.newEntryError.value, /selected branch/)
  assert.equal(state.requests.length, 0)
})

test('branch controls are rendered only for national staff and can prefill recording from the branch filter', async () => {
  for (const role of ['super_admin', 'branch_manager', 'instructor']) {
    const { page } = await mount(role)
    const html = await render(page)
    assert.equal(html.includes('id="feedback-branch-filter"'), role === 'super_admin')
    assert.equal(html.includes('id="feedback-entry-branch"'), role === 'super_admin')
    assert.ok(html.includes('<dialog'))
    if (role === 'super_admin') {
      page.branchFilter.value = 'b'
      page.openModal()
      assert.equal(page.newEntry.value.branch, 'b')
      assert.equal(page.newEntry.value.session, '')
    }
  }
})

test('all feedback routes use the shared page, keep role access, and national navigation exposes feedback', () => {
  const context = vm.createContext({
    createWebHistory() {}, createRouter: options => ({ ...options, beforeEach() {} }),
    LandingPage: {}, Login: {}, AboutUs: {}, ContactUs: {}, ComingSoon: {}, CreateStaff: {}, UserDetail: {}, StaffDetail: {},
    loadUser() {}, createAccessGuard() {},
  })
  const source = readFileSync(new URL('../src/router/index.js', import.meta.url), 'utf8')
    .replace(/^import .*$/gm, '').replace('export default router', 'this.router = router')
  vm.runInContext(source, context)
  for (const [role, name] of [['super_admin', 'sa-feedback'], ['branch_manager', 'bm-feedback'], ['instructor', 'in-feedback']]) {
    const route = context.router.routes.find(route => route.name === name)
    assert.ok(route.component.toString().includes("@/views/Feedback.vue"))
    assert.equal(routeAccess(route, { role }), true)
    assert.equal(routeAccess(route, null).name, 'home')
    for (const other of ['super_admin', 'branch_manager', 'instructor'].filter(other => other !== role)) {
      assert.equal(routeAccess(route, { role: other }).name, 'not-authorised')
    }
  }
  const { descriptor: nav } = parse(readFileSync(new URL('../src/components/DashboardNav.vue', import.meta.url), 'utf8'))
  const navCode = compileScript(nav, { id: 'feedback-nav-test' }).content
    .replace(/^import .*$/gm, '').replace('export default', 'const component =')
  const navContext = vm.createContext({ computed, ref, watch, onMounted() {}, onUnmounted() {}, initials,
    NAV, ADMIN_LABEL, HELP_LINK, ROLE_LABELS, isUnder, NavMenu: {},
    auth: { user: { role: 'super_admin' } }, clearUser() {}, logout() {}, ThemeSwitcher: {}, logoSrc: '',
    useRouter: () => ({}), useRoute: () => ({ fullPath: '/' }) })
  vm.runInContext(navCode + '\nthis.component = component', navContext)
  const navigation = navContext.component.setup({}, { expose() {} })
  assert.ok(navigation.navItems.value.some(item => item.label === 'Feedback' && item.to === '/super-admin/feedback'))
})
