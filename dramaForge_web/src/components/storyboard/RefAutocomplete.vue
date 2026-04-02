<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface RefOption {
  id: number
  name: string
  thumbnail?: string
  role?: string
  type?: string
}

const props = defineProps<{
  modelValue: string | string[]
  type: 'character' | 'scene'
  options: RefOption[]
  multiple?: boolean
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | string[]]
}>()

const inputValue = ref('')
const showDropdown = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

const filtered = computed(() => {
  const q = inputValue.value.replace('@', '').toLowerCase()
  if (!q) return props.options
  return props.options.filter(o => o.name.toLowerCase().includes(q))
})

function onInput() {
  if (inputValue.value.includes('@') || inputValue.value.length > 0) {
    showDropdown.value = true
  }
}

function select(item: RefOption) {
  if (props.multiple) {
    const current = Array.isArray(props.modelValue) ? [...props.modelValue] : []
    if (!current.includes(item.name)) {
      current.push(item.name)
    }
    emit('update:modelValue', current)
  } else {
    emit('update:modelValue', item.name)
  }
  inputValue.value = ''
  showDropdown.value = false
}

function selectFirst() {
  if (filtered.value.length) {
    select(filtered.value[0])
  }
}

function removeTag(name: string) {
  if (props.multiple && Array.isArray(props.modelValue)) {
    emit('update:modelValue', props.modelValue.filter(v => v !== name))
  }
}

function handleBlur() {
  // Delay to allow click on dropdown items
  setTimeout(() => { showDropdown.value = false }, 200)
}
</script>

<template>
  <div class="ref-autocomplete relative">
    <!-- Selected tags (multiple mode) -->
    <div v-if="multiple && Array.isArray(modelValue) && modelValue.length" class="flex flex-wrap gap-1 mb-1.5">
      <span
        v-for="name in modelValue"
        :key="name"
        class="inline-flex items-center gap-1 bg-primary-50 text-primary-600 text-[12px] px-2 py-0.5 rounded-full"
      >
        <span>{{ type === 'character' ? '🎭' : '🖼' }}</span>
        <span>{{ name }}</span>
        <button class="ml-0.5 hover:text-primary-800 cursor-pointer" @click="removeTag(name)">×</button>
      </span>
    </div>

    <!-- Single value display -->
    <div v-if="!multiple && modelValue && !showDropdown" class="flex items-center gap-1">
      <span class="inline-flex items-center gap-1 bg-primary-50 text-primary-600 text-[12px] px-2 py-0.5 rounded-full cursor-pointer" @click="showDropdown = true">
        <span>{{ type === 'character' ? '🎭' : '🖼' }}</span>
        <span>{{ modelValue }}</span>
      </span>
    </div>

    <!-- Input -->
    <input
      v-show="multiple || !modelValue || showDropdown"
      ref="inputRef"
      v-model="inputValue"
      class="w-full h-[32px] px-3 border border-gray-200 rounded-[8px] text-[13px] outline-none focus:border-primary-500 bg-white transition-colors"
      :placeholder="placeholder || `输入 @ 引用${type === 'character' ? '角色' : '场景'}`"
      @input="onInput"
      @focus="showDropdown = true"
      @blur="handleBlur"
      @keydown.enter.prevent="selectFirst"
    />

    <!-- Dropdown -->
    <Transition name="fade">
      <div
        v-if="showDropdown && filtered.length"
        class="absolute z-50 top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-[8px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] max-h-[200px] overflow-y-auto"
      >
        <div
          v-for="item in filtered"
          :key="item.id"
          class="flex items-center gap-2.5 px-3 py-2 hover:bg-gray-50 cursor-pointer transition-colors"
          @mousedown.prevent="select(item)"
        >
          <div class="w-6 h-6 rounded-[4px] bg-gray-100 overflow-hidden shrink-0">
            <img v-if="item.thumbnail" :src="item.thumbnail" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full flex items-center justify-center text-[10px] text-gray-400">
              {{ type === 'character' ? '👤' : '🏠' }}
            </div>
          </div>
          <span class="text-[13px] text-gray-800">@{{ item.name }}</span>
          <span v-if="item.role || item.type" class="text-[11px] text-gray-400 ml-auto">{{ item.role || item.type }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>
