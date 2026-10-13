import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createAccessGuard, dashboardRoute, routeAccess } from '../src/router/access.js'

const Page = { render: () => null }
const destinations = { super_admin: 'sa-users', branch_manager: 'bm-overview', instructor: 'in-home' }
function makeRouter(session) {
  const routes = [
    { path: '/', name: 'home', component: Page },
    { path: '/login', name: 'login', component: Page },
    { path: '/about', name: 'about-us', component: Page },
    { path: '/not-authorised', name: 'not-authorised', component: Page, meta: { requiresAuth: true } },
    ...Object.entries(destinations).map(([role, name]) => ({
      path: `/${name}`, name, component: Page, meta: { requiresAuth: true, roles: [role] },
    })),
    { path: '/:pathMatch(.*)*', name: 'unknown-route', component: Page },
  ]
  const router = createRouter({ history: createMemoryHistory(), routes })
  router.beforeEach(createAccessGuard(async () => session.user))
  return router
}

for (const [role, destination] of Object.entries(destinations)) {
  test(`${role} lands on its own dashboard from home and login`, async () => {
    const router = makeRouter({ user: { role } })
    for (const path of ['/', '/login']) {
      await router.push(path)
      assert.equal(router.currentRoute.value.name, destination)
    }
    assert.equal(dashboardRoute(role).name, destination)
  })

  test(`${role} gets an access-denied page for other dashboards`, async () => {
    const router = makeRouter({ user: { role } })
    for (const [otherRole, name] of Object.entries(destinations)) {
      await router.push({ name })
      assert.equal(router.currentRoute.value.name, otherRole === role ? name : 'not-authorised')
    }
    await router.push('/missing-page')
    assert.equal(router.currentRoute.value.name, 'not-authorised')
    await router.push(dashboardRoute(role))
    assert.equal(router.currentRoute.value.name, destination)
  })
}

test('signed-out protected and unknown URLs go home; login and public pages remain available', async () => {
  const router = makeRouter({ user: null })
  for (const path of ['/sa-users', '/bm-overview', '/in-home', '/not-authorised', '/missing-page']) {
    await router.push(path)
    assert.equal(router.currentRoute.value.name, 'home')
  }
  await router.push('/login')
  assert.equal(router.currentRoute.value.name, 'login')
  await router.push('/about')
  assert.equal(router.currentRoute.value.name, 'about-us')
})

test('an expired server session redirects home on the next navigation', async () => {
  const session = { user: { role: 'instructor' } }
  const router = makeRouter(session)
  await router.push('/in-home')
  session.user = null
  await router.push('/sa-users')
  assert.equal(router.currentRoute.value.name, 'home')
})

test('an unrecognised role does not create a redirect loop', async () => {
  const router = makeRouter({ user: { role: 'unknown' } })
  await router.push('/')
  assert.equal(router.currentRoute.value.name, 'not-authorised')
})


test('participant bookmarks open each role’s participant details after access checks', () => {
  const to = { name: 'participant-detail', params: { id: 'participant-id' }, meta: { requiresAuth: true, roles: ['super_admin', 'instructor', 'branch_manager'] } }
  for (const [role, name] of [['super_admin', 'sa-participant-detail'], ['branch_manager', 'bm-participant-detail'], ['instructor', 'in-participant-detail']]) {
    assert.deepEqual(routeAccess(to, { role }), { name, params: to.params, replace: true })
  }
  assert.deepEqual(routeAccess(to, null), { name: 'home', replace: true })
})
