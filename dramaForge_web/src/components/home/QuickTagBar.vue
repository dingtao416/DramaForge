<script setup lang="ts">
defineProps<{
  tags: string[]
}>()

const emit = defineEmits<{
  select: [tag: string]
}>()
</script>

<template>
  <div class="flex items-center justify-center gap-3 flex-wrap">
    <button
      v-for="tag in tags"
      :key="tag"
      class="h-[36px] px-5 rounded-full text-[13px] border border-gray-200 text-gray-500 bg-white hover:border-primary-300 hover:text-primary-600 hover:bg-primary-50/60 transition-all cursor-pointer"
      @click="emit('select', tag)"
    >
      {{ tag }}
    </button>
  </div>
</template>
