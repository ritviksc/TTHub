<script setup>
import heroImg from '@/assets/taranaki.jpg'
</script>

<template>
  <div class="public-page">
    <header class="page-head" :style="{ backgroundImage: `url(${heroImg})` }">
      <p class="eyebrow">Nau mai, haere mai ki Taurite Tū</p>
      <h1>Supporting the kaimahi behind every class</h1>
      <p class="lead">
        Taurite Tū is a strength and balance wellness programme designed by Māori, for
        Māori aged 50 plus and their whānau. This site is where the people who deliver
        the programme keep track of it.
      </p>
    </header>

    <div class="prose">
      <p>
        Branches run a class each week, working through exercises that build strength, balance and
        confidence, drawing on mau rākau, tī rākau, poi and other Māori movement forms.
        What happens in those sessions is recorded here, so the mahi stays visible to the
        people supporting it.
      </p>

      <h2>Who this site is for</h2>

      <p>
        Instructors take the roll for their weekly class, record what the class worked
        through, and note how participants found the session.
      </p>

      <p>
        Branch managers see every session their branch has run and who is coming along, and
        they set up the instructor accounts for their rohe.
      </p>

      <p>
        Nationally, those same records build one picture of the programme across Aotearoa:
        every branch, every account, and the reporting that ties them together.
      </p>

      <h2>Getting started</h2>

      <p>
        Accounts are created for you by your branch manager, so there is nothing to sign
        up for here. Once you have one, sign in from the top of the page and you will be
        taken straight to the pages for your role.
      </p>
    </div>
  </div>
</template>

<style scoped>
.public-page {
  min-height: 100vh;
}

.page-head {
  position: relative;
  min-height: 88vh;
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

.lead {
  max-width: 560px;
  color: rgba(255, 255, 255, 0.75);
  font-size: var(--text-lg);
  line-height: 1.6;
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
.public-page {
  padding: 0;
  min-height: 100vh;
  max-width: none;
}

.page-head {
  max-width: none !important;
  width: 100%;
  margin: 0;
  /* keep all your other properties */
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
</style>