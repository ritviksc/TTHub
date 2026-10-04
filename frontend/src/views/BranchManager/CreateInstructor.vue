<script setup>
import { ref, computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { createStaffAccount } from '@/apis.js'
import { auth } from '@/stores/auth.js'

const router = useRouter()

const form = ref({
  email: '',
  first_name: '',
  last_name: '',
  password: '',
})

const loading = ref(false)
const error = ref(null)
const success = ref(null)

const branchName = computed(() => auth.user?.branch?.name ?? 'Your branch')

async function submit() {
  if (loading.value) return
  error.value = null
  success.value = null
  loading.value = true

  try {
    await createStaffAccount({
      ...form.value,
      role: 'instructor',
      branch: auth.user?.branch?.id || auth.user?.branch,
    })
    success.value = `Instructor account created for ${form.value.email}.`
    form.value = { email: '', password: '', first_name: '', last_name: '' }
    await router.push({ name: 'bm-instructors' })
  } catch (e) {
    const data = e.response?.data
    if (data && typeof data === 'object') {
      error.value = Object.entries(data)
        .map(([field, msg]) => `${field}: ${Array.isArray(msg) ? msg.join(' ') : msg}`)
        .join('; ')
    } else {
      error.value = e.response?.data?.detail ?? 'Could not create instructor account.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="dash-page">
    <main class="content">

      <div class="page-header">
        <RouterLink to="/branch-manager/instructors" class="back-link">← Back to Kaimahi</RouterLink>
        <h1>Add Kaimahi</h1>
        <p class="page-subtitle">Create an instructor account for {{ branchName }}.</p>
      </div>

      <div class="form-card">
        <form @submit.prevent="submit">

          <div class="field-row">
            <div class="field">
              <label>First name</label>
              <input v-model="form.first_name" placeholder="First name" required />
            </div>
            <div class="field">
              <label>Last name</label>
              <input v-model="form.last_name" placeholder="Last name" required />
            </div>
          </div>

          <div class="field">
            <label>Email</label>
            <input v-model="form.email" type="email" placeholder="instructor@example.com" required />
          </div>

          <div class="field">
            <label>Password</label>
            <input v-model="form.password" type="password" placeholder="At least 8 characters" minlength="8" required />
          </div>

          <div v-if="error" class="msg error">{{ error }}</div>
          <div v-if="success" class="msg success">{{ success }}</div>

          <button type="submit" class="btn-primary" :disabled="loading">{{ loading ? 'Creating…' : 'Create instructor account' }}</button>

        </form>
      </div>

    </main>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: 24px;
}
.back-link {
  display: inline-block;
  font-size: 13px;
  color: var(--teal);
  text-decoration: none;
  margin-bottom: 8px;
}
.back-link:hover { text-decoration: underline; }

.form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 32px 28px;
  max-width: 560px;
  box-shadow: var(--shadow-panel);
}

.field {
  display: flex;
  flex-direction: column;
  margin-bottom: 18px;
}
.field label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.field input {
  padding: 10px 14px;
  border: 1.5px solid var(--border-strong);
  border-radius: var(--radius);
  font-size: var(--text-base);
  background: var(--surface);
  color: var(--text);
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.field input:focus {
  border-color: var(--teal);
  box-shadow: 0 0 0 3px var(--teal-tint);
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.btn-primary {
  background: var(--maroon);
  color: var(--text-on-ink);
  border: none;
  padding: 11px 22px;
  border-radius: var(--radius);
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  margin-top: 6px;
  box-shadow: 0 1px 2px rgba(36, 28, 23, 0.1);
  transition: all 0.15s ease;
}
.btn-primary:hover:not(:disabled) {
  background: var(--maroon-dark);
  box-shadow: 0 2px 6px rgba(36, 28, 23, 0.15);
}

.msg {
  padding: 12px 16px;
  border-radius: var(--radius);
  font-size: var(--text-sm);
  margin-bottom: 18px;
  line-height: 1.45;
}
.error {
  background: var(--danger-bg);
  border: 1px solid rgba(184, 46, 36, 0.2);
  color: var(--danger);
}
.success {
  background: var(--success-bg);
  border: 1px solid rgba(35, 108, 60, 0.2);
  color: var(--success);
}
</style>
