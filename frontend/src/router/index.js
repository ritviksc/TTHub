import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '@/views/LandingPage.vue'
import Login from '@/views/Login.vue'
import AboutUs from '@/views/AboutUs.vue'
import ContactUs from '@/views/ContactUs.vue'
import ComingSoon from '@/views/ComingSoon.vue'
import CreateStaff from '@/views/SuperAdmin/CreateStaff.vue'
import { loadUser } from '@/stores/auth.js'
import UserDetail from '@/views/SuperAdmin/UserDetail.vue'
import StaffDetail from '@/views/StaffDetail.vue'
import { createAccessGuard } from './access.js'

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
        {
            path: '/branch-manager/administration', name: 'bm-administration',
            component: () => import('@/views/BranchManager/Administration.vue'),
            meta: { requiresAuth: true, roles: BM },
        },
        {
            path: '/branch-manager/administration/audit', name: 'bm-audit-log',
            component: () => import('@/views/BranchManager/AuditLog.vue'),
            meta: { requiresAuth: true, roles: BM },
        },
        {
            path: '/super-admin/administration/audit', name: 'sa-audit-log',
            component: () => import('@/views/SuperAdmin/AuditLog.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
        {
            path: '/super-admin/physical-assessments/:id', name: 'sa-physical-assessment',
            component: () => import('@/views/SuperAdmin/PhysicalAssessment.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
        {
            path: '/branch-manager/physical-assessments/:id', name: 'bm-physical-assessment',
            component: () => import('@/views/BranchManager/PhysicalAssessment.vue'),
            meta: { requiresAuth: true, roles: BM },
        },
        {
            path: '/instructor/physical-assessments/:id', name: 'in-physical-assessment',
            component: () => import('@/views/Instructor/PhysicalAssessment.vue'),
            meta: { requiresAuth: true, roles: IN },
        },
        { path: '/super-admin/reporting/attendance', name: 'sa-attendance-report',
          component: () => import('@/views/SuperAdmin/AttendanceReporting.vue'),
          meta: { requiresAuth: true, roles: SA } },
        ...['attendance', 'physical', 'acc'].map(reportType => ({
          path: `/super-admin/reporting/${reportType}/history/:id?`, name: `sa-${reportType}-history`,
          component: () => import('@/views/SuperAdmin/ReportHistory.vue'),
          props: { reportType }, meta: { requiresAuth: true, roles: SA },
        })),
        { path: '/super-admin/reporting/physical', name: 'sa-physical-report',
          component: () => import('@/views/SuperAdmin/PhysicalReporting.vue'),
          meta: { requiresAuth: true, roles: SA } },
        { path: '/branch-manager/reports/attendance', name: 'bm-attendance-report',
          component: () => import('@/views/BranchManager/AttendanceReporting.vue'),
          meta: { requiresAuth: true, roles: BM } },
        { path: '/branch-manager/reports/physical', name: 'bm-physical-report',
          component: () => import('@/views/BranchManager/PhysicalReporting.vue'),
          meta: { requiresAuth: true, roles: BM } },
        { path: '/super-admin/reporting/acc', name: 'sa-acc-report',
          component: () => import('@/views/SuperAdmin/ACCReporting.vue'),
          meta: { requiresAuth: true, roles: SA } },
        /* ---- public ---- */
        { path: '/', name: 'home', component: LandingPage },
        { path: '/about', name: 'about-us', component: AboutUs },
        { path: '/contact', name: 'contact-us', component: ContactUs },
        { path: '/login', name: 'login', component: Login },
        {
            path: '/not-authorised', name: 'not-authorised',
            component: () => import('@/views/NotAuthorised.vue'),
            meta: { requiresAuth: true },
        },

        /* ---- super admin ---- */
        { path: '/super-admin', redirect: '/super-admin/users' },
        { path: '/super-admin/dashboard', redirect: '/super-admin/users' },
        {
            path: '/super-admin/users', name: 'sa-users',
            component: () => import('@/views/SuperAdmin/Users.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
        // Task #17: user detail page, links from the users list
        {
        path: '/super-admin/users/:id',
        name: 'sa-user-detail',
        component: UserDetail,
        meta: { requiresAuth: true, roles: ['super_admin'] },
        },
        {
        path: '/staff/:id',
        name: 'staff-detail',
        component: StaffDetail,
        meta: {
        requiresAuth: true,
        roles: ['super_admin', 'branch_manager']
        }
        },
        {
            path: '/super-admin/administration', name: 'sa-administration',
            component: () => import('@/views/SuperAdmin/Administration.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
        {
            path: '/super-admin/overview', name: 'sa-overview',
            component: () => import('@/views/SuperAdmin/overview.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
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
        {
            path: '/super-admin/participants/:id', name: 'sa-participant-detail',
            component: () => import('@/views/SuperAdmin/ParticipantDetail.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
        {
            path: '/super-admin/reporting', name: 'sa-reporting',
            component: () => import('@/views/SuperAdmin/Reporting.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
        {
            path: '/documents', name: 'documents',
            component: () => import('@/views/Documents.vue'),
            meta: { requiresAuth: true, roles: [...SA, ...BM, ...IN] },
        },
        {
            path: '/super-admin/participants/:id/attendance', name: 'sa-participant-attendance',
            component: () => import('@/views/SuperAdmin/ParticipantAttendance.vue'),
            meta: { requiresAuth: true, roles: SA },
        },
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
        {
            path: '/branch-manager/sessions', name: 'bm-sessions',
            component: () => import('@/views/Instructor/Sessions.vue'),
            meta: { requiresAuth: true, roles: BM },
        },
        {
            path: '/branch-manager/sessions/:id', name: 'bm-session-detail',
            component: () => import('@/views/Instructor/SessionDetail.vue'),
            meta: { requiresAuth: true, roles: BM },
        },
        { path: '/branch-manager/participants', name: 'bm-participants', component: () => import('@/views/BranchManager/Participants.vue'), meta: { requiresAuth: true, roles: BM } },
        {
            path: '/branch-manager/instructors', name: 'bm-instructors',
            component: () => import('@/views/BranchManager/Instructors.vue'),
            meta: { requiresAuth: true, roles: BM },
        },
        {
            path: '/branch-manager/feedback', name: 'bm-feedback',
            component: () => import('@/views/BranchManager/Feedback.vue'),
            meta: { requiresAuth: true, roles: BM },
        },
        {
            path: '/branch-manager/reports', name: 'bm-reports',
            component: () => import('@/views/BranchManager/Reports.vue'),
            meta: { requiresAuth: true, roles: BM },
        },
        {
            path: '/branch-manager/create-instructor', name: 'create-instructor',
            component: () => import('@/views/BranchManager/CreateInstructor.vue'),
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
        {
            path: '/instructor/sessions/:id', name: 'in-session-detail',
            component: () => import('@/views/Instructor/SessionDetail.vue'),
            meta: { requiresAuth: true, roles: IN },
        },
        {
            path: '/instructor/sessions/:id/attendance', name: 'in-attendance-mode',
            component: () => import('@/views/Instructor/AttendanceMode.vue'),
            meta: { requiresAuth: true, roles: IN },
        },
       {
            path: '/instructor/participants',
            name: 'in-participants',
            component: () => import('@/views/Instructor/Participants.vue'),
            meta: { requiresAuth: true, roles: IN },
        },
        comingSoon('/instructor/feedback', 'in-feedback', 'Feedback', IN),
        {
            path: '/instructor/participants/:id', name: 'in-participant-detail',
            component: () => import('@/views/Instructor/ParticipantDetail.vue'),
            meta: { requiresAuth: true, roles: IN },
        },
        {
            path: '/instructor/participants/:id/attendance', name: 'in-participant-attendance',
            component: () => import('@/views/Instructor/ParticipantAttendance.vue'),
            meta: { requiresAuth: true, roles: IN },
        },

        {
            path: '/participants/:id', name: 'participant-detail',
            component: () => import('@/views/ParticipantConsent.vue'),
            meta: { requiresAuth: true, roles: [...SA, ...BM, ...IN]},
        },
        {
            path: '/:pathMatch(.*)*', name: 'unknown-route',
            component: () => import('@/views/NotAuthorised.vue'),
        },
    ]
})

router.beforeEach(createAccessGuard(loadUser))

export default router
