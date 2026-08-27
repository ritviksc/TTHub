<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  TIMEOUT_ERROR,
  MAX_ATTEMPTS,
  withRetry,
  login,
  fetchCsrfCookie
} from '@/apis.js'

const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const roleRoutes = {
  super_admin: '/super-admin/dashboard',
  branch_manager: '/branch-manager/dashboard',
  instructor: '/instructor/dashboard',
}

onMounted(async () => {
  try {
    await withRetry(MAX_ATTEMPTS, fetchCsrfCookie)
  } catch (err) {
    console.error('Unable to get CSRF cookie:', err)
    error.value = 'Unable to connect to server. Try logging in later.'
  }
})

async function handleSubmit() {
  loading.value = true
  error.value = ''

  try {
    const data = await login(username.value, password.value)
    router.push(roleRoutes[data.role] ?? '/')
  } catch (err) {
    if (err.code === TIMEOUT_ERROR) {
      error.value = 'The server took too long to respond.'
    } else if (err.response?.status === 401) {
      error.value = 'Incorrect username or password.'
    } else if (err.response?.status === 403) {
      error.value = 'Request was rejected. Please refresh and try again.'
    } else if (!err.response) {
      error.value = 'Unable to reach the server.'
    } else {
      error.value = 'Something went wrong. Please try again later.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-wrap">

      <!-- Brand -->
      <div class="brand">
        <h1>Taurite Tū</h1>
        <p>Sign in to your account</p>
      </div>

      <!-- Login Card -->
      <div class="card">
        <form class="form-area" @submit.prevent="handleSubmit">

          <!-- Username -->
          <div class="field">
            <label for="username">Username</label>

            <div class="input-wrap">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <circle cx="12" cy="8" r="4"></circle>
                <path d="M4 21a8 8 0 0 1 16 0"></path>
              </svg>

              <input
                id="username"
                v-model="username"
                type="text"
                placeholder="Enter your username"
                autocomplete="username"
                required
              />
            </div>
          </div>

          <!-- Password -->
          <div class="field">
            <label for="password">Password</label>

            <div class="input-wrap">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <rect x="3" y="11" width="18" height="11" rx="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>

              <input
                id="password"
                v-model="password"
                type="password"
                placeholder="Enter your password"
                autocomplete="current-password"
                required
              />
            </div>
          </div>

          <!-- Forgot Password -->
          <div class="forgot-row">
            <a href="#" @click.prevent>
              Forgot password?
            </a>
          </div>

          <!-- Error -->
          <p
            v-if="error"
            class="error-msg"
            role="alert"
          >
            {{ error }}
          </p>

          <!-- Sign In -->
          <button
            type="submit"
            class="submit-btn"
            :disabled="loading"
          >
            {{ loading ? 'Signing in…' : 'Sign in' }}

            <svg
              v-if="!loading"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M5 12h14"></path>
              <path d="m12 5 7 7-7 7"></path>
            </svg>
          </button>

        </form>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* ================================
   LOGIN PAGE
================================ */

.login-page {
  --bg: #121212;
  --card-bg: #1a1a1a;
  --card-border: #2a2a2a;

  --heading-green: #00a9ac;

  --input-bg: #161616;
  --input-border: #333333;
  --input-placeholder: #6f6f6f;

  --text-primary: #f2f2f2;
  --text-secondary: #c9c9c9;

  --btn-green: #00a9ac;
  --btn-green-hover: #008f92;

  --link-color: #b9b9b9;
  --error-color: #e08a8a;

  width: 100%;
  min-height: 100vh;
  min-height: 100dvh;

  display: flex;
  align-items: center;
  justify-content: center;

  /* Original padding */
  padding: 24px 16px;

  background: var(--bg);
  color: var(--text-primary);

  box-sizing: border-box;

  font-family: 'Inter', sans-serif;
}


/* ================================
   WRAPPER
================================ */

.login-wrap {
  width: 100%;
  max-width: 440px;
  margin: 0 auto;
}


/* ================================
   BRAND
================================ */

.brand {
  text-align: center;
  margin-bottom: 24px;
}

.brand h1 {
  margin: 0 0 6px;

  font-family: 'Playfair Display', serif;
  font-size: clamp(2rem, 6vw, 2.6rem);
  font-weight: 700;
  line-height: 1.1;

  letter-spacing: 0.5px;

  color: var(--heading-green);
}

.brand p {
  margin: 0;

  font-size: 0.95rem;
  font-weight: 400;

  color: var(--text-secondary);
}


/* ================================
   LOGIN CARD
================================ */

.card {
  width: 100%;

  background: var(--card-bg);

  border: 1px solid var(--card-border);
  border-radius: 16px;

  overflow: hidden;

  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);

  box-sizing: border-box;
}


/* ================================
   FORM
================================ */

.form-area {
  width: 100%;

  /* Original padding */
  padding: 28px;

  display: flex;
  flex-direction: column;

  box-sizing: border-box;
}


/* ================================
   FORM FIELD
================================ */

.field {
  width: 100%;
  margin-bottom: 18px;
}

.field label {
  display: block;

  margin-bottom: 7px;

  font-size: 0.9rem;
  font-weight: 600;

  color: var(--text-primary);
}


/* ================================
   INPUT
================================ */

.input-wrap {
  position: relative;

  display: flex;
  align-items: center;

  width: 100%;
}

.input-wrap svg {
  position: absolute;

  left: 13px;

  width: 17px;
  height: 17px;

  color: #9a9a9a;

  pointer-events: none;
}

.input-wrap input {
  width: 100%;
  min-width: 0;
  height: 46px;

  padding: 10px 12px 10px 40px;

  background: var(--input-bg);

  border: 1px solid var(--input-border);
  border-radius: 8px;

  color: var(--text-primary);

  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;

  outline: none;

  box-sizing: border-box;

  transition: border-color 0.15s ease;
}

.input-wrap input::placeholder {
  color: var(--input-placeholder);
}

.input-wrap input:focus {
  border-color: var(--heading-green);
}


/* ================================
   FORGOT PASSWORD
================================ */

.forgot-row {
  text-align: right;

  margin: -2px 0 18px;
}

.forgot-row a {
  color: var(--link-color);

  font-size: 0.82rem;

  text-decoration: none;
}

.forgot-row a:hover {
  text-decoration: underline;
}


/* ================================
   ERROR
================================ */

.error-msg {
  margin: -4px 0 14px;

  color: var(--error-color);

  font-size: 0.82rem;
  line-height: 1.4;
}


/* ================================
   SIGN IN BUTTON
================================ */

.submit-btn {
  width: 100%;
  height: 46px;

  display: flex;
  align-items: center;
  justify-content: center;

  gap: 8px;

  padding: 10px 16px;

  background: var(--btn-green);

  border: none;
  border-radius: 8px;

  color: #fff;

  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  font-weight: 600;

  cursor: pointer;

  transition:
    background 0.15s ease,
    opacity 0.15s ease;
}

.submit-btn:hover:not(:disabled) {
  background: var(--btn-green-hover);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.submit-btn svg {
  width: 17px;
  height: 17px;
}


/* ================================
   TABLET
================================ */

@media (max-width: 600px) {
  .login-page {
    /* Original padding */
    padding: 20px 14px;
  }

  .login-wrap {
    max-width: 420px;
  }

  .brand {
    margin-bottom: 20px;
  }

  .brand h1 {
    font-size: 2.2rem;
  }

  .brand p {
    font-size: 0.9rem;
  }

  .form-area {
    /* Original padding */
    padding: 24px 22px;
  }
}


/* ================================
   MOBILE
================================ */

@media (max-width: 430px) {
  .login-page {
    /* Original padding */
    padding: 16px 10px;
  }

  .login-wrap {
    max-width: 100%;
  }

  .brand {
    margin-bottom: 16px;
  }

  .brand h1 {
    font-size: 2rem;
  }

  .brand p {
    font-size: 0.85rem;
  }

  .card {
    border-radius: 13px;
  }

  .form-area {
    /* Original padding */
    padding: 20px 18px 22px;
  }

  .field {
    margin-bottom: 16px;
  }

  .field label {
    font-size: 0.85rem;
    margin-bottom: 6px;
  }

  .input-wrap input {
    height: 44px;
    font-size: 0.9rem;
  }

  .submit-btn {
    height: 44px;
    font-size: 0.9rem;
  }
}


/* ================================
   SMALL HEIGHT SCREENS
================================ */

@media (max-height: 700px) {
  .login-page {
    /* Original padding */
    padding-top: 12px;
    padding-bottom: 12px;
  }

  .brand {
    margin-bottom: 12px;
  }

  .brand h1 {
    font-size: 1.9rem;
    margin-bottom: 3px;
  }

  .brand p {
    font-size: 0.8rem;
  }

  .form-area {
    /* Original padding */
    padding-top: 18px;
    padding-bottom: 18px;
  }

  .field {
    margin-bottom: 13px;
  }

  .forgot-row {
    margin-bottom: 13px;
  }
}


/* ================================
   VERY SMALL MOBILE HEIGHT
================================ */

@media (max-width: 430px) and (max-height: 700px) {
  .login-page {
    /* Original padding */
    padding: 10px;
  }

  .brand {
    margin-bottom: 10px;
  }

  .brand h1 {
    font-size: 1.7rem;
  }

  .form-area {
    /* Original padding */
    padding: 16px;
  }

  .field {
    margin-bottom: 12px;
  }

  .input-wrap input,
  .submit-btn {
    height: 42px;
  }
}
</style>