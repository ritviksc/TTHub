<script setup>
import axios from 'axios'
import { ref } from 'vue'
import { login } from '@/apis.js'

import { useRouter } from 'vue-router'
const router = useRouter()
router.push('/')
</script>

<template>
    <p>
        Landing Page
    </p>

</template>

<style scoped></style>
