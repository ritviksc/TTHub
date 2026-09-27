// Ignore checks started before logout or a newer check; they must not restore stale identity.
export function createSessionActions(state, fetchUser) {
  let revision = 0
  async function loadUser() {
    const requestRevision = ++revision
    let user = null
    try { user = await fetchUser() } catch { /* No verified session. */ }
    if (requestRevision === revision) {
      state.user = user
      state.loaded = true
    }
    return state.user
  }
  function clearUser() {
    revision++
    state.user = null
    state.loaded = true
  }
  return { loadUser, clearUser }
}
