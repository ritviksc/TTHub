import assert from 'node:assert/strict'
import { after, beforeEach, test } from 'node:test'
import axios from 'axios'

// Replace only the transport: exercise the actual exported API functions with no server.
const originalAdapter = axios.defaults.adapter
let respond
axios.defaults.adapter = config => respond(config)
const api = await import('../src/apis.js')
after(() => { axios.defaults.adapter = originalAdapter })
beforeEach(() => { respond = () => { throw new Error('Unexpected request') } })

const reads = [
  ['getAttendanceAnalysisJob', ['job-id'], '/reporting/attendance/jobs/job-id/'],
  ['fetchCsrfCookie', [], '/auth/csrf/'],
  ['fetchMe', [], '/auth/me/'],
  ['listStaff', [], '/auth/staff/list/'],
  ['listBranches', [{ search: 'Dunedin' }], '/branches/'],
  ['getBranch', ['branch-id'], '/branches/branch-id/'],
  ['listParticipants', [{ is_active: true }], '/participants/'],
  ['getParticipant', ['participant-id'], '/participants/participant-id/'],
  ['listSessions', [], '/sessions/'],
  ['getSession', ['session-id'], '/sessions/session-id/'],
  ['getAttendanceReport', [{ start_date: '2026-01-01', end_date: '2026-03-31' }], '/reporting/attendance/'],
]

for (const [name, args, url] of reads) {
  test(`${name} retries a timeout and preserves its request`, async t => {
    t.mock.method(Math, 'random', () => 0)
    let attempts = 0
    respond = async config => {
      attempts++
      assert.equal(config.method, 'get')
      assert.equal(config.url, url)
      if (typeof args[0] === 'object') assert.deepEqual(config.params, args[0])
      if (attempts === 1) throw new axios.AxiosError('Timed out', api.TIMEOUT_ERROR)
      return { data: { ok: true }, status: 200, headers: {}, config }
    }
    const result = await api[name](...args)
    if (name !== 'fetchCsrfCookie') assert.deepEqual(result, { ok: true })
    assert.equal(attempts, 2)
  })
}

test('GET stops after three attempts and preserves the final error', async t => {
  t.mock.method(Math, 'random', () => 0)
  let attempts = 0
  const failure = new axios.AxiosError('Timed out', api.TIMEOUT_ERROR)
  respond = async () => { attempts++; throw failure }
  await assert.rejects(api.fetchMe(), error => error === failure)
  assert.equal(attempts, 3)
})

test('GET permission errors reach the caller without retrying', async () => {
  let attempts = 0
  const failure = new axios.AxiosError('Forbidden', 'ERR_BAD_REQUEST', undefined, undefined, {
    status: 403, data: { detail: 'Permission denied' }, headers: {},
  })
  respond = async () => { attempts++; throw failure }
  await assert.rejects(api.getSession('session-id'), error =>
    error === failure && error.response.data.detail === 'Permission denied')
  assert.equal(attempts, 1)
})

for (const [name, args] of [
  ['createSession', [{ activity: 'Class' }]],
  ['updateAttendance', ['session-id', 'record-id', { status: 'present' }]],
  ['deleteSession', ['session-id']],
  ['analyseAttendanceReport', [{ start_date: '2026-01-01', end_date: '2026-03-31' }]],
]) {
  test(`${name} does not retry a timed-out write`, async () => {
    let attempts = 0
    const failure = new axios.AxiosError('Timed out', api.TIMEOUT_ERROR)
    respond = async () => { attempts++; throw failure }
    await assert.rejects(api[name](...args), error => error === failure)
    assert.equal(attempts, 1)
  })
}

test('invalid retry limits fail instead of silently returning undefined', async () => {
  for (const limit of [0, -1, 1.5]) {
    await assert.rejects(api.withRetry(limit, () => assert.fail('Must not run')), RangeError)
  }
})

test('super-admin creation sends no branch without mutating the form', async () => {
  const payload = { email: 'admin@example.com', role: 'super_admin', branch: '' }
  respond = async config => {
    assert.equal(JSON.parse(config.data).branch, null)
    return { data: { id: 'new-admin' }, status: 201, headers: {}, config }
  }
  await api.createStaffAccount(payload)
  assert.equal(payload.branch, '')
})

test('empty branch selections are omitted so the server can validate or assign the branch', async () => {
  respond = async config => {
    assert.equal(Object.hasOwn(JSON.parse(config.data), 'branch'), false)
    return { data: { id: 'new-instructor' }, status: 201, headers: {}, config }
  }
  await api.createStaffAccount({ role: 'instructor', branch: '' })
})
