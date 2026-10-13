const DASHBOARDS = {
  super_admin: 'sa-users',
  branch_manager: 'bm-overview',
  instructor: 'in-home',
}

export function dashboardRoute(role) {
  return { name: DASHBOARDS[role] ?? 'not-authorised' }
}

export function routeAccess(to, user) {
  const unknown = to.name === 'unknown-route' || to.matched?.length === 0
  if (!user) {
    return to.meta?.requiresAuth || unknown ? { name: 'home', replace: true } : true
  }
  if (to.name === 'home' || to.name === 'login') {
    return { ...dashboardRoute(user.role), replace: true }
  }
  if (unknown || (to.meta?.roles && !to.meta.roles.includes(user.role))) {
    return { name: 'not-authorised', replace: true }
  }
  const participantRoute = { super_admin: 'sa-participant-detail', branch_manager: 'bm-participant-detail', instructor: 'in-participant-detail' }[user.role]
  if (to.name === 'participant-detail' && participantRoute) {
    return { name: participantRoute, params: to.params, replace: true }
  }
  return true
}

export function createAccessGuard(loadUser) {
  return async to => {
    // Recheck the server session so an expired login cannot leave a stale signed-in bar.
    const user = await loadUser()
    return routeAccess(to, user)
  }
}
