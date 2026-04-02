<script setup lang="ts">
defineProps<{
  visible: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <Transition name="fade">
    <div v-if="visible" class="fixed inset-0 z-[90] flex items-center justify-center bg-black/30" @click.self="emit('cancel')">
      <div class="bg-white rounded-xl p-6 w-[400px] max-w-[90vw] shadow-xl">
        <h3 class="text-base font-semibold text-gray-900 mb-2">{{ title || '确认操作' }}</h3>
        <p class="text-sm text-gray-600 mb-6">{{ message }}</p>
        <div class="flex justify-end gap-3">
          <button class="btn btn-outline btn-sm" @click="emit('cancel')">
            {{ cancelText || '取消' }}
          </button>
          <button
            class="btn btn-sm"
            :class="danger ? 'bg-error text-white hover:bg-red-600' : 'btn-primary'"
            @click="emit('confirm')"
          >
            {{ confirmText || '确认' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>