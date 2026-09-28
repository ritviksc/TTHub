<script setup>
import { ref, computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
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

      <RouterLink :to="{ name: 'bm-instructors' }" class="back-link">&lsaquo; Back to instructors</RouterLink>

      <div class="page-header">
        <div>
          <h1>Create instructor</h1>
          <p class="page-subtitle">Add a new instructor for {{ branchName }}.</p>
        </div>
      </div>

      <div class="card form-card">
        <form @submit.prevent="submit">

          <div v-if="error" class="form-error" style="margin-bottom: 20px;">
            {{ error }}
          </div>

          <div v-if="success" class="form-success" style="margin-bottom: 20px;">
            ✓ {{ success }} Redirecting to instructors…
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="first-name">First name</label>
              <input
                id="first-name"
                v-model="form.first_name"
                type="text"
                required
                placeholder="e.g. Ari"
              />
            </div>

            <div class="form-group">
              <label for="last-name">Last name</label>
              <input
                id="last-name"
                v-model="form.last_name"
                type="text"
                required
                placeholder="e.g. Te Rangi"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="email">Email address</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              placeholder="instructor@example.com"
            />
          </div>

          <div class="form-group">
            <label for="password">Temporary password</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              minlength="8"
              placeholder="At least 8 characters"
            />
            <span class="field-hint">The instructor will sign in with their email and this password.</span>
          </div>

          <div class="form-group">
            <label>Assigned branch</label>
            <input
              type="text"
              :value="branchName"
              disabled
              class="readonly-input"
            />
            <span class="field-hint">Instructors are automatically scoped to your branch.</span>
          </div>

          <div class="form-actions">
            <RouterLink :to="{ name: 'bm-instructors' }" class="btn-cancel">Cancel</RouterLink>
            <button type="submit" class="btn-primary" :disabled="loading">
              {{ loading ? 'Creating instructor…' : 'Create instructor' }}
            </button>
          </div>

        </form>
      </div>

    </main>
  </div>
</template>

<style scoped>
.form-card {
  max-width: 640px;
}

.form-success {
  background: var(--mint);
  color: var(--forest);
  border: 1px solid var(--forest);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  font-size: var(--text-sm);
  font-weight: 500;
}

.readonly-input {
  background: var(--sand-light) !important;
  color: var(--bark) !important;
  cursor: not-allowed;
}

.field-hint {
  display: block;
  font-size: var(--text-xs);
  color: var(--bark);
  margin-top: 4px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border-faint);
}
</style>