import {createRouter, createWebHistory} from 'vue-router'
import LandingPage from '@/views/LandingPage.vue'
import Login from '@/views/Login.vue'
import AboutUs from '@/views/AboutUs.vue'
import ContactUs from '@/views/ContactUs.vue'
import TestDashboard from '@/views/TestDashboard.vue'
import BMDashboard from '@/views/BranchManager/BM-Dashboard.vue'
import INDashboard from '@/views/Instructor/IN-Dashboard.vue'
import SADashboard from '@/views/SuperAdmin/SA-Dashboard.vue'
import CreateStaff from '@/views/SuperAdmin/CreateStaff.vue'
import { fetchMe } from '@/apis.js'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', name: 'home', component: LandingPage},
        { path: '/about', name: 'about-us', component: AboutUs},
        { path: '/contact', name: 'contact-us', component: ContactUs},
        { path: '/login', name: 'login', component: Login},
        { path: '/testdashboard', name: 'testdashboard', component: TestDashboard},
        { path: '/branch-manager/dashboard', name: 'bm-dashboard', component: BMDashboard,
            meta: { requiresAuth: true, roles: ['branch_manager'] } },
        { path: '/instructor/dashboard', name: 'in-dashboard', component: INDashboard,
            meta: {requiresAuth: true, roles: ['instructor'] } },
        { path: '/super-admin/dashboard', name: 'sa-dashboard', component: SADashboard,
            meta: {requiresAuth: true, roles: ['super_admin'] } },
        { path: '/super-admin/create-staff', name: 'create-staff', component: CreateStaff,
            meta: { requiresAuth: true, roles: ['super_admin'] } },
    ]
})

router.beforeEach(async (to) => {
    if (!to.meta.requiresAuth) return true
  
    try {
      const me = await fetchMe()
      if (to.meta.roles && !to.meta.roles.includes(me.role)) {
        return '/login'  // logged in, but wrong role for this page
      }
      return true
    } catch {
      return '/login'  // no valid session at all
    }
  })

export default router
