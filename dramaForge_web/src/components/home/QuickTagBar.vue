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
      class="h-[36px] px-5 rounded-[2px] text-[13px] border-2 border-[#D4C898] text-gray-600 bg-transparent hover:border-[#F5C34B] hover:text-[#F5C34B] hover:bg-[rgba(241,196,15,0.08)] transition-all cursor-pointer"
      @click="emit('select', tag)"
    >
      {{ tag }}
    </button>
  </div>
</template>
