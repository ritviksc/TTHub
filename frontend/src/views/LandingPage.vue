<script setup>
import axios from 'axios'
import { ref } from 'vue'
import { login } from '@/apis.js'

import { useRouter } from 'vue-router'
const router = useRouter()

function goToLogin(){
router.push('/login')
}

</script>


<template>
   <div class="landing-page">
   <section class="hero">
     <div class="hero-content">
        <h1>Taurite Tu</h1>

        <h2>Programme Tracking Made Simple</h2>

        <p>
          A digital platform designed to help manage,
          track and monitor programmes across kapa.
        </p>

        <button @click="goToLogin">Login</button>
     </div>
    </section>

    </div>

</template>

<style scoped>
.landing-page {
  min-height: 100vh;
  background: #f5f7f4;
}

.hero {
  min-height: 90vh;

  display: flex;
  align-items: center;
  justify-content: center;

  text-align: center;
  padding: 40px;
}

.hero-content {
  max-width: 700px;
}

h1 {
  font-size: 64px;
  margin: 0;
  color: #4D9298;
}

h2 {
  font-size: 30px;
  margin: 15px 0;
  color: #222;
}

p {
  font-size: 18px;
  line-height: 1.6;
  color: #666;
  margin-bottom: 30px;
}

button {
  padding: 12px 30px;

  border: none;
  border-radius: 6px;

  background: #4D9298;
  color: white;

  font-size: 16px;
  cursor: pointer;
}

button:hover {
  background: #163b2d;
}</style>
