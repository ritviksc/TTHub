<script setup>
import axios from 'axios'
import { ref } from 'vue'

import { useRouter } from 'vue-router'
const router = useRouter()

</script>

<template>
    <!--TODO: Needs rough skelton-->
    <div class="landing-page">
    <section class="hero">
     <div class="hero-content">
        <h1>Contact Us</h1>

        <p>
          Phone: 022 344 9201
        </p>

        <button @click="goToLogin">Login</button>
     </div>
    </section>
    </div>
</template>

<style scoped></style>
