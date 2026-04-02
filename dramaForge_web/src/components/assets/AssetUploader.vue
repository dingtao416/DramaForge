<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  upload: [file: File]
}>()

const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

function handleDrop(e: DragEvent) {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files?.length) {
    emit('upload', files[0])
  }
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    emit('upload', input.files[0])
  }
}

function triggerUpload() {
  fileInput.value?.click()
}
</script>

<template>
  <div
    class="border-2 border-dashed rounded-[12px] p-8 text-center transition-colors cursor-pointer"
    :class="isDragging ? 'border-primary-400 bg-primary-50/50' : 'border-gray-300 hover:border-gray-400'"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="handleDrop"
    @click="triggerUpload"
  >
    <input ref="fileInput" type="file" class="hidden" accept=".docx,.doc,.txt,.pdf" @change="handleFileSelect" />

    <div class="text-3xl mb-3">📤</div>
    <p class="text-[14px] text-gray-600 mb-1">支持 docx 格式，剧本字数不超过 10 万字</p>
    <p class="text-[12px] text-gray-400">可拖拽至此处上传</p>

    <button class="btn btn-primary mt-4" @click.stop="triggerUpload">
      📤 上传
    </button>
  </div>
</template>
