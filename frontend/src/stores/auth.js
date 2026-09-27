import { reactive } from 'vue'
import { fetchMe } from '@/apis.js'
import { createSessionActions } from '@/utils/sessionState.js'

// Who is signed in. Shared so the navbar and the router guard read the same thing.
export const auth = reactive({
  user: null,     // { email, role, first_name, last_name, branch: { id, name } | null }
  loaded: false,  // has a session check finished at least once?
})

export const { loadUser, clearUser } = createSessionActions(auth, fetchMe)
