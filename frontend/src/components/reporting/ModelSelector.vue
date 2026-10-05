<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { getReportModels } from '@/apis.js'
const props = defineProps({ modelValue: String, disabled: Boolean })
const emit = defineEmits(['update:modelValue'])
const models = ref([]), loading = ref(true), error = ref('')
let active = true
onBeforeUnmount(() => { active = false })
async function load() {
  loading.value = true; error.value = ''
  try {
    const result = await getReportModels()
    if (!active) return
    models.value = result.models
    if (!models.value.includes(props.modelValue)) emit('update:modelValue', result.default || '')
    if (!models.value.length) error.value = 'No AI models are available. Statistics are still available.'
  } catch {
    if (active) error.value = 'Could not load AI models. Please try again.'
  } finally { if (active) loading.value = false }
}
onMounted(load)
</script>

<template>
  <div class="form-group">
    <label for="report-ai-model">AI model</label>
    <select id="report-ai-model" :value="modelValue" :disabled="disabled || loading || !models.length"
      @change="emit('update:modelValue', $event.target.value)">
      <option v-if="!models.length" value="">{{ loading ? 'Loading models…' : 'No models available' }}</option>
      <option v-for="model in models" :key="model" :value="model">{{ model }}</option>
    </select>
    <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    <button class="btn-cancel" type="button" :disabled="disabled || loading" @click="load">{{ loading ? 'Loading models…' : 'Refresh models' }}</button>
  </div>
</template>
