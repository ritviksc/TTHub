// Theme management store and utilities
import { ref } from 'vue'

export const THEMES = [
  { id: 'classic',  name: 'Classic',        color: '#54463b', desc: 'Original Pounamu & Kōkōwai' },
  { id: 'sapphire', name: 'Royal Sapphire', color: '#2563eb', desc: 'Electric Cobalt & Crisp Slate' },
  { id: 'pounamu',  name: 'Oceanic Pounamu', color: '#0d9488', desc: 'Vibrant Sea Teal & Slate' },
  { id: 'emerald',  name: 'Emerald Health',  color: '#059669', desc: 'Fresh Kawakawa Vitality' },
  { id: 'sunset',   name: 'Sunset Coral',    color: '#e11d48', desc: 'Modern Rose & Violet' },
  { id: 'midnight', name: 'Midnight Dark',   color: '#38bdf8', desc: 'Deep Obsidian Dark Mode' },
]

function getInitialTheme() {
  if (typeof localStorage !== 'undefined') {
    const saved = localStorage.getItem('taurite_theme')
    if (saved && THEMES.some(t => t.id === saved)) {
      return saved
    }
  }
  return 'classic'
}

export const currentTheme = ref(getInitialTheme())

export function applyTheme(themeId) {
  if (!THEMES.some(t => t.id === themeId)) return
  currentTheme.value = themeId
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', themeId)
    if (document.body) {
      document.body.setAttribute('data-theme', themeId)
    }
  }
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('taurite_theme', themeId)
  }
}

// Apply immediately on load
if (typeof document !== 'undefined') {
  applyTheme(currentTheme.value)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => applyTheme(currentTheme.value))
  }
}
