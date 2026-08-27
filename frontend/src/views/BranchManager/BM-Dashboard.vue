<script setup>
import axios from 'axios'
import { ref } from 'vue'
import { login } from '@/apis.js'

import { useRouter } from 'vue-router'
const router = useRouter()

</script>

<template>
    <div class="dashboard">
        <h1>Branch Manager Dashboard</h1>
        <nav class="dashboard-nav">
            <RouterLink to="/branch-manager/create-instructor">+ Create Instructor</RouterLink>
        </nav>
    </div>
</template>

<style scoped></style>