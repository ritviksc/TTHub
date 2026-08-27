<script setup>
import axios from 'axios'
import { ref } from 'vue'

import { useRouter } from 'vue-router'
const router = useRouter()

const name = ref('')
const email = ref('')
const message = ref('')
const submitted = ref(false)

//TODO: implement submit
function handleSubmit() {
  // No backend endpoint exists for contact submissions yet
  submitted.value = true
  name.value = ''
  email.value = ''
  message.value = ''
}
</script>

<template>
    <div class="landing-page">
    <section class="hero">
     <div class="hero-content">
        <h1>Contact Us</h1>

        <p class="lead">
          Have a question about Taurite Tū, or want to find a class near you? Get in touch
          using the details below, or send us a message and we'll get back to you.
        </p>

        <div class="contact-details">
          <a class="detail-item" href="tel:+64223449201">
            <span class="info-icon" aria-hidden="true">📞</span>
            <span>022 344 9201</span>
          </a>

          <span class="detail-divider" aria-hidden="true"></span>

          <a class="detail-item" href="mailto:tauritetu@tro.org.nz">
            <span class="info-icon" aria-hidden="true">✉️</span>
            <span>tauritetu@tro.org.nz</span>
          </a>
        </div>

        <form class="contact-form" @submit.prevent="handleSubmit">
          <h2>Send us a message</h2>

          <div class="field-row">
            <div class="field">
              <label for="name">Name</label>
              <input
                id="name"
                v-model="name"
                type="text"
                placeholder="Your name"
                required
              />
            </div>

            <div class="field">
              <label for="email">Email</label>
              <input
                id="email"
                v-model="email"
                type="email"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          <div class="field">
            <label for="message">Message</label>
            <textarea
              id="message"
              v-model="message"
              rows="5"
              placeholder="How can we help?"
              required
            ></textarea>
          </div>

          <p v-if="submitted" class="success-msg" role="status">
            Thanks for reaching out! We'll be in touch soon.
          </p>

          <button type="submit">Send Message</button>
        </form>
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
  max-width: 720px;
  width: 100%;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  padding: 48px 56px;
  text-align: center;
}

h1 {
  font-size: 42px;
  margin: 0 0 16px;
  color: #4D9298;
  line-height: 1.2;
}

.lead {
  font-size: 18px;
  line-height: 1.7;
  color: #444;
  margin: 0 auto 32px;
  max-width: 560px;
}

.contact-details {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
  margin-bottom: 48px;
  padding-bottom: 40px;
  border-bottom: 1px solid #e5e9e6;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #163b2d;
  font-weight: 600;
  font-size: 16px;
  text-decoration: none;
}

.detail-item:hover {
  color: #4D9298;
  text-decoration: underline;
}

.info-icon {
  font-size: 20px;
  line-height: 1;
}

.detail-divider {
  width: 1px;
  height: 24px;
  background: #dfe3e0;
}

.contact-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 480px;
  margin: 0 auto;
  text-align: left;
}

.contact-form h2 {
  margin: 0 0 4px;
  font-size: 22px;
  color: #163b2d;
  text-align: center;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 14px;
  font-weight: 600;
  color: #163b2d;
}

.field input,
.field textarea {
  font-family: inherit;
  font-size: 15px;
  padding: 12px 14px;
  border: 1px solid #dfe3e0;
  border-radius: 8px;
  background: #fff;
  color: #222;
  resize: vertical;
}

.field input:focus,
.field textarea:focus {
  outline: none;
  border-color: #4D9298;
}

.contact-form button {
  align-self: center;
  padding: 12px 36px;
  border: none;
  border-radius: 6px;
  background: #4D9298;
  color: white;
  font-size: 16px;
  cursor: pointer;
}

.contact-form button:hover {
  background: #163b2d;
}

.success-msg {
  margin: 0;
  padding: 10px 14px;
  border-radius: 6px;
  background: #e6f4ea;
  color: #1e5631;
  font-size: 14px;
  text-align: center;
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

  .contact-details {
    flex-direction: column;
    gap: 16px;
  }

  .detail-divider {
    display: none;
  }

  .field-row {
    grid-template-columns: 1fr;
  }
}
</style>
