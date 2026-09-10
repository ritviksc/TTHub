import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '@/views/LandingPage.vue'
import Login from '@/views/Login.vue'
import AboutUs from '@/views/AboutUs.vue'
import ContactUs from '@/views/ContactUs.vue'
import ComingSoon from '@/views/ComingSoon.vue'
import CreateStaff from '@/views/SuperAdmin/CreateStaff.vue'
import CreateInstructor from '@/views/BranchManager/CreateInstructor.vue'
import { auth, loadUser } from '@/stores/auth.js'

// Not-yet-built pages all share one placeholder; meta.title is what it renders.
const comingSoon = (path, name, title, roles) => ({
    path, name, component: ComingSoon,
    meta: { requiresAuth: true, roles, title },
})

const SA = ['super_admin']
const BM = ['branch_manager']
const IN = ['instructor']

const router = createRouter({
    history: createWebHistory(),
    routes: [
        /* ---- public ---- */
        { path: '/', name: 'home', component: LandingPage },
        { path: '/about', name: 'about-us', component: AboutUs },
        { path: '/contact', name: 'contact-us', component: ContactUs },
        { path: '/login', name: 'login', component: Login },

        /* ---- super admin ---- */
        { path: '/super-admin', redirect: '/super-admin/users' },
        { path: '/super-admin/dashboard', redirect: '/super-admin/users' },
        {
            path: '/super-admin/users', name: 'sa-users',
            component: () => import('@/views/SuperAdmin/Users.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
        {
            path: '/super-admin/administration', name: 'sa-administration',
            component: () => import('@/views/SuperAdmin/Administration.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
        comingSoon('/super-admin/overview', 'sa-overview', 'National overview', SA),
        {
            path: '/super-admin/branches', name: 'sa-branches',
            component: () => import('@/views/SuperAdmin/Branches.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
        {
            path: '/super-admin/branches/:id', name: 'sa-branch-detail',
            component: () => import('@/views/SuperAdmin/BranchDetail.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
        {
            path: '/super-admin/participants', name: 'sa-participants',
            component: () => import('@/views/SuperAdmin/Participants.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
        comingSoon('/super-admin/reporting', 'sa-reporting', 'Reporting', SA),
        {
            path: '/super-admin/create-staff', name: 'create-staff', component: CreateStaff,
            meta: { requiresAuth: true, roles: SA },
        },

        /* ---- branch manager ---- */
        { path: '/branch-manager', redirect: '/branch-manager/overview' },
        { path: '/branch-manager/dashboard', redirect: '/branch-manager/overview' },
        {
            path: '/branch-manager/overview', name: 'bm-overview',
            component: () => import('@/views/BranchManager/Overview.vue'),
            meta: { requiresAuth: true, roles: BM },
        },
        comingSoon('/branch-manager/sessions', 'bm-sessions', 'Sessions', BM),
        comingSoon('/branch-manager/participants', 'bm-participants', 'Participants', BM),
        comingSoon('/branch-manager/instructors', 'bm-instructors', 'Instructors', BM),
        comingSoon('/branch-manager/feedback', 'bm-feedback', 'Feedback', BM),
        comingSoon('/branch-manager/reports', 'bm-reports', 'Reports', BM),
        {
            path: '/branch-manager/create-instructor', name: 'create-instructor', component: CreateInstructor,
            meta: { requiresAuth: true, roles: BM },
        },

        /* ---- instructor ---- */
        { path: '/instructor', redirect: '/instructor/home' },
        { path: '/instructor/dashboard', redirect: '/instructor/home' },
        {
            path: '/instructor/home', name: 'in-home',
            component: () => import('@/views/Instructor/Home.vue'),
            meta: { requiresAuth: true, roles: IN },
        },
        {
            path: '/instructor/sessions', name: 'in-sessions',
            component: () => import('@/views/Instructor/Sessions.vue'),
            meta: { requiresAuth: true, roles: IN },
        },
        comingSoon('/instructor/participants', 'in-participants', 'Participants', IN),
        comingSoon('/instructor/feedback', 'in-feedback', 'Feedback', IN),

        {
            path: '/participants/:id', name: 'participant-detail',
            component: () => import('@/views/ParticipantConsent.vue'),
            meta: { requiresAuth: true, roles: SA, BM, IN},
        },
    ]
})

router.beforeEach(async (to) => {
    if (!to.meta.requiresAuth) return true

    // main.js resolves the session before mount, so this is normally cached.
    const user = auth.user ?? await loadUser()
    if (!user) return '/login'

    if (to.meta.roles && !to.meta.roles.includes(user.role)) return '/login'
    return true
})

export default router
