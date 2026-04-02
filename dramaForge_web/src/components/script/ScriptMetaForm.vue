<script setup lang="ts">
import { computed } from 'vue'
import type { ScriptDetail } from '@/types/script'

const props = defineProps<{
  script: ScriptDetail
}>()

const emit = defineEmits<{
  update: [field: string, value: string]
}>()

const fields = computed(() => [
  { key: 'protagonist', label: '主角', value: props.script.protagonist },
  { key: 'genre', label: '故事类型', value: props.script.genre },
  { key: 'synopsis', label: '故事梗概', value: props.script.synopsis },
  { key: 'background', label: '故事背景', value: props.script.background },
  { key: 'setting', label: '故事设定', value: props.script.setting },
  { key: 'one_liner', label: '一句话故事', value: props.script.one_liner },
])
</script>

<template>
  <div class="bg-white border border-gray-200 rounded-[12px] p-6">
    <h2 class="text-[16px] font-semibold text-gray-900 mb-5">剧本摘要</h2>

    <div class="space-y-6">
      <div v-for="field in fields" :key="field.key">
        <div class="text-[14px] font-medium text-gray-900 mb-1">{{ field.label }}</div>
        <div
          class="text-[14px] text-gray-600 leading-[1.8] whitespace-pre-wrap cursor-text rounded-lg px-3 py-2 -mx-3 hover:bg-gray-50 transition-colors"
          contenteditable="true"
          @blur="(e: Event) => emit('update', field.key, (e.target as HTMLElement).textContent || '')"
        >{{ field.value || '未设置' }}</div>
      </div>
    </div>
  </div>
</template>
