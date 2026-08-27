import { reactive } from 'vue'
import { fetchMe } from '@/apis.js'

// Who is signed in. Shared so the navbar and the router guard read the same thing.
export const auth = reactive({
  user: null,     // { email, role, first_name, last_name, branch: { id, name } | null }
  loaded: false,  // has a session check finished at least once?
})

// TEMPORARY: which dashboard tab is showing. Goes away once the tabs become
// real routes and router-link-active tracks this for us.
export const ui = reactive({
  activeNav: '',
})

export async function loadUser() {
  try {
    auth.user = await fetchMe()
  } catch {
    auth.user = null
  }
  auth.loaded = true
  return auth.user
}

export function clearUser() {
  auth.user = null
}
