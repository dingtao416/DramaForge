<script setup lang="ts">
import { computed } from 'vue'
import { ProjectStep } from '@/types/enums'

const props = defineProps<{
  currentStep: ProjectStep
}>()

const steps = [
  { key: ProjectStep.SCRIPT, label: '剧本大纲', num: 1 },
  { key: ProjectStep.ASSETS, label: '角色和场景', num: 2 },
  { key: ProjectStep.STORYBOARD, label: '分集视频', num: 3 },
]

const stepOrder = [ProjectStep.SCRIPT, ProjectStep.ASSETS, ProjectStep.STORYBOARD, ProjectStep.COMPLETED]
const currentIndex = computed(() => stepOrder.indexOf(props.currentStep))

function getStepState(step: typeof steps[0]) {
  const idx = stepOrder.indexOf(step.key)
  if (idx < currentIndex.value) return 'completed'
  if (idx === currentIndex.value) return 'current'
  return 'upcoming'
}
</script>

<template>
  <div class="flex items-center justify-center gap-0 py-1">
    <template v-for="(step, i) in steps" :key="step.key">
      <!-- Step indicator -->
      <div class="flex items-center gap-2.5">
        <!-- Circle / Checkmark -->
        <div
          class="w-7 h-7 rounded-full flex items-center justify-center text-[12px] font-semibold shrink-0 transition-all"
          :class="{
            'bg-primary-600 text-white shadow-[0_2px_8px_rgba(124,58,237,0.3)]': getStepState(step) === 'current',
            'bg-primary-100 text-primary-600': getStepState(step) === 'completed',
            'bg-gray-100 text-gray-400': getStepState(step) === 'upcoming',
          }"
        >
          <svg v-if="getStepState(step) === 'completed'" width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M3.5 7L6 9.5L10.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span v-else>{{ step.num }}</span>
        </div>

        <!-- Label -->
        <span
          class="text-[14px] whitespace-nowrap transition-colors"
          :class="{
            'text-gray-900 font-semibold': getStepState(step) === 'current',
            'text-primary-600 font-medium': getStepState(step) === 'completed',
            'text-gray-400': getStepState(step) === 'upcoming',
          }"
        >
          {{ step.label }}
        </span>
      </div>

      <!-- Connector dashed line -->
      <div
        v-if="i < steps.length - 1"
        class="w-24 mx-5 border-t-2 border-dashed transition-colors"
        :class="i < currentIndex ? 'border-primary-300' : 'border-gray-200'"
      />
    </template>
  </div>
</template>