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
  ['getStaff', ['staff-id'], '/auth/staff/staff-id/'],
  ['getParticipantAttendance', ['participant-id'], '/participants/participant-id/attendance/'],
  ['downloadGpDocument', ['participant-id'], '/participants/participant-id/gp-document/'],
  ['downloadDocument', ['document-id'], '/documents/document-id/download/'],
  ['listDocuments', [{ branch: 'branch-id' }], '/documents/'],
  ['listFolders', [{ branch: 'branch-id' }], '/folders/'],
  ['getPhysicalReport', [{ start_date: '2026-01-01', end_date: '2026-03-31' }], '/reporting/physical/'],
  ['getPhysicalAnalysisJob', ['job-id'], '/reporting/physical/jobs/job-id/'],
  ['listPhysicalAssessments', ['participant-id'], '/physical-tests/participants/participant-id/'],
  ['getPhysicalAssessment', ['assessment-id'], '/physical-tests/assessment-id/'],
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
  ['analysePhysicalReport', [{ start_date: '2026-01-01', end_date: '2026-03-31' }]],
  ['startPhysicalAssessment', ['participant-id']],
  ['savePhysicalResults', ['assessment-id', 'tug', [], 0]],
  ['updatePhysicalAssessmentDate', ['assessment-id', '2026-01-01', 0]],
  ['completePhysicalAssessment', ['assessment-id', 0]],
  ['createSession', [{ activity: 'Class' }]],
  ['reactivateStaff', ['staff-id']],
  ['reactivateParticipant', ['participant-id']],
  ['updateAttendance', ['session-id', 'record-id', { status: 'present' }]],
  ['deleteSession', ['session-id']],
  ['analyseAttendanceReport', [{ start_date: '2026-01-01', end_date: '2026-03-31' }]],
  ['deleteDocument', ['document-id']],
  ['updateDocument', ['document-id', { name: 'Renamed.pdf' }]],
  ['createFolder', [{ name: 'Policies' }]],
  ['updateFolder', ['folder-id', { name: 'Renamed' }]],
  ['deleteFolder', ['folder-id']],
]) {
  test(`${name} does not retry a timed-out write`, async () => {
    let attempts = 0
    const failure = new axios.AxiosError('Timed out', api.TIMEOUT_ERROR)
    respond = async () => { attempts++; throw failure }
    await assert.rejects(api[name](...args), error => error === failure)
    assert.equal(attempts, 1)
  })
}

for (const [name, url] of [
  ['reactivateStaff', '/auth/staff/record-id/reactivate/'],
  ['reactivateParticipant', '/participants/record-id/reactivate/'],
]) {
  test(`${name} posts to the dedicated reactivation endpoint and returns its status`, async () => {
    respond = async config => {
      assert.equal(config.method, 'post')
      assert.equal(config.url, url)
      return { data: { id: 'record-id', is_active: true }, status: 200, headers: {}, config }
    }
    assert.deepEqual(await api[name]('record-id'), { id: 'record-id', is_active: true })
  })
}

test('uploadDocument posts to the documents endpoint with a longer timeout', async () => {
  const formData = new FormData()
  formData.append('file', new Blob(['x']), 'notes.pdf')
  respond = async config => {
    assert.equal(config.method, 'post')
    assert.equal(config.url, '/documents/')
    assert.equal(config.timeout, 60000)
    return { data: { id: 'doc-id' }, status: 201, headers: {}, config }
  }
  const result = await api.uploadDocument(formData)
  assert.deepEqual(result, { id: 'doc-id' })
})

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

test('staff promotion clears the hidden branch without mutating the edit form', async () => {
  const payload = { role: 'super_admin', branch: 'old-branch-id' }
  respond = async config => {
    assert.equal(config.method, 'patch')
    assert.equal(JSON.parse(config.data).branch, null)
    return { data: { id: 'staff-id' }, status: 200, headers: {}, config }
  }
  await api.updateStaff('staff-id', payload)
  assert.equal(payload.branch, 'old-branch-id')
})
