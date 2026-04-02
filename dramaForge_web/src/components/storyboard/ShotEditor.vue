<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Shot } from '@/types/shot'
import DurationSlider from './DurationSlider.vue'

const props = defineProps<{
  shot: Shot
}>()

const emit = defineEmits<{
  save: [data: Partial<Shot>]
  cancel: []
}>()

const form = ref<Partial<Shot>>({})

watch(() => props.shot, (s) => {
  form.value = { ...s }
}, { immediate: true, deep: true })

function handleSave() {
  emit('save', form.value)
}
</script>

<template>
  <div class="bg-white border border-gray-200 rounded-[12px] p-5">
    <h3 class="text-[14px] font-semibold text-gray-900 mb-4">编辑分镜</h3>

    <div class="space-y-4">
      <!-- 时间 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">时间</label>
        <select
          v-model="form.time_of_day"
          class="w-full h-[36px] px-3 border border-gray-200 rounded-[8px] text-[13px] outline-none focus:border-primary-500 bg-white"
        >
          <option value="日">日</option>
          <option value="夜">夜</option>
          <option value="黄昏">黄昏</option>
          <option value="清晨">清晨</option>
        </select>
      </div>

      <!-- 场景 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">场景</label>
        <input
          v-model="form.scene_ref"
          class="w-full h-[36px] px-3 border border-gray-200 rounded-[8px] text-[13px] outline-none focus:border-primary-500"
          placeholder="输入 @ 引用场景"
        />
      </div>

      <!-- 镜头类型 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">镜头类型</label>
        <select
          v-model="form.camera_type"
          class="w-full h-[36px] px-3 border border-gray-200 rounded-[8px] text-[13px] outline-none focus:border-primary-500 bg-white"
        >
          <option value="close_up">特写</option>
          <option value="medium">中景</option>
          <option value="wide">远景</option>
          <option value="extreme_close_up">极特写</option>
          <option value="extreme_wide">极远景</option>
          <option value="over_shoulder">过肩</option>
        </select>
      </div>

      <!-- 角度描述 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">角度描述</label>
        <input
          v-model="form.camera_angle"
          class="w-full h-[36px] px-3 border border-gray-200 rounded-[8px] text-[13px] outline-none focus:border-primary-500"
          placeholder="如：从舞台正下方略俯视角度拍摄"
        />
      </div>

      <!-- 动作/背景 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">动作描述</label>
        <textarea
          v-model="form.background"
          rows="2"
          class="w-full px-3 py-2 border border-gray-200 rounded-[8px] text-[13px] outline-none focus:border-primary-500 resize-y"
          placeholder="描述角色的动作、表情等"
        />
      </div>

      <!-- 台词 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">台词</label>
        <textarea
          v-model="form.dialogue"
          rows="2"
          class="w-full px-3 py-2 border border-gray-200 rounded-[8px] text-[13px] outline-none focus:border-primary-500 resize-y"
          placeholder="输入角色台词"
        />
      </div>

      <!-- 音色 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">音色</label>
        <input
          v-model="form.voice_style"
          class="w-full h-[36px] px-3 border border-gray-200 rounded-[8px] text-[13px] outline-none focus:border-primary-500"
          placeholder="如：男声，青年音色"
        />
      </div>

      <!-- 运镜 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">运镜</label>
        <select
          v-model="form.camera_movement"
          class="w-full h-[36px] px-3 border border-gray-200 rounded-[8px] text-[13px] outline-none focus:border-primary-500 bg-white"
        >
          <option value="static">静止</option>
          <option value="pan_left">左摇</option>
          <option value="pan_right">右摇</option>
          <option value="tilt_up">上摇</option>
          <option value="tilt_down">下摇</option>
          <option value="zoom_in">推进</option>
          <option value="zoom_out">拉远</option>
          <option value="tracking">跟踪</option>
          <option value="dolly">推轨</option>
        </select>
      </div>

      <!-- 时长 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">时长 ({{ form.duration }}s)</label>
        <DurationSlider v-model="form.duration" :min="0.5" :max="15" />
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center justify-end gap-3 mt-5 pt-4 border-t border-gray-100">
      <button class="btn btn-outline btn-sm" @click="emit('cancel')">取消</button>
      <button class="btn btn-primary btn-sm" @click="handleSave">保存</button>
    </div>
  </div>
</template>
