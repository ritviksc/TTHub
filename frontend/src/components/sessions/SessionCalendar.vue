<script setup>
import { ref, computed } from 'vue'
import {
  WEEKDAYS,
  parseDateKey,
  generateCalendarGrid,
  groupSessionsByDate,
  formatMonthYear,
  formatFullDate,
  formatTimeDisplay,
} from '@/utils/calendar.js'
import { programmeToday } from '@/utils/sessions.js'

const props = defineProps({
  sessions: {
    type: Array,
    default: () => [],
  },
  canCreate: {
    type: Boolean,
    default: true,
  },
  showBranch: { type: Boolean, default: false },
})

const emit = defineEmits(['select-session', 'create-session'])

const todayStr = programmeToday()
const todayParsed = parseDateKey(todayStr) || { year: new Date().getFullYear(), monthIndex: new Date().getMonth(), day: new Date().getDate() }

// Viewing month & year
const viewYear = ref(todayParsed.year)
const viewMonth = ref(todayParsed.monthIndex)

// Selected date on the calendar
const selectedDate = ref(todayStr)

// Group sessions by 'YYYY-MM-DD'
const sessionsByDate = computed(() => groupSessionsByDate(props.sessions))

// Current month info
const monthInfo = computed(() => formatMonthYear(viewYear.value, viewMonth.value))

// Calendar grid cells
const gridCells = computed(() =>
  generateCalendarGrid(viewYear.value, viewMonth.value, todayStr)
)

// Sessions for the currently selected day
const selectedDaySessions = computed(() =>
  sessionsByDate.value[selectedDate.value] || []
)

// Selected day relative label (Today, Tomorrow, or empty)
const selectedDayRelative = computed(() => {
  if (selectedDate.value === todayStr) return 'Today'
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  const tomorrowStr = tomorrow.toISOString().slice(0, 10)
  if (selectedDate.value === tomorrowStr) return 'Tomorrow'
  return ''
})

// Whether the selected date is in the past
const isSelectedDatePast = computed(() => selectedDate.value < todayStr)

// Navigation methods
function prevMonth() {
  if (viewMonth.value === 0) {
    viewMonth.value = 11
    viewYear.value--
  } else {
    viewMonth.value--
  }
}

function nextMonth() {
  if (viewMonth.value === 11) {
    viewMonth.value = 0
    viewYear.value++
  } else {
    viewMonth.value++
  }
}

function goToToday() {
  viewYear.value = todayParsed.year
  viewMonth.value = todayParsed.monthIndex
  selectedDate.value = todayStr
}

function selectCell(cell) {
  selectedDate.value = cell.date
  // If user clicked a cell outside current month, switch view to that month
  const parsed = parseDateKey(cell.date)
  if (parsed && (parsed.monthIndex !== viewMonth.value || parsed.year !== viewYear.value)) {
    viewYear.value = parsed.year
    viewMonth.value = parsed.monthIndex
  }
}

function onAddSessionForDate(date) {
  emit('create-session', date)
}

function onSessionClick(session) {
  emit('select-session', session.id)
}
</script>

<template>
  <div class="calendar-container">
    <!-- Main calendar view area -->
    <div class="calendar-main">
      <!-- Toolbar -->
      <div class="calendar-toolbar">
        <div class="month-heading">
          <h2 class="month-title">{{ monthInfo.title }}</h2>
          <span class="month-maori">{{ monthInfo.maori }}</span>
        </div>

        <div class="toolbar-nav">
          <button
            type="button"
            class="btn-nav"
            aria-label="Previous month"
            title="Previous month"
            @click="prevMonth"
          >
            ‹
          </button>
          <button
            type="button"
            class="btn-today"
            @click="goToToday"
          >
            Today
          </button>
          <button
            type="button"
            class="btn-nav"
            aria-label="Next month"
            title="Next month"
            @click="nextMonth"
          >
            ›
          </button>
        </div>
      </div>

      <!-- Weekday headers -->
      <div class="weekday-grid">
        <div
          v-for="w in WEEKDAYS"
          :key="w.short"
          class="weekday-cell"
        >
          <span class="wd-short">{{ w.short }}</span>
          <span class="wd-maori">{{ w.maori }}</span>
        </div>
      </div>

      <!-- Days grid -->
      <div class="days-grid">
        <div
          v-for="cell in gridCells"
          :key="cell.date"
          :class="[
            'day-cell',
            {
              'other-month': !cell.isCurrentMonth,
              'is-today': cell.isToday,
              'is-selected': cell.date === selectedDate,
              'has-sessions': sessionsByDate[cell.date]?.length > 0,
            }
          ]"
          tabindex="0"
          role="button"
          :aria-label="`Date ${cell.date}`"
          @click="selectCell(cell)"
          @keydown.enter="selectCell(cell)"
          @keydown.space.prevent="selectCell(cell)"
        >
          <div class="day-cell-header">
            <span :class="['day-num', { 'today-badge': cell.isToday }]">
              {{ cell.dayNumber }}
            </span>
            <button
              v-if="canCreate && !cell.isPast"
              type="button"
              class="btn-quick-add"
              title="Add session on this date"
              @click.stop="onAddSessionForDate(cell.date)"
            >
              +
            </button>
          </div>

          <!-- Session previews in cell -->
          <div v-if="sessionsByDate[cell.date]?.length" class="cell-sessions">
            <div
              v-for="session in sessionsByDate[cell.date].slice(0, 2)"
              :key="session.id"
              :class="['session-pill', { 'pill-finalised': session.attendance_finalised }]"
              :title="`${showBranch ? session.branch_name + ' · ' : ''}${session.time} · ${session.activity}`"
              @click.stop="onSessionClick(session)"
            >
              <span class="pill-time">{{ session.time ? session.time.slice(0, 5) : '' }}</span>
              <span class="pill-activity">{{ showBranch ? `${session.branch_name} · ${session.activity}` : session.activity }}</span>
            </div>

            <div
              v-if="sessionsByDate[cell.date].length > 2"
              class="more-pill"
            >
              +{{ sessionsByDate[cell.date].length - 2 }} more
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Selected Day Agenda / Inspector Sidebar -->
    <aside class="day-agenda">
      <div class="agenda-header">
        <div class="agenda-date-info">
          <span v-if="selectedDayRelative" class="agenda-tag">{{ selectedDayRelative }}</span>
          <h3 class="agenda-title">{{ formatFullDate(selectedDate) }}</h3>
        </div>

        <button
          v-if="canCreate && !isSelectedDatePast"
          type="button"
          class="btn-primary btn-add-day"
          @click="onAddSessionForDate(selectedDate)"
        >
          + Add session
        </button>
      </div>

      <!-- Agenda content -->
      <div class="agenda-content">
        <div v-if="selectedDaySessions.length" class="agenda-sessions">
          <div
            v-for="session in selectedDaySessions"
            :key="session.id"
            class="agenda-card"
            @click="onSessionClick(session)"
          >
            <div class="card-time">
              <span class="time-clock">⏰</span>
              <span>{{ formatTimeDisplay(session.time) }}</span>
            </div>

            <div class="card-title">{{ session.activity }}</div>
            <div v-if="showBranch" class="card-branch">{{ session.branch_name }}</div>

            <div class="card-footer">
              <div v-if="session.attendance_finalised" class="status-finalised">
                ✓ Finalised · {{ session.present_count }} / {{ session.roster_count }} present
              </div>
              <div v-else-if="session.present_count > 0" class="status-progress">
                ✓ {{ session.present_count }} / {{ session.roster_count }} present
              </div>
              <div v-else class="status-pending">
                {{ session.roster_count }} participants on roster
              </div>

              <span class="card-arrow">›</span>
            </div>
          </div>
        </div>

        <div v-else class="agenda-empty">
          <div class="empty-icon">📅</div>
          <h4>No sessions scheduled</h4>
          <p>There are no sessions recorded for this day.</p>
          <span v-if="isSelectedDatePast" class="past-note">
            Past dates cannot have new sessions scheduled.
          </span>
        </div>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.calendar-container {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 24px;
  margin-top: 16px;
  align-items: start;
}

/* Calendar Main Grid Panel */
.calendar-main {
  min-width: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: 24px;
}

/* Toolbar */
.calendar-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.month-heading {
  display: flex;
  flex-direction: column;
}

.month-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text);
  margin: 0;
  line-height: 1.2;
}

.month-maori {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--teal);
  letter-spacing: 0.02em;
}

.toolbar-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-nav {
  background: var(--surface);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  color: var(--text);
  font-size: var(--text-lg);
  font-weight: 700;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
  line-height: 1;
}

.btn-nav:hover {
  background: var(--surface-sunken);
  border-color: var(--teal);
  color: var(--teal);
}

.btn-today {
  background: var(--sand-light);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  color: var(--text);
  font-size: var(--text-sm);
  font-weight: 600;
  height: 36px;
  padding: 0 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-today:hover {
  background: var(--sand);
  color: var(--teal-dark);
}

/* Weekday header row */
.weekday-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 8px;
}

.weekday-cell {
  text-align: center;
  padding: 8px 4px;
  border-bottom: 2px solid var(--border);
}

.wd-short {
  display: block;
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.wd-maori {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* Days grid */
.days-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 8px;
}

.day-cell {
  min-height: 96px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  outline: none;
}

.day-cell:hover {
  transform: translateY(-2px);
  border-color: var(--teal-light);
  box-shadow: 0 4px 12px var(--shadow-glow, rgba(37, 99, 235, 0.12));
}

.day-cell:focus-visible {
  border-color: var(--teal);
  box-shadow: 0 0 0 2px var(--teal-subtle);
}

.day-cell.other-month {
  background: var(--surface-sunken);
  opacity: 0.5;
}

.day-cell.is-today {
  border-color: var(--teal);
}

.day-cell.is-selected {
  border: 2px solid var(--teal);
  background: var(--teal-subtle);
}

.day-cell-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.day-num {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-pill);
}

.day-num.today-badge {
  background: var(--teal);
  color: var(--text-on-ink);
  font-weight: 700;
}

.btn-quick-add {
  display: none;
  width: 20px;
  height: 20px;
  border-radius: var(--radius-pill);
  background: var(--teal-subtle);
  color: var(--teal-dark);
  border: none;
  font-size: var(--text-sm);
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  padding: 0;
}

.day-cell:hover .btn-quick-add {
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-quick-add:hover {
  background: var(--teal);
  color: var(--text-on-ink);
}

/* Session pills in day cells */
.cell-sessions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: hidden;
}

.session-pill {
  background: var(--sand-light);
  border-left: 3px solid var(--teal);
  border-radius: 4px;
  padding: 3px 6px;
  font-size: 11px;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  transition: all 0.15s ease;
}

.session-pill:hover {
  background: var(--sand);
  transform: translateX(1px);
}

.session-pill.pill-finalised {
  border-left-color: var(--forest);
}

.pill-time {
  font-weight: 700;
  color: var(--teal-dark);
  flex-shrink: 0;
}

.pill-activity {
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}

.more-pill {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  padding-left: 4px;
}

/* Day Agenda Sidebar */
.day-agenda {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: 24px;
}

.agenda-header {
  border-bottom: 1px solid var(--border);
  padding-bottom: 16px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.agenda-tag {
  display: inline-block;
  background: var(--teal-subtle);
  color: var(--teal-dark);
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  margin-bottom: 6px;
}

.agenda-title {
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--text);
  margin: 0;
  line-height: 1.3;
}

.btn-add-day {
  width: 100%;
  justify-content: center;
  font-size: var(--text-sm);
  padding: 10px 16px;
}

/* Agenda Session Cards */
.agenda-sessions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.agenda-card {
  background: var(--sand-light);
  border: 1px solid var(--border);
  border-left: 4px solid var(--teal);
  border-radius: var(--radius);
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.agenda-card:hover {
  background: var(--surface);
  border-color: var(--teal);
  box-shadow: var(--shadow-panel);
  transform: translateY(-2px);
}

.card-time {
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--teal-dark);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.card-title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
  line-height: 1.3;
}

.card-branch {
  font-size: var(--text-sm);
  color: var(--text-muted);
  margin-bottom: 12px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-xs);
}

.status-finalised {
  color: var(--forest);
  font-weight: 600;
}

.status-progress {
  color: var(--teal);
  font-weight: 600;
}

.status-pending {
  color: var(--text-muted);
}

.card-arrow {
  font-size: var(--text-base);
  color: var(--text-muted);
  font-weight: 700;
}

/* Agenda Empty State */
.agenda-empty {
  text-align: center;
  padding: 32px 16px;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.agenda-empty h4 {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text);
  margin: 0 0 6px;
}

.agenda-empty p {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin: 0 0 16px;
  line-height: 1.4;
}

.past-note {
  display: block;
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-style: italic;
}

/* Responsive */
@media (max-width: 960px) {
  .calendar-container {
    grid-template-columns: 1fr;
  }
  .day-cell {
    min-height: 80px;
  }
}

@media (max-width: 640px) {
  .wd-maori {
    display: none;
  }
  .day-cell {
    min-height: 64px;
    padding: 4px;
  }
  .day-num {
    font-size: var(--text-xs);
  }
  .pill-activity {
    display: none;
  }
}
</style>
