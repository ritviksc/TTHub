<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  ariaLabel: { type: String, default: '' },
  align: { type: String, default: 'left' },
  triggerClass: { type: String, default: 'nav-icon-btn' },
  // Also open while a mouse is over the menu; clicks still toggle for touch and keyboard.
  hover: { type: Boolean, default: false },
})

const route = useRoute()
const open = ref(false)
const menuRef = ref(null)
const triggerRef = ref(null)

// Short delay so the pointer can cross the gap between the trigger and the panel.
let leaveTimer = null

function onPointerEnter(e) {
  if (!props.hover || e.pointerType !== 'mouse') return
  clearTimeout(leaveTimer)
  open.value = true
}

function onPointerLeave(e) {
  if (!props.hover || e.pointerType !== 'mouse') return
  leaveTimer = setTimeout(() => { open.value = false }, 200)
}

function onTriggerClick(e) {
  // A mouse click on a hover menu would otherwise close the menu the hover just opened.
  if (props.hover && e.pointerType === 'mouse') open.value = true
  else open.value = !open.value
}

function close({ focus = false } = {}) {
  open.value = false
  if (focus) triggerRef.value?.focus()
}

function onClickOutside(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) close()
}

function onKeydown(e) {
  if (open.value && e.key === 'Escape') close({ focus: true })
}

watch(() => route.fullPath, () => close())

onMounted(() => {
  document.addEventListener('click', onClickOutside)
  document.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  clearTimeout(leaveTimer)
  document.removeEventListener('click', onClickOutside)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div ref="menuRef" class="nav-menu" @pointerenter="onPointerEnter" @pointerleave="onPointerLeave">
    <button
      ref="triggerRef"
      type="button"
      :class="[triggerClass, 'nav-menu__trigger']"
      aria-haspopup="menu"
      :aria-expanded="open"
      :aria-label="ariaLabel || undefined"
      @click.stop="onTriggerClick"
    >
      <slot name="trigger" />
      <span class="nav-menu__chevron" :class="{ 'is-open': open }" aria-hidden="true">▾</span>
    </button>

    <transition name="popover">
      <div v-if="open" :class="['nav-menu__panel', `nav-menu__panel--${align}`]" role="menu">
        <slot />
      </div>
    </transition>
  </div>
</template>
