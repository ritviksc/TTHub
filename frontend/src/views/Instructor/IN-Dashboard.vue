<script setup>
import { logout} from '@/apis.js'

import { useRouter } from 'vue-router'
const router = useRouter()
async function handleLogout() {
    try {
      await logout();
    } catch (err) {
      console.log("Error logging out",err)
    }
    router.push('/')
}

</script>

<template>
    <form @submit.prevent="handleLogout">
    <button type="submit">
        Logout
    </button>
    </form>
    <p>Instructor Dashboard</p>
</template>

<style scoped></style>