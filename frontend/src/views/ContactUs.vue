<script setup>
import { ref } from 'vue'

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
  <div class="public-page">
    <article class="panel contact-panel">
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
    </article>
  </div>
</template>

<style scoped>
.contact-panel { text-align: center; }

.contact-panel .lead {
  color: var(--text-secondary);
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
  border-bottom: 1px solid var(--border);
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text);
  font-weight: 600;
  font-size: var(--text-md);
}
.detail-item:hover { color: var(--teal); }

.info-icon { font-size: 20px; line-height: 1; }

.detail-divider { width: 1px; height: 24px; background: var(--border); }

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
  font-size: var(--text-xl);
  text-align: center;
}

.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }

.contact-form button {
  align-self: center;
  padding: 12px 36px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--teal);
  color: var(--text-on-ink);
  font-size: var(--text-md);
  font-weight: 600;
}
.contact-form button:hover { background: var(--teal-dark); }

@media (max-width: 640px) {
  .contact-details { flex-direction: column; gap: 16px; }
  .detail-divider { display: none; }
  .field-row { grid-template-columns: 1fr; }
}
</style>
