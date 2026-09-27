function wait(ms, signal) {
  return new Promise((resolve, reject) => {
    const cancel = () => {
      clearTimeout(timer)
      reject(new DOMException('Polling stopped', 'AbortError'))
    }
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', cancel)
      resolve()
    }, ms)
    if (signal?.aborted) cancel()
    else signal?.addEventListener('abort', cancel, { once: true })
  })
}

// Poll sequentially: slow status requests must not overlap or repeat generation.
export async function waitForAnalysis(fetchStatus, {
  signal, onStatus = () => {}, intervalMs = 1500, timeoutMs = 960000,
} = {}) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (signal?.aborted) throw new DOMException('Polling stopped', 'AbortError')
    const job = await fetchStatus()
    if (signal?.aborted) throw new DOMException('Polling stopped', 'AbortError')
    onStatus(job.status)
    if (job.status === 'succeeded') return job
    if (job.status === 'failed') throw new Error(job.detail || 'Analysis failed. Please try again.')
    if (!['queued', 'running'].includes(job.status)) throw new Error('Unexpected analysis status.')
    await wait(intervalMs, signal)
  }
  throw new Error('Analysis is taking too long. Please try again later.')
}
