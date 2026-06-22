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
    <div v-if="visible" class="fixed inset-0 z-[90] flex items-center justify-center bg-black/50" @click.self="emit('cancel')">
      <div class="bg-[#FEF9E7] rounded-[2px] p-6 w-[400px] max-w-[90vw] border-2 border-[#D4C898]" style="box-shadow: 6px 6px 0 0 rgba(0,0,0,0.4);">
        <h3 class="text-base font-semibold text-gray-900 mb-2 font-pixel tracking-wider">{{ title || '确认操作' }}</h3>
        <p class="text-sm text-gray-500 mb-6">{{ message }}</p>
        <div class="flex justify-end gap-3">
          <button class="btn btn-outline btn-sm" @click="emit('cancel')">
            {{ cancelText || '取消' }}
          </button>
          <button
            class="btn btn-sm"
            :class="danger ? 'bg-error text-white hover:bg-red-600' : 'btn-primary'"
            :style="danger ? { borderRadius: '2px', border: '3px solid #C0392B', boxShadow: '3px 3px 0 0 #C0392B' } : {}"
            @click="emit('confirm')"
          >
            {{ confirmText || '确认' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>