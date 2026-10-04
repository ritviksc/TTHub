<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="public-page">
    <header class="page-head">
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
