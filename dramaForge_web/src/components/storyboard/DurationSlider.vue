<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelValue?: number
  min?: number
  max?: number
  step?: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const minVal = computed(() => props.min ?? 0.5)
const maxVal = computed(() => props.max ?? 15)
const stepVal = computed(() => props.step ?? 0.5)
const value = computed(() => props.modelValue ?? 3)

const percentage = computed(() =>
  ((value.value - minVal.value) / (maxVal.value - minVal.value)) * 100
)

function onInput(e: Event) {
  const v = parseFloat((e.target as HTMLInputElement).value)
  emit('update:modelValue', v)
}
</script>

<template>
  <div class="flex items-center gap-3">
    <span class="text-[12px] text-gray-400 w-7 text-right">{{ minVal }}s</span>
    <div class="flex-1 relative">
      <input
        type="range"
        :value="value"
        :min="minVal"
        :max="maxVal"
        :step="stepVal"
        class="slider w-full"
        @input="onInput"
      />
      <div
        class="absolute top-1/2 left-0 h-1 bg-primary-500 rounded-full pointer-events-none -translate-y-1/2"
        :style="{ width: `${percentage}%` }"
      />
    </div>
    <span class="text-[12px] text-gray-400 w-8">{{ maxVal }}s</span>
  </div>
</template>

<style scoped>
.slider {
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  background: #e8e8e8;
  border-radius: 2px;
  outline: none;
  position: relative;
  z-index: 1;
}
.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #7C3AED;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.15);
  cursor: pointer;
  position: relative;
  z-index: 2;
}
.slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #7C3AED;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.15);
  cursor: pointer;
}
</style>
