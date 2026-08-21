import {createRouter, createWebHistory} from 'vue-router'
import LandingPage from '@/views/LandingPage.vue'
import Login from '@/views/Login.vue'
import AboutUs from '@/views/AboutUs.vue'
import ContactUs from '@/views/ContactUs.vue'
import TestDashboard from '@/views/TestDashboard.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', name: 'home', component: LandingPage},
        { path: '/about', name: 'about-us', component: AboutUs},
        { path: '/contact', name: 'contact-us', component: ContactUs},
        { path: '/login', name: 'login', component: Login},
        { path: '/testdashboard', name: 'testdashboard', component: TestDashboard},
    ]
})

export default router
