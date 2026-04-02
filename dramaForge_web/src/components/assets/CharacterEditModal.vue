<script setup lang="ts">
import { ref, watch } from 'vue'
import { CharacterRole, CharacterRoleLabel } from '@/types/enums'
import type { CharacterDetail } from '@/types/character'

const props = defineProps<{
  visible: boolean
  character: CharacterDetail | null
}>()

const emit = defineEmits<{
  close: []
  save: [data: Partial<CharacterDetail>]
}>()

const form = ref({
  name: '',
  role: CharacterRole.SUPPORTING as CharacterRole,
  appearance: '',
  voice_description: '',
})

watch(() => props.character, (char) => {
  if (char) {
    form.value = {
      name: char.name,
      role: char.role,
      appearance: char.appearance || '',
      voice_description: char.voice_description || '',
    }
  }
}, { immediate: true })

function handleSave() {
  emit('save', { ...form.value })
}

const roleOptions = Object.entries(CharacterRoleLabel) as [CharacterRole, string][]
</script>

<template>
  <Transition name="fade">
    <div
      v-if="visible && character"
      class="fixed inset-0 z-[90] flex items-center justify-center bg-black/30 backdrop-blur-[2px]"
      @click.self="emit('close')"
    >
      <div class="bg-white rounded-[16px] w-[520px] max-w-[90vw] max-h-[85vh] overflow-y-auto shadow-[0_12px_24px_rgba(0,0,0,0.12)]">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 class="text-[16px] font-semibold text-gray-900">
            编辑角色 — {{ character.name }}
          </h3>
          <button
            class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-gray-600 cursor-pointer transition-colors"
            @click="emit('close')"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 2L12 12M12 2L2 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          </button>
        </div>

        <!-- Body -->
        <div class="px-6 py-5 space-y-5">
          <!-- 角色名 -->
          <div>
            <label class="block text-[13px] font-medium text-gray-700 mb-1.5">角色名</label>
            <input
              v-model="form.name"
              class="w-full h-[40px] px-3 border border-gray-200 rounded-[8px] text-[14px] text-gray-800 outline-none focus:border-primary-500 transition-colors"
              placeholder="输入角色名"
            />
          </div>

          <!-- 角色类型 -->
          <div>
            <label class="block text-[13px] font-medium text-gray-700 mb-1.5">角色类型</label>
            <select
              v-model="form.role"
              class="w-full h-[40px] px-3 border border-gray-200 rounded-[8px] text-[14px] text-gray-800 outline-none focus:border-primary-500 bg-white transition-colors"
            >
              <option v-for="[key, label] in roleOptions" :key="key" :value="key">{{ label }}</option>
            </select>
          </div>

          <!-- 外貌描述 -->
          <div>
            <label class="block text-[13px] font-medium text-gray-700 mb-1.5">外貌描述</label>
            <textarea
              v-model="form.appearance"
              rows="3"
              class="w-full px-3 py-2.5 border border-gray-200 rounded-[8px] text-[14px] text-gray-800 outline-none focus:border-primary-500 resize-y transition-colors leading-[1.7]"
              placeholder="25岁，长发及腰，气质优雅，常穿白色..."
            />
          </div>

          <!-- 音色描述 -->
          <div>
            <label class="block text-[13px] font-medium text-gray-700 mb-1.5">音色描述</label>
            <textarea
              v-model="form.voice_description"
              rows="2"
              class="w-full px-3 py-2.5 border border-gray-200 rounded-[8px] text-[14px] text-gray-800 outline-none focus:border-primary-500 resize-y transition-colors leading-[1.7]"
              placeholder="女声，温柔成熟，音调中偏低，语速适中..."
            />
          </div>

          <!-- 形象图 -->
          <div>
            <label class="block text-[13px] font-medium text-gray-700 mb-1.5">形象图</label>
            <div class="flex gap-3 flex-wrap">
              <div
                v-for="(img, idx) in character.reference_images"
                :key="idx"
                class="w-20 h-24 rounded-lg overflow-hidden bg-gray-100 border border-gray-200"
              >
                <img :src="img" :alt="`形象${idx + 1}`" class="w-full h-full object-cover" />
              </div>
              <!-- 添加按钮 -->
              <button class="w-20 h-24 rounded-lg border-2 border-dashed border-gray-300 flex flex-col items-center justify-center text-gray-400 hover:border-primary-400 hover:text-primary-500 cursor-pointer transition-colors">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><line x1="10" y1="4" x2="10" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="4" y1="10" x2="16" y2="10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
                <span class="text-[10px] mt-1">添加</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
          <button class="btn btn-outline" @click="emit('close')">取消</button>
          <button class="btn btn-primary" @click="handleSave">保存并重新生成形象</button>
        </div>
      </div>
    </div>
  </Transition>
</template>
