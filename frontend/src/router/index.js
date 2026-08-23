import {createRouter, createWebHistory} from 'vue-router'
import LandingPage from '@/views/LandingPage.vue'
import Login from '@/views/Login.vue'
import AboutUs from '@/views/AboutUs.vue'
import ContactUs from '@/views/ContactUs.vue'
import TestDashboard from '@/views/TestDashboard.vue'
import BMDashboard from '@/views/BranchManager/BM-Dashboard.vue'
import INDashboard from '@/views/Instructor/IN-Dashboard.vue'
import SADashboard from '@/views/SuperAdmin/SA-Dashboard.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', name: 'home', component: LandingPage},
        { path: '/about', name: 'about-us', component: AboutUs},
        { path: '/contact', name: 'contact-us', component: ContactUs},
        { path: '/login', name: 'login', component: Login},
        { path: '/testdashboard', name: 'testdashboard', component: TestDashboard},
        { path: '/branch-manager/dashboard', name: 'bm-dashboard', component: BMDashboard },
        { path: '/instructor/dashboard', name: 'in-dashboard', component: INDashboard },
        { path: '/super-admin/dashboard', name: 'sa-dashboard', component: SADashboard },
    ]
})

export default router
