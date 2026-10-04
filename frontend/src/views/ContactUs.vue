<script setup>
import { ref } from 'vue'

const name = ref('')
const email = ref('')
const message = ref('')
const submitted = ref(false)

function handleSubmit() {
  submitted.value = true
  name.value = ''
  email.value = ''
  message.value = ''
}
</script>

<template>
  <div class="public-page">
    <header class="page-head">
      <span class="eyebrow">Contact us</span>
      <h1>Get in touch</h1>
      <p class="lead">
        Have a question about Taurite Tū, or want to find a class near you? Use the details
        below, or send us a message and we'll get back to you.
      </p>

      <div class="contact-details">
        <a class="detail-card" href="tel:+64223449201">
          <span class="info-icon" aria-hidden="true">📞</span>
          <div class="detail-text">
            <span class="detail-label">Phone</span>
            <span class="detail-val">022 344 9201</span>
          </div>
        </a>

        <a class="detail-card" href="mailto:tauritetu@tro.org.nz">
          <span class="info-icon" aria-hidden="true">✉️</span>
          <div class="detail-text">
            <span class="detail-label">Email</span>
            <span class="detail-val">tauritetu@tro.org.nz</span>
          </div>
        </a>
      </div>
    </header>

    <div class="form-wrapper">
      <form class="contact-form" @submit.prevent="handleSubmit">
        <h2>Send us a message</h2>
        <p class="form-subtitle">Fill in the fields below and our team will be in touch.</p>

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
          ✓ Thanks for reaching out! We'll be in touch soon.
        </p>

        <button type="submit" class="submit-btn">Send Message</button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.contact-details {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 28px;
}

.detail-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  text-decoration: none;
  transition: all 0.15s ease;
}

.detail-card:hover {
  box-shadow: var(--shadow-panel);
  border-color: var(--teal);
  text-decoration: none;
}

.detail-text {
  display: flex;
  flex-direction: column;
  text-align: left;
}

.detail-label {
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.detail-val {
  color: var(--text);
  font-weight: 600;
  font-size: var(--text-base);
}

.info-icon {
  font-size: 20px;
  line-height: 1;
}

.form-wrapper {
  max-width: 540px;
  margin: 48px auto 0;
}

.contact-form {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 36px 32px;
  box-shadow: var(--shadow-panel);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.contact-form h2 {
  margin: 0;
  font-size: var(--text-xl);
  text-align: center;
}

.form-subtitle {
  text-align: center;
  color: var(--text-muted);
  font-size: var(--text-sm);
  margin: -10px 0 6px;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.submit-btn {
  align-self: center;
  padding: 12px 36px;
  border: none;
  border-radius: var(--radius);
  background: var(--maroon);
  color: var(--text-on-ink);
  font-size: var(--text-base);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(36, 28, 23, 0.15);
  cursor: pointer;
  transition: all 0.15s ease;
  margin-top: 6px;
}

.submit-btn:hover {
  background: var(--maroon-dark);
  box-shadow: 0 4px 10px rgba(36, 28, 23, 0.2);
}

@media (max-width: 640px) {
  .contact-details {
    flex-direction: column;
    width: 100%;
  }
  .detail-card {
    width: 100%;
    justify-content: center;
  }
  .contact-form {
    padding: 24px 20px;
  }
  .field-row {
    grid-template-columns: 1fr;
  }
}
</style>
