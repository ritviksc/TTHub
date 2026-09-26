<script setup>
import { computed, ref, useId } from 'vue'
import { LABELS } from '@/utils/physicalTests.js'
import { measurementPoints } from '@/utils/measurementCharts.js'
import MeasurementChart from '@/components/charts/MeasurementChart.vue'
const props = defineProps({ assessments: Array })
const exercise = ref('tug')
const inputId = useId()
const points = computed(() => measurementPoints(props.assessments, exercise.value))
</script>

<template>
  <div>
    <div class="form-group"><label :for="inputId">Exercise to compare</label>
      <select :id="inputId" v-model="exercise"><option v-for="(label, key) in LABELS" :key="key" :value="key">{{ label }}</option></select>
    </div>
    <MeasurementChart :points="points" :title="LABELS[exercise]" :unit="exercise === 'chair' ? 'stands' : 'seconds'" />
    <p class="loading-note">Completed assessments only. Gaps mean no measurement. Chair stands requiring arms appear as zero. Changes in testing conditions can affect comparisons.</p>
  </div>
</template>
