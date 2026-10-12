<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { THEMES, currentTheme, applyTheme } from '@/utils/theme.js'

const open = ref(false)
const switcherRef = ref(null)

const activeTheme = computed(() => {
  return THEMES.find(t => t.id === currentTheme.value) || THEMES[0]
})

function toggle() {
  open.value = !open.value
}

function selectTheme(themeId) {
  applyTheme(themeId)
  open.value = false
}

function onClickOutside(e) {
  if (switcherRef.value && !switcherRef.value.contains(e.target)) {
    open.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutside)
})
</script>

<template>
  <div ref="switcherRef" class="theme-switcher">
    <button
      type="button"
      class="theme-btn"
      :aria-expanded="open"
      aria-label="Change color theme"
      :title="`Theme: ${activeTheme.name}`"
      @click.stop="toggle"
    >
      <span
        class="theme-dot"
        :style="{ backgroundColor: activeTheme.color }"
      ></span>
      <span class="theme-icon">🎨</span>
      <span class="theme-chevron" :class="{ 'is-open': open }">▾</span>
    </button>

    <transition name="popover">
      <div v-if="open" class="theme-menu" role="menu">
        <div class="menu-header">Select Color Theme</div>
        <div class="theme-list">
          <button
            v-for="t in THEMES"
            :key="t.id"
            type="button"
            :class="['theme-option', { active: currentTheme === t.id }]"
            role="menuitem"
            @click.stop="selectTheme(t.id)"
          >
            <span class="swatch" :style="{ backgroundColor: t.color }"></span>
            <div class="theme-info">
              <span class="option-name">{{ t.name }}</span>
              <span class="option-desc">{{ t.desc }}</span>
            </div>
            <span v-if="currentTheme === t.id" class="check">✓</span>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.theme-switcher {
  position: relative;
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  white-space: nowrap;
}

.theme-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: var(--radius-pill);
  padding: 5px 9px;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-on-ink);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  white-space: nowrap;
  flex-shrink: 0;
}

.theme-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.32);
  transform: translateY(-1px);
}

.theme-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-pill);
  flex-shrink: 0;
  box-shadow: 0 0 6px currentColor;
}

.theme-icon {
  font-size: 13px;
  line-height: 1;
}

.theme-chevron {
  font-size: 10px;
  transition: transform 0.2s ease;
  opacity: 0.8;
}

.theme-chevron.is-open {
  transform: rotate(180deg);
}

/* Popover menu */
.theme-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: 0 12px 32px -4px rgba(0, 0, 0, 0.4), 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 250px;
  padding: 8px;
  z-index: 99999;
  transform-origin: top right;
}

.menu-header {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  padding: 6px 10px 8px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 4px;
}

.theme-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius);
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
  color: var(--text);
}

.theme-option:hover {
  background: var(--surface-sunken);
}

.theme-option.active {
  background: var(--teal-tint);
  border-color: var(--teal-light);
}

.swatch {
  width: 16px;
  height: 16px;
  border-radius: var(--radius-pill);
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.theme-info {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  overflow: hidden;
}

.option-name {
  font-size: var(--text-sm);
  font-weight: 600;
  line-height: 1.25;
  color: var(--text);
}

.option-desc {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.check {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--teal);
}

/* Animations */
.popover-enter-active,
.popover-leave-active {
  transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1), transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.popover-enter-from,
.popover-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-6px);
}
</style>
