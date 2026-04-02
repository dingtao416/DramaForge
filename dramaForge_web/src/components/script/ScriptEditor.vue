<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  content: string
  readonly?: boolean
}>()

const emit = defineEmits<{
  'update:content': [value: string]
}>()

const editing = ref(false)
const editText = ref('')

function startEdit() {
  if (props.readonly) return
  editText.value = props.content
  editing.value = true
}

function saveEdit() {
  emit('update:content', editText.value)
  editing.value = false
}

function cancelEdit() {
  editing.value = false
}
</script>

<template>
  <div class="bg-white border border-gray-200 rounded-[12px]">
    <!-- View mode -->
    <div v-if="!editing" class="p-5">
      <div
        class="text-[14px] text-gray-700 leading-[1.9] whitespace-pre-wrap"
        @dblclick="startEdit"
      >{{ content || '暂无剧本内容' }}</div>

      <div v-if="!readonly" class="mt-4 flex items-center gap-2">
        <button
          class="btn btn-outline btn-sm text-[13px]"
          @click="startEdit"
        >
          ✏️ 编辑
        </button>
      </div>
    </div>

    <!-- Edit mode -->
    <div v-else class="p-5">
      <textarea
        v-model="editText"
        class="w-full min-h-[300px] border border-gray-200 rounded-lg px-4 py-3 text-[14px] text-gray-700 leading-[1.9] outline-none focus:border-primary-500 resize-y transition-colors"
        placeholder="输入剧本内容..."
      />
      <div class="mt-3 flex items-center justify-end gap-3">
        <button class="btn btn-outline btn-sm" @click="cancelEdit">取消</button>
        <button class="btn btn-primary btn-sm" @click="saveEdit">保存</button>
      </div>
    </div>
  </div>
</template>
