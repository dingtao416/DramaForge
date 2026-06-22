<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { Shot } from '@/types/shot'
import type { CharacterDetail } from '@/types/character'
import type { SceneDetail } from '@/types/scene'
import DurationSlider from './DurationSlider.vue'
import RefAutocomplete from './RefAutocomplete.vue'

const props = defineProps<{
  shot: Shot
  characters?: CharacterDetail[]
  scenes?: SceneDetail[]
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

// Character autocomplete options from asset panel
const characterOptions = computed(() =>
  (props.characters || []).map(c => ({
    id: c.id,
    name: c.name,
    thumbnail: c.reference_images?.[0],
  }))
)

const sceneOptions = computed(() =>
  (props.scenes || []).map(s => ({
    id: s.id,
    name: s.name,
    thumbnail: s.reference_images?.[0],
  }))
)

const sceneRefValue = computed({
  get: () => form.value.scene_ref || '',
  set: (val: string | string[]) => {
    form.value.scene_ref = Array.isArray(val) ? (val[0] || '') : val
  },
})

const EMOTIONS = ['紧张', '轻松', '悲伤', '欢乐', '愤怒', '恐惧', '期待', '平静', '浪漫', '悬疑']

// Selected character names (for display in multi-select)
const selectedCharacterNames = computed({
  get: () => {
    // Convert ShotCharacterRef[] to string[] for RefAutocomplete display
    const chars = form.value.characters
    if (!chars || !Array.isArray(chars)) return []
    return chars.map((c: any) => {
      const char = props.characters?.find(ch => ch.id === (c.char_id || c.id))
      return char?.name || c.name || String(c.char_id || c.id || '')
    }).filter(Boolean) as string[]
  },
  set: (val: string | string[]) => {
    const names = Array.isArray(val) ? val : [val]
    form.value.characters = names.map(name => ({ char_id: 0, name, appearance_idx: 0, action: '' }))
  },
})
</script>

<template>
  <div class="bg-[#FEF9E7] border border-[#D4C898] rounded-[2px] p-5">
    <h3 class="text-[14px] font-semibold text-gray-900 mb-4">编辑分镜</h3>

    <div class="space-y-4">
      <!-- 时间 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">时间</label>
        <select
          v-model="form.time_of_day"
          class="w-full h-[36px] px-3 border border-[#D4C898] rounded-[2px] text-[13px] outline-none focus:border-primary-500 bg-[#FEF9E7]"
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
        <RefAutocomplete
          v-model="sceneRefValue"
          type="scene"
          :options="sceneOptions"
          placeholder="输入 @ 引用场景"
          class="w-full"
        />
      </div>

      <!-- 镜头类型 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">镜头类型</label>
        <select
          v-model="form.camera_type"
          class="w-full h-[36px] px-3 border border-[#D4C898] rounded-[2px] text-[13px] outline-none focus:border-primary-500 bg-[#FEF9E7]"
        >
          <option value="close_up">特写</option>
          <option value="medium">中景</option>
          <option value="full">全景</option>
          <option value="wide">远景</option>
          <option value="extreme_close">大特写</option>
          <option value="over_shoulder">过肩</option>
          <option value="pov">主观视角</option>
          <option value="aerial">航拍</option>
        </select>
      </div>

      <!-- 角度描述 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">角度描述</label>
        <input
          v-model="form.camera_angle"
          class="w-full h-[36px] px-3 border border-[#D4C898] rounded-[2px] text-[13px] outline-none focus:border-primary-500"
          placeholder="如：从舞台正下方略俯视角度拍摄"
        />
      </div>

      <!-- 动作/背景 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">动作描述</label>
        <textarea
          v-model="form.background"
          rows="2"
          class="w-full px-3 py-2 border border-[#D4C898] rounded-[2px] text-[13px] outline-none focus:border-primary-500 resize-y"
          placeholder="描述角色的动作、表情等"
        />
      </div>

      <!-- 台词 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">台词</label>
        <textarea
          v-model="form.dialogue"
          rows="2"
          class="w-full px-3 py-2 border border-[#D4C898] rounded-[2px] text-[13px] outline-none focus:border-primary-500 resize-y"
          placeholder="输入角色台词"
        />
      </div>

      <!-- 音色 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">音色</label>
        <input
          v-model="form.voice_style"
          class="w-full h-[36px] px-3 border border-[#D4C898] rounded-[2px] text-[13px] outline-none focus:border-primary-500"
          placeholder="如：男声，青年音色"
        />
      </div>

      <!-- 情绪 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-2">情绪</label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="emo in EMOTIONS"
            :key="emo"
            type="button"
            class="text-[12px] px-3 py-1.5 rounded-full border transition-all cursor-pointer"
            :class="form.emotion === emo
              ? 'bg-primary-500 text-white border-primary-500'
              : 'bg-gray-50 text-gray-600 border-[#D4C898] hover:border-primary-300 hover:text-primary-600'"
            @click="form.emotion = form.emotion === emo ? '' : emo"
          >{{ emo }}</button>
        </div>
      </div>

      <!-- 旁白 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">配音旁白</label>
        <textarea
          v-model="form.narration"
          rows="2"
          class="w-full px-3 py-2 border border-[#D4C898] rounded-[2px] text-[13px] outline-none focus:border-primary-500 resize-y"
          placeholder="输入配音旁白文本（独立于角色台词）"
        />
      </div>

      <!-- 角色 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">角色</label>
        <RefAutocomplete
          v-model="selectedCharacterNames"
          type="character"
          :options="characterOptions"
          :multiple="true"
          placeholder="输入 @ 添加角色"
          class="w-full"
        />
      </div>

      <!-- 运镜 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">运镜</label>
        <select
          v-model="form.camera_movement"
          class="w-full h-[36px] px-3 border border-[#D4C898] rounded-[2px] text-[13px] outline-none focus:border-primary-500 bg-[#FEF9E7]"
        >
          <option value="static">静止</option>
          <option value="pan">摇</option>
          <option value="tilt">俯仰</option>
          <option value="zoom_in">推进</option>
          <option value="zoom_out">拉远</option>
          <option value="dolly">推轨</option>
          <option value="tracking">跟踪</option>
          <option value="handheld">手持</option>
        </select>
      </div>

      <!-- 时长 -->
      <div>
        <label class="block text-[13px] font-medium text-gray-700 mb-1">时长 ({{ form.duration }}s)</label>
        <DurationSlider v-model="form.duration" :min="0.5" :max="15" />
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center justify-end gap-3 mt-5 pt-4 border-t border-[#D4C898]">
      <button class="btn btn-outline btn-sm" @click="emit('cancel')">取消</button>
      <button class="btn btn-primary btn-sm" @click="handleSave">保存</button>
    </div>
  </div>
</template>
