import assert from 'node:assert/strict'
import { test } from 'node:test'
import { childrenOf, folderAndDescendantIds, folderPath, folderTrail, groupBranchesByRegion, pushRecent } from '../src/utils/documents.js'

const folders = [
  { id: 'policies', name: 'Policies', parent: null },
  { id: 'hs', name: 'H&S', parent: 'policies' },
  { id: 'forms', name: 'Forms', parent: 'hs' },
  { id: 'terms', name: 'Term plans', parent: null },
]

test('childrenOf lists only direct children, sorted by name', () => {
  assert.deepEqual(childrenOf(folders, null).map(f => f.id), ['policies', 'terms'])
  assert.deepEqual(childrenOf(folders, 'policies').map(f => f.id), ['hs'])
  assert.deepEqual(childrenOf(folders, 'hs').map(f => f.id), ['forms'])
})

test('folderTrail walks from the root down to the given folder', () => {
  assert.deepEqual(folderTrail(folders, null), [])
  assert.deepEqual(folderTrail(folders, 'hs').map(f => f.id), ['policies', 'hs'])
  assert.deepEqual(folderTrail(folders, 'forms').map(f => f.id), ['policies', 'hs', 'forms'])
})

test('folderPath renders the trail as a breadcrumb string', () => {
  assert.equal(folderPath(folders, null), '')
  assert.equal(folderPath(folders, 'forms'), 'Policies › H&S › Forms')
})

test('folderAndDescendantIds includes the folder itself and every nested subfolder', () => {
  assert.deepEqual(folderAndDescendantIds(folders, 'policies'), new Set(['policies', 'hs', 'forms']))
  assert.deepEqual(folderAndDescendantIds(folders, 'forms'), new Set(['forms']))
  assert.deepEqual(folderAndDescendantIds(folders, 'terms'), new Set(['terms']))
})

test('groupBranchesByRegion sorts regions and names, with unassigned branches last', () => {
  const groups = groupBranchesByRegion([
    { key: 'd', label: 'Dunedin', region: 'Otago' },
    { key: 'wn', label: 'Wellington North', region: 'Wellington' },
    { key: 'x', label: 'Pop-up', region: '' },
    { key: 'wc', label: 'Wellington Central', region: 'Wellington' },
    { key: 'q', label: 'Queenstown', region: 'Otago' },
  ])
  assert.deepEqual(groups.map(g => g.title), ['Otago', 'Wellington', 'Other'])
  assert.deepEqual(groups[0].branches.map(b => b.key), ['d', 'q'])
  assert.deepEqual(groups[1].branches.map(b => b.key), ['wc', 'wn'])
})

test('pushRecent moves a key to the front without duplicates and caps the list', () => {
  assert.deepEqual(pushRecent([], 'a'), ['a'])
  assert.deepEqual(pushRecent(['a', 'b', 'c'], 'c'), ['c', 'a', 'b'])
  assert.deepEqual(pushRecent(['a', 'b', 'c'], 'd', 3), ['d', 'a', 'b'])
})
