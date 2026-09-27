<script setup>
import { ref, computed, onMounted } from 'vue'
import { getParticipantAttendance } from '@/apis.js'
import { countByStatus, formatSessionDate, finalisedAttendance } from '@/utils/sessions.js'

const props = defineProps({ participantId: { type: String, required: true } })
const records = ref([])
const loading = ref(true)
const error = ref('')
// Match reporting: only explicit finalisation establishes a completed register.
const completed = computed(() => finalisedAttendance(records.value))
const incomplete = computed(() => records.value.length - completed.value.length)
const summary = computed(() => countByStatus(completed.value))
onMounted(async () => {
  try {
    records.value = await getParticipantAttendance(props.participantId)
  } catch (e) {
    error.value = e.response?.data?.detail ?? 'Could not load attendance history.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="attendance">
    <h2>Attendance history</h2>
    <p v-if="loading" class="loading-note">Loading attendance…</p>
    <p v-else-if="error" class="form-error" role="alert">{{ error }}</p>
    <template v-else>
      <p v-if="incomplete" class="loading-note">{{ incomplete }} unfinished register entries excluded from attendance totals.</p>
      <p v-if="!completed.length" class="loading-note">No finalised attendance recorded.</p>
      <template v-else>
        <p>Attendance totals include only finalised registers.</p>
        <div class="stat-grid">
          <div v-for="status in ['present', 'absent']" :key="status" class="stat-tile">
            <div class="stat-tile-value">{{ summary[status] }}</div>
            <div class="stat-tile-label">{{ status === 'present' ? 'Present' : 'Absent' }}</div>
          </div>
          <div class="stat-tile"><div class="stat-tile-value">{{ summary.rate }}%</div><div class="stat-tile-label">Attendance rate</div></div>
        </div>
        <div class="table-scroll">
          <table class="data-table">
            <thead><tr><th>Date</th><th>Activity</th><th>Attendance</th><th>Absence reason</th></tr></thead>
            <tbody>
              <tr v-for="record in completed" :key="record.id">
                <td>{{ formatSessionDate(record.date) }} {{ record.time.slice(0, 5) }}</td>
                <td>{{ record.activity }}</td>
                <td><span :class="['status-badge', record.status === 'present' ? 'active' : 'inactive']">{{ record.status === 'present' ? 'Present' : 'Absent' }}</span></td>
                <td>{{ record.absence_reason_other || record.absence_reason || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </template>
  </section>
</template>

<style scoped>
.attendance { margin: 24px 0; }
.attendance h2 { margin-bottom: 16px; }
.attendance p { color: var(--text-secondary); }
.table-scroll { overflow-x: auto; }
</style>
