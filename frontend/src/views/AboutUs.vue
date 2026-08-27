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
        <h1>What is Taurite Tū?</h1>

        <p class="lead">
          Taurite Tū is a strength and balance wellness programme designed by Māori for Māori
          aged 50 plus and their whānau.
        </p>

        <p>
          We use traditional Māori techniques to strengthen muscle, build balance and
          confidence, and prevent the risk of falling by focusing on posture, breathing,
          strengthening, stretching, coordination, body awareness and pelvic floor muscles.
        </p>

        <p>
          Other benefits of the programme include having a space for kaumātua and pakeke to
          build connection with each other, discuss life, and have some fun!
        </p>

        <h2>Our History</h2>

        <p>
          The concept of Taurite Tū first came to fruition at Ōtākou Marae, located on the
          Otago Peninsula, 25 kilometres from Dunedin City.
        </p>

        <p>
          In 2008, Ūpoko of Te Rūnanga o Ōtākou (TRŌ) Edward Ellison put out a tono to our
          people to find solutions for kaumātua Māori who were not receiving targeted
          falls-prevention approaches.
        </p>

        <p>
          Katrina Pōtiki Bryant is an uri of Ōtākou with 30 years clinical physiotherapy
          experience working in Māori communities, and also Associate Dean Māori&nbsp;&ndash;
          School of Physiotherapy at the University of Otago.
        </p>

        <p>
          Katrina picked up the tono and, with the support of kaumātua Māori, Māori
          physiotherapists, and Māori movement experts in mau rākau (Māori martial arts), tī
          rākau (Māori stick games), poi, tākaro (games) and whare tapere (Māori performing
          arts), she undertook research between 2019&ndash;2022 to develop a te ao Māori falls
          prevention solution with equitable outcomes for aging Māori.
        </p>

        <h2>Growing the Programme</h2>

        <p>
          Phase 1 was rolled out in 2021 with participants from Ōtākou, Puketeraki Marae in
          Karitāne (north of Dunedin) and Ōtākou Health Clinic's Te Kāika, located in central
          Dunedin.
        </p>

        <p>
          Phase 2 of Taurite Tū was adopted by groups in Southland, as well as two locations in
          Te Ika a Māui. In 2023, phase 3 saw 13 more groups deliver Taurite Tū.
        </p>

        <p class="cta-text">
          To find a Taurite Tū class near you, please email
          <a href="mailto:tauritetu@tro.org.nz">tauritetu@tro.org.nz</a>
        </p>
     </div>
    </section>
    </div>
</template>

<style scoped>
.landing-page {
  min-height: 100vh;
  background: #f5f7f4;
  padding: 60px 24px 80px;
}

.hero {
  display: flex;
  justify-content: center;
}

.hero-content {
  max-width: 760px;
  width: 100%;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  padding: 48px 56px;
}

h1 {
  font-size: 42px;
  margin: 0 0 24px;
  color: #4D9298;
  line-height: 1.2;
}

h2 {
  font-size: 24px;
  margin: 40px 0 16px;
  color: #163b2d;
}

p {
  font-size: 17px;
  line-height: 1.7;
  color: #444;
  margin: 0 0 18px;
}

.lead {
  font-size: 19px;
  color: #333;
  font-weight: 500;
}

.cta-text {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e0e0e0;
  color: #333;
}

.cta-text a {
  color: #4D9298;
  font-weight: 600;
  text-decoration: none;
}

.cta-text a:hover {
  text-decoration: underline;
}

@media (max-width: 640px) {
  .landing-page {
    padding: 32px 16px 56px;
  }

  .hero-content {
    padding: 32px 24px;
  }

  h1 {
    font-size: 32px;
  }
}
</style>
