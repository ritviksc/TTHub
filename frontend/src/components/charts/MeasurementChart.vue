<script setup>
import { computed } from 'vue'
import { chartGeometry } from '@/utils/measurementCharts.js'
const props = defineProps({ points: { type: Array, default: () => [] }, title: String, unit: String })
const chart = computed(() => chartGeometry(props.points))
</script>

<template>
  <figure class="measurement-chart">
    <figcaption>{{ title }} ({{ unit }})</figcaption>
    <p v-if="!chart.hasData" class="loading-note">No measured results to plot in this selection.</p>
    <template v-else>
      <svg viewBox="0 0 640 215" role="img" :aria-label="`${title}, in ${unit}. Exact values are listed below.`">
        <line x1="55" y1="35" x2="55" y2="165" class="axis" />
        <line x1="55" y1="165" x2="585" y2="165" class="axis" />
        <text x="45" y="169" text-anchor="end">0</text>
        <text x="45" y="40" text-anchor="end">{{ chart.maximum.toFixed(1) }}</text>
        <text x="55" y="195">{{ points[0]?.date }}</text>
        <text x="585" y="195" text-anchor="end">{{ points.at(-1)?.date }}</text>
        <polyline v-for="(segment, index) in chart.segments" :key="index" :points="segment.map(p => `${p.x},${p.y}`).join(' ')" class="trend" />
        <template v-for="(point, index) in chart.plotted" :key="index">
          <circle v-if="point.y !== null" :cx="point.x" :cy="point.y" r="4" class="point"><title>{{ point.date }}: {{ point.value }} {{ unit }} {{ point.note || '' }}</title></circle>
        </template>
      </svg>
      <details><summary>View chart values</summary><ul><li v-for="(point, index) in points" :key="index">{{ point.date }}: {{ point.value === null ? 'No measurement' : `${point.value} ${unit}` }} <span v-if="point.note">({{ point.note }})</span></li></ul></details>
    </template>
  </figure>
</template>

<style scoped>
.measurement-chart { margin: 16px 0; }
figcaption { font-weight: 600; color: var(--text); }
svg { width: 100%; max-height: 300px; }
text { fill: var(--text-muted); font-size: var(--text-sm); }
.axis { stroke: var(--border-strong); }
.trend { stroke: var(--teal-dark); stroke-width: 2; fill: none; }
.point { fill: var(--maroon); }
summary { cursor: pointer; color: var(--text-secondary); }
</style>
