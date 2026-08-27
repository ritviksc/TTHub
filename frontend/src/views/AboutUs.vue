<script setup>
import axios from 'axios'
import { ref } from 'vue'

import { useRouter } from 'vue-router'
const router = useRouter()

</script>

<template>
    <div class="landing-page">
    <section class="hero">
     <div class="hero-content">
        <h1>WHAT IS TAURITE TU?…</h1>

        <p class="about-text">Taurite Tū is a strength and balance wellness programme designed by Māori for Māori aged 50 plus and their whānau.
            We use traditional Māori techniques to strengthen muscle, build balance and confidence and prevent the risk of falling by focusing on posture, breathing, strengthening, stretching, coordination, body awareness and pelvic floor muscles.
Other benefits of the programme include having a space for kaumātua and pakeke to build connection with each other, discuss life, and have some fun!

The concept of Taurite Tū first came to fruition at Ōtākou Marae, located on the Otago Peninsula, 25 kilometres from Dunedin City.

In 2008, Ūpoko of Te Rūnanga o Ōtākou (TRŌ) Edward Ellison put out a tono to our people to find solutions for kaumātua Māori who were not receiving targeted falls-prevention approaches.

Katrina Pōtiki Bryant is an uri of Ōtākou with 30 years clinical physiotherapy experience working in Māori communities, and also Associate Dean Māori-School of Physiotherapy at the University of Otago.

Katrina picked up the tono and, with the support of kaumātua Māori, Māori physiotherapists, and Māori movement experts in mau rākau (Māori martial arts), tī rākau (Māori stick games), poi, tākaro (games) and whare tapare (Māori performing arts), she undertook research between 2019-2022 to develop a te ao Māori falls prevention solution with equitable outcomes for aging Māori.

Phase 1 was rolled out in 2021 with participants from Ōtākou, Puketeraki Marae in Karitane (north of Dunedin) and Ōtākou Health Clinic's Te Kāika, located in central Dunedin.

Phase 2 of Taurite Tū was adopted by groups in Southland, as well as two locations in Te Ika a Maui. In 2023, phase 3 saw 13 more groups deliver Taurite Tū.

To find a Taurite Tū class near you, please email tauritetu@tro.org.nz</p>

        <button @click="goToLogin">Login</button>
     </div>
    </section>
    </div>
</template>

<style scoped>
.about-text {
  white-space: pre-line;
}
</style>
