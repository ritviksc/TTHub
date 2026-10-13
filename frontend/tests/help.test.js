import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  buildHelpTree, chatHistory, helpError, parseNdjson, siblings, stripCitations, treeRows,
} from '../src/utils/help.js'
import { routeAccess } from '../src/router/access.js'

const article = (slug, title, audience, section) => ({
  slug, title, section, audience,
  audience_label: { general: 'General', kaimahi: 'Kaimahi', 'branch-manager': 'Branch Manager' }[audience],
})
const articles = [
  article('using-help', 'Using this Help page', 'general', 'Getting started'),
  article('documents', 'Storing documents', 'general', 'Documents'),
  article('kaimahi-sessions', 'Creating a session', 'kaimahi', 'Sessions'),
  article('kaimahi-attendance', 'Taking attendance', 'kaimahi', 'Sessions'),
  article('bm-reports', 'Attendance reports', 'branch-manager', 'Reporting'),
]

test('buildHelpTree groups articles into audience then section folders, keeping order', () => {
  const tree = buildHelpTree(articles)
  assert.deepEqual(tree.map(node => node.label), ['General', 'Kaimahi', 'Branch Manager'])
  assert.deepEqual(tree[0].children.map(node => node.label), ['Getting started', 'Documents'])
  assert.deepEqual(tree[1].children[0].children.map(node => node.slug), ['kaimahi-sessions', 'kaimahi-attendance'])
})

test('with nothing opened, only the closed role folders are shown', () => {
  const rows = treeRows(buildHelpTree(articles), new Set())
  assert.deepEqual(rows.map(row => [row.node.label, row.open]),
    [['General', false], ['Kaimahi', false], ['Branch Manager', false]])
})

test('opening a role folder shows its sections; opening a section shows its articles', () => {
  const tree = buildHelpTree(articles)
  const labels = expanded => treeRows(tree, new Set(expanded)).map(row => row.node.label)
  assert.deepEqual(labels(['a:kaimahi']), ['General', 'Kaimahi', 'Sessions', 'Branch Manager'])
  assert.deepEqual(labels(['a:kaimahi', 's:kaimahi/Sessions']),
    ['General', 'Kaimahi', 'Sessions', 'Creating a session', 'Taking attendance', 'Branch Manager'])
  assert.deepEqual(treeRows(tree, new Set(['a:kaimahi', 's:kaimahi/Sessions'])).slice(1, 4).map(row => row.depth), [0, 1, 2])
})

test('searching shows only matching articles, with their folders opened', () => {
  const tree = buildHelpTree(articles)
  const rows = treeRows(tree, new Set(), 'ATTENDANCE')
  assert.deepEqual(rows.map(row => row.node.label),
    ['Kaimahi', 'Sessions', 'Taking attendance', 'Branch Manager', 'Reporting', 'Attendance reports'])
  assert.deepEqual(treeRows(tree, new Set(), 'nothing like this'), [])
})

test('siblings finds the previous and next article within the same section', () => {
  assert.deepEqual(siblings(articles, 'kaimahi-sessions'), { previous: null, next: articles[3] })
  assert.deepEqual(siblings(articles, 'kaimahi-attendance'), { previous: articles[2], next: null })
  assert.deepEqual(siblings(articles, 'documents'), { previous: null, next: null })
  assert.deepEqual(siblings(articles, 'missing'), { previous: null, next: null })
})

test('stripCitations hides [slug] markers but keeps Markdown links', () => {
  assert.equal(stripCitations('Open Documents [documents]. Then upload [documents][acc-reports].'),
    'Open Documents. Then upload.')
  assert.equal(stripCitations('See [the guide](/testing-guides/tug.pdf).'), 'See [the guide](/testing-guides/tug.pdf).')
})

test('while streaming, a half-written citation at the end is hidden too', () => {
  assert.equal(stripCitations('Open Documents [docum', { streaming: true }), 'Open Documents')
  assert.equal(stripCitations('Open Documents [docum'), 'Open Documents [docum')
})

test('parseNdjson returns whole lines and keeps a partial last line for later', () => {
  const first = parseNdjson('{"type":"delta","text":"Kia "}\n{"type":"del')
  assert.deepEqual(first.events, [{ type: 'delta', text: 'Kia ' }])
  const second = parseNdjson(first.rest + 'ta","text":"ora"}\n\n')
  assert.deepEqual(second.events, [{ type: 'delta', text: 'ora' }])
  assert.equal(second.rest, '')
})

test('chatHistory leaves out stopped and failed turns and keeps the most recent six', () => {
  const messages = [
    { role: 'user', content: 'Q1', omit: true },
    { role: 'assistant', content: 'Sorry', omit: true, status: 'error' },
    ...Array.from({ length: 7 }, (_, index) => ({ role: index % 2 ? 'assistant' : 'user', content: `T${index}`, id: index })),
  ]
  const history = chatHistory(messages)
  assert.equal(history.length, 6)
  assert.deepEqual(history[0], { role: 'assistant', content: 'T1' })
  assert.ok(history.every(turn => Object.keys(turn).length === 2))
})

test('helpError explains throttling, outages and timeouts', () => {
  assert.match(helpError({ response: { status: 429 } }), /wait/)
  assert.equal(helpError({ response: { status: 503, data: { detail: 'Down.' } } }), 'Down.')
  assert.match(helpError({ code: 'ETIMEDOUT' }), /too long/)
  assert.match(helpError(new Error('offline')), /Could not reach/)
})

test('every staff role can open the Help page', () => {
  const to = { name: 'help', matched: [{}], meta: { requiresAuth: true, roles: ['super_admin', 'branch_manager', 'instructor'] } }
  for (const role of ['super_admin', 'branch_manager', 'instructor']) {
    assert.equal(routeAccess(to, { role }), true)
  }
  assert.deepEqual(routeAccess(to, null), { name: 'home', replace: true })
})
