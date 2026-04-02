<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  sortOrder?: string
}>()

const emit = defineEmits<{
  filter: [filters: Record<string, string>]
  sort: [order: string]
}>()

const showFilterPanel = ref(false)
const selectedType = ref('')
const selectedDate = ref('')

function applyFilter() {
  emit('filter', {
    type: selectedType.value,
    date: selectedDate.value,
  })
  showFilterPanel.value = false
}

function resetFilter() {
  selectedType.value = ''
  selectedDate.value = ''
  emit('filter', {})
  showFilterPanel.value = false
}
</script>

<template>
  <div class="relative">
    <button
      class="h-[32px] px-3 rounded-[8px] text-[13px] text-gray-500 hover:bg-gray-100 cursor-pointer transition-colors flex items-center gap-1 border border-gray-200"
      @click="showFilterPanel = !showFilterPanel"
    >
      🔽 筛选
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M3.5 4.5L6 7L8.5 4.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </button>

    <!-- Filter panel -->
    <Transition name="fade">
      <div
        v-if="showFilterPanel"
        class="absolute top-full right-0 mt-2 w-[260px] bg-white border border-gray-200 rounded-[12px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] p-4 z-50"
      >
        <h4 class="text-[13px] font-medium text-gray-800 mb-3">筛选条件</h4>

        <!-- Type -->
        <div class="mb-3">
          <label class="block text-[12px] text-gray-500 mb-1">资产类型</label>
          <select
            v-model="selectedType"
            class="w-full h-[32px] px-2 border border-gray-200 rounded-[6px] text-[13px] outline-none focus:border-primary-500 bg-white"
          >
            <option value="">全部</option>
            <option value="character">角色</option>
            <option value="scene">场景</option>
            <option value="image">图片</option>
          </select>
        </div>

        <!-- Date range -->
        <div class="mb-4">
          <label class="block text-[12px] text-gray-500 mb-1">时间范围</label>
          <select
            v-model="selectedDate"
            class="w-full h-[32px] px-2 border border-gray-200 rounded-[6px] text-[13px] outline-none focus:border-primary-500 bg-white"
          >
            <option value="">不限</option>
            <option value="today">今天</option>
            <option value="week">最近7天</option>
            <option value="month">最近30天</option>
          </select>
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-end gap-2">
          <button class="text-[12px] text-gray-400 hover:text-gray-600 cursor-pointer" @click="resetFilter">重置</button>
          <button class="btn btn-primary btn-sm text-[12px]" @click="applyFilter">确定</button>
        </div>
      </div>
    </Transition>
  </div>
</template>
