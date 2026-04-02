<script setup lang="ts">
defineProps<{
  modelValue: 'dialogue' | 'narration'
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: 'dialogue' | 'narration']
  convert: []
}>()
</script>

<template>
  <div class="flex items-center gap-3">
    <div class="flex border border-gray-200 rounded-lg overflow-hidden">
      <button
        class="px-4 py-2 text-[13px] font-medium transition-colors"
        :class="modelValue === 'dialogue' ? 'bg-gray-900 text-white' : 'bg-white text-gray-500 hover:bg-gray-50'"
        @click="emit('update:modelValue', 'dialogue')"
      >
        对话型
      </button>
      <button
        class="px-4 py-2 text-[13px] font-medium transition-colors"
        :class="modelValue === 'narration' ? 'bg-gray-900 text-white' : 'bg-white text-gray-500 hover:bg-gray-50'"
        @click="emit('update:modelValue', 'narration')"
      >
        旁白型
      </button>
    </div>

    <button
      class="btn btn-outline btn-sm text-[13px]"
      :disabled="loading"
      @click="emit('convert')"
    >
      <span v-if="loading" class="w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
      <span v-else>🔄</span>
      改写为{{ modelValue === 'dialogue' ? '旁白型' : '对话型' }}
    </button>
  </div>
</template>
