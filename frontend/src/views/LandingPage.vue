<script setup>
import heroImg from '@/assets/taranaki.jpg'
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="public-page">
    <header class="page-head" :style="{ backgroundImage: `url(${heroImg})` }">
      <span class="eyebrow">Nau mai, haere mai ki Taurite Tū</span>
      <h1>Supporting the kaimahi behind every class</h1>
      <p class="lead">
        Taurite Tū is a strength and balance wellness programme designed by Māori, for
        Māori aged 50 plus and their whānau. This site is where the people who deliver
        the programme keep track of it.
      </p>

      <div class="hero-actions">
        <RouterLink to="/login" class="btn">
          Sign in to your account
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </RouterLink>
        <RouterLink to="/about" class="btn-secondary">About the programme</RouterLink>
      </div>
    </header>

    <div class="prose">
      <div class="callout-box">
        <p>
          Branches run a class each week, working through exercises that build strength, balance and
          confidence, drawing on mau rākau, tī rākau, poi and other Māori movement forms.
          What happens in those sessions is recorded here, so the mahi stays visible to the
          people supporting it.
        </p>
      </div>

      <h2>Who this site is for</h2>

      <div class="feature-grid">
        <div class="feature-card">
          <span class="feature-tag">Kaimahi</span>
          <h3>Instructors</h3>
          <p>
            Take the roll for weekly classes, record what the group worked through,
            and monitor kaumātua progress and feedback.
          </p>
        </div>

        <div class="feature-card">
          <span class="feature-tag">Whakahaere</span>
          <h3>Branch Managers</h3>
          <p>
            See every session run in your rohe, review attendance trends, manage
            local instructor accounts, and prepare quarterly reports.
          </p>
        </div>

        <div class="feature-card">
          <span class="feature-tag">Te Motu Whānui</span>
          <h3>National Overview</h3>
          <p>
            One connected picture of Taurite Tū across Aotearoa: every branch,
            every staff member, and the reporting that ties them together.
          </p>
        </div>
      </div>

      <h2>Getting started</h2>

      <p>
        Accounts are created for you by your branch manager, so there is nothing to sign
        up for here. Once you have an account, sign in from the top of the page and you will be
        taken straight to the pages for your role.
      </p>
    </div>
  </div>
</template>

<style scoped>
.public-page {
  padding: 0;
  min-height: 100vh;
  max-width: none;
}

.page-head {
  max-width: none;
  width: 100%;
  margin: 0;
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 80px 24px;
  background-size: cover;
  background-position: center;
  overflow: hidden;
}

.page-head::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(10, 25, 28, 0.25) 0%,
    rgba(10, 25, 28, 0.45) 60%,
    rgba(10, 25, 28, 0.75) 100%
  );
}

.page-head > * {
  position: relative;
  z-index: 1;
}

.eyebrow {
  color: #ffffff;
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.6);
  font-size: var(--text-sm);
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 16px;
}

.page-head h1 {
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 800;
  letter-spacing: -1px;
  line-height: 1.1;
  max-width: 700px;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #ffffff 0%, #7dcdd1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-head .lead {
  max-width: 560px;
  color: rgba(255, 255, 255, 0.88);
  font-size: var(--text-lg);
  line-height: 1.6;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.9);
}

.prose {
  max-width: 680px;
  margin: 0 auto;
  padding: 64px 24px;
  line-height: 1.7;
}

.prose h2 {
  color: var(--text);
  font-size: var(--text-xl);
  font-weight: 700;
  margin: 40px 0 16px;
}

.prose p {
  color: var(--text-secondary);
  margin-bottom: 20px;
}
</style>