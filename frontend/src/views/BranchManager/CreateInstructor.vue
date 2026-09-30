<script setup>
import { ref, computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { createStaffAccount, assignBranchInstructor } from '@/apis.js'
import { auth } from '@/stores/auth.js'

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
    const createdEmail = form.value.email
    form.value = { email: '', password: '', first_name: '', last_name: '' }
    setTimeout(() => {
      router.push({ name: 'bm-instructors' })
    }, 1500)
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
            <label>Temporary password</label>
            <input v-model="form.password" type="password" placeholder="They can change this after logging in" required />
          </div>

          <div v-if="error" class="msg error">{{ error }}</div>
          <div v-if="success" class="msg success">{{ success }}</div>

          <button type="submit" class="btn-primary">Create instructor account</button>

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
  border-radius: 10px;
  padding: 28px;
  max-width: 560px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.field {
  display: flex;
  flex-direction: column;
  margin-bottom: 18px;
}
.field label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.field input {
  padding: 10px 12px;
  border: 1px solid var(--border-faint);
  border-radius: 6px;
  font-size: 14px;
  background: var(--bg);
  color: var(--text);
}
.field input:focus {
  outline: none;
  border-color: var(--teal);
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.btn-primary {
  background: var(--teal);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  margin-top: 4px;
}
.btn-primary:hover { opacity: 0.9; }

.msg {
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 16px;
}
.error {
  background: var(--danger-bg, #fee);
  color: var(--danger);
}
.success {
  background: var(--success-bg);
  color: var(--success);
}
</style>