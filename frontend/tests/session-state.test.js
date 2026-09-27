import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createSessionActions } from '../src/utils/sessionState.js'

function deferred() {
  let resolve, reject
  const promise = new Promise((yes, no) => { resolve = yes; reject = no })
  return { promise, resolve, reject }
}
test('a session check completing after logout cannot restore the old identity', async () => {
  const response = deferred()
  const state = { user: { role: 'super_admin' }, loaded: true }
  const actions = createSessionActions(state, () => response.promise)
  const pending = actions.loadUser()
  actions.clearUser()
  response.resolve({ role: 'super_admin' })
  assert.equal(await pending, null)
  assert.equal(state.user, null)
})
test('an older success cannot overwrite a newer expired-session check', async () => {
  const old = deferred(), latest = deferred()
  let calls = 0
  const state = { user: null, loaded: false }
  const actions = createSessionActions(state, () => calls++ ? latest.promise : old.promise)
  const first = actions.loadUser(), second = actions.loadUser()
  latest.reject(new Error('Session expired'))
  await second
  old.resolve({ role: 'super_admin' })
  await first
  assert.equal(state.user, null)
  assert.equal(state.loaded, true)
})
test('an older failed check cannot erase a newly verified identity', async () => {
  const old = deferred(), latest = deferred()
  let calls = 0
  const state = { user: null, loaded: false }
  const actions = createSessionActions(state, () => calls++ ? latest.promise : old.promise)
  const first = actions.loadUser(), second = actions.loadUser()
  const user = { role: 'instructor' }
  latest.resolve(user)
  await second
  old.reject(new Error('Old failure'))
  assert.equal(await first, user)
  assert.equal(state.user, user)
})
