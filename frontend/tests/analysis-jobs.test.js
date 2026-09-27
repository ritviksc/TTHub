import assert from 'node:assert/strict'
import { test } from 'node:test'
import { waitForAnalysis } from '../src/utils/analysisJobs.js'

test('polls queued and running jobs before returning the result', async () => {
  const replies = [{ status: 'queued' }, { status: 'running' }, { status: 'succeeded', narrative: 'Report' }]
  const seen = []
  const result = await waitForAnalysis(async () => replies.shift(), {
    intervalMs: 0, onStatus: status => seen.push(status),
  })
  assert.equal(result.narrative, 'Report')
  assert.deepEqual(seen, ['queued', 'running', 'succeeded'])
})

test('failed jobs propagate their safe error message', async () => {
  await assert.rejects(waitForAnalysis(async () => ({ status: 'failed', detail: 'Provider unavailable' })), /Provider unavailable/)
})

test('cancelling polling prevents further status requests', async () => {
  const controller = new AbortController()
  let calls = 0
  await assert.rejects(waitForAnalysis(async () => {
    calls++
    controller.abort()
    return { status: 'running' }
  }, { signal: controller.signal }), { name: 'AbortError' })
  assert.equal(calls, 1)
})

test('a bounded wait reports a timeout', async () => {
  await assert.rejects(waitForAnalysis(() => assert.fail('Must not fetch'), { timeoutMs: 0 }), /too long/)
})
