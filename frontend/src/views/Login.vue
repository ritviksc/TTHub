<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { TIMEOUT_ERROR, MAX_ATTEMPTS, withRetry, login, fetchCsrfCookie } from '@/apis.js'

const router = useRouter()

// Tabs are a visual convenience for the person signing in — the account's
// actual role always comes back from the server on login, so picking a tab
// never grants access by itself.
const roleTabs = [
  { key: 'super_admin', label: 'Super Admin', placeholder: 'admin@tauritetu.nz' },
  { key: 'branch_manager', label: 'Branch Manager', placeholder: 'manager@tauritetu.nz' },
  { key: 'instructor', label: 'Instructor', placeholder: 'instructor@tauritetu.nz' },
  { key: 'participant', label: 'Participant', placeholder: 'you@tauritetu.nz' },
]

const roleRoutes = {
  super_admin: '/super-admin/dashboard',
  branch_manager: '/branch-manager/dashboard',
  instructor: '/instructor/dashboard',
}

const activeRole = ref('super_admin')
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const activePlaceholder = computed(
  () => roleTabs.find((r) => r.key === activeRole.value)?.placeholder
)

function selectRole(role) {
  activeRole.value = role.key
  error.value = ''
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
    const destination = roleRoutes[data.role]
    if (destination) {
      router.push(destination)
    } else {
      // No dashboard wired up yet for this account's role (e.g. participant).
      router.push('/')
    }
  } catch (err) {
    if (err.code === TIMEOUT_ERROR) {
      error.value = 'The server took too long to respond.'
    } else if (err.response?.status === 401) {
      error.value = 'Incorrect email or password.'
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
      <div class="brand">
        <h1>Taurite Tū</h1>
        <p>Sign in to your account</p>
      </div>

      <div class="card">
        <div class="tabs" role="tablist">
          <button
            v-for="role in roleTabs"
            :key="role.key"
            type="button"
            role="tab"
            class="tab"
            :class="{ active: activeRole === role.key }"
            :aria-selected="activeRole === role.key"
            @click="selectRole(role)"
          >
            {{ role.label }}
          </button>
        </div>

        <form class="form-area" @submit.prevent="handleSubmit">
          <div class="field">
            <label for="email">Work email</label>
            <div class="input-wrap">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2"></rect>
                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
              </svg>
              <input
                id="email"
                v-model="username"
                type="email"
                :placeholder="activePlaceholder"
                autocomplete="username"
                required
              />
            </div>
          </div>

          <div class="field">
            <label for="password">Password</label>
            <div class="input-wrap">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
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

          <div class="forgot-row">
            <a href="#" @click.prevent>Forgot password?</a>
          </div>

          <p v-if="error" class="error-msg" role="alert">{{ error }}</p>

          <button type="submit" class="submit-btn" :disabled="loading">
            {{ loading ? 'Signing in…' : 'Sign in' }}
            <svg v-if="!loading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
.login-page {
  --bg: #121212;
  --card-bg: #1a1a1a;
  --card-border: #2a2a2a;
  --tab-active-bg: #e9efdc;
  --tab-active-text: #00a9ac;
  --tab-inactive-text: #8a8a8a;
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

  /* Full screen */
  width: 100%;
  min-height: 100vh;
  min-height: 100dvh;

  background: var(--bg);

  display: flex;
  align-items: center;
  justify-content: center;

  padding: 24px 16px;

  font-family: 'Inter', sans-serif;
  color: var(--text-primary);

  box-sizing: border-box;
}

* {
  box-sizing: border-box;
}

.login-wrap {
  width: 100%;
  max-width: 440px;
  margin: auto;
}

/* ---------------- BRAND ---------------- */

.brand {
  text-align: center;
  margin-bottom: 24px;
}

.brand h1 {
  font-family: 'Playfair Display', serif;
  font-weight: 700;
  font-size: clamp(2rem, 6vw, 2.6rem);
  line-height: 1.1;

  color: var(--heading-green);

  margin: 0 0 6px 0;
  letter-spacing: 0.5px;
}

.brand p {
  font-size: 0.95rem;
  color: var(--text-secondary);

  margin: 0;
  font-weight: 400;
}

/* ---------------- CARD ---------------- */

.card {
  width: 100%;

  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 16px;

  overflow: hidden;

  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}

/* ---------------- TABS ---------------- */

.tabs {
  display: flex;
  width: 100%;

  border-bottom: 1px solid var(--card-border);
}

.tab {
  flex: 1;
  min-width: 0;

  text-align: center;

  padding: 15px 4px;

  font-size: 0.78rem;
  font-weight: 600;

  color: var(--tab-inactive-text);

  cursor: pointer;

  background: transparent;
  border: none;

  font-family: 'Inter', sans-serif;

  transition:
    background 0.15s ease,
    color 0.15s ease;

  position: relative;

  white-space: nowrap;
}

.tab.active {
  background: var(--tab-active-bg);
  color: var(--tab-active-text);
}

.tab.active::after {
  content: '';

  position: absolute;

  bottom: -1px;
  left: 0;
  right: 0;

  height: 2px;

  background: var(--heading-green);
}

/* ---------------- FORM ---------------- */

.form-area {
  width: 100%;

  padding: 26px 28px 28px;

  display: flex;
  flex-direction: column;
}

.field {
  margin-bottom: 18px;
}

.field label {
  display: block;

  font-size: 0.9rem;
  font-weight: 600;

  margin-bottom: 7px;

  color: var(--text-primary);
}

/* ---------------- INPUT ---------------- */

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

  background: var(--input-bg);

  border: 1px solid var(--input-border);
  border-radius: 8px;

  padding: 10px 12px 10px 40px;

  font-size: 0.95rem;

  color: var(--text-primary);

  font-family: 'Inter', sans-serif;

  outline: none;

  transition: border-color 0.15s ease;
}

.input-wrap input::placeholder {
  color: var(--input-placeholder);
}

.input-wrap input:focus {
  border-color: var(--heading-green);
}

/* ---------------- FORGOT PASSWORD ---------------- */

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

/* ---------------- ERROR ---------------- */

.error-msg {
  color: var(--error-color);

  font-size: 0.82rem;

  margin: -4px 0 14px;

  line-height: 1.4;
}

/* ---------------- BUTTON ---------------- */

.submit-btn {
  width: 100%;
  height: 46px;

  background: var(--btn-green);

  color: #fff;

  border: none;
  border-radius: 8px;

  padding: 10px 16px;

  font-size: 0.95rem;
  font-weight: 600;

  font-family: 'Inter', sans-serif;

  cursor: pointer;

  display: flex;
  align-items: center;
  justify-content: center;

  gap: 8px;

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

/* ---------------- TABLET ---------------- */

@media (max-width: 600px) {
  .login-page {
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
    padding: 24px 22px 24px;
  }

  .tab {
    font-size: 0.74rem;
    padding: 14px 2px;
  }
}

/* ---------------- MOBILE ---------------- */

@media (max-width: 430px) {
  .login-page {
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

  .tab {
    font-size: 0.68rem;
    padding: 13px 2px;
  }

  .form-area {
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

/* ---------------- VERY SMALL HEIGHT ---------------- */

@media (max-height: 700px) {
  .login-page {
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

  .tab {
    padding-top: 11px;
    padding-bottom: 11px;
  }

  .form-area {
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
</style>