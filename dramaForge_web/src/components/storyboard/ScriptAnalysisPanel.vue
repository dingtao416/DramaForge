<script setup lang="ts">
import { ref } from 'vue'
import type { CharacterDetail } from '@/types/character'
import type { SegmentDetail } from '@/types/segment'

const props = defineProps<{
  synopsis?: string
  background?: string
  setting?: string
  genre?: string
  protagonist?: string
  characters?: CharacterDetail[]
  segments?: SegmentDetail[]
}>()

const collapsed = ref(false)

const roleLabel: Record<string, string> = {
  protagonist: '主角',
  supporting: '配角',
  antagonist: '反派',
  extra: '群演',
  narrator: '旁白',
}
</script>

<template>
  <div class="sa-root" :class="{ collapsed }">
    <!-- Toggle bar -->
    <div class="sa-toggle" @click="collapsed = !collapsed">
      <svg
        class="sa-toggle-icon"
        :class="{ rotated: !collapsed }"
        width="14" height="14" viewBox="0 0 14 14" fill="none"
      >
        <path d="M5 2.5L9.5 7L5 11.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span class="sa-toggle-label">📖 剧本解析</span>
      <span v-if="props.protagonist" class="sa-toggle-sub">— {{ props.protagonist }} · {{ props.genre || '未分类' }}</span>
    </div>

    <!-- Content -->
    <div v-if="!collapsed" class="sa-content">
      <!-- Col 1: 世界观 -->
      <div class="sa-col">
        <div class="sa-col-title">🌍 世界观</div>
        <div class="sa-col-body">
          <div v-if="props.background" class="sa-item">
            <span class="sa-item-label">背景</span>
            <span class="sa-item-text line-clamp-3">{{ props.background }}</span>
          </div>
          <div v-if="props.setting" class="sa-item">
            <span class="sa-item-label">设定</span>
            <span class="sa-item-text line-clamp-3">{{ props.setting }}</span>
          </div>
          <div v-if="props.synopsis" class="sa-item">
            <span class="sa-item-label">梗概</span>
            <span class="sa-item-text line-clamp-2">{{ props.synopsis }}</span>
          </div>
          <div v-if="!props.background && !props.setting && !props.synopsis" class="sa-empty">
            暂无世界观数据
          </div>
        </div>
      </div>

      <!-- Col 2: 人物设定 -->
      <div class="sa-col">
        <div class="sa-col-title">👥 人物设定</div>
        <div class="sa-col-body">
          <div v-if="props.protagonist" class="sa-item">
            <span class="sa-role-tag lead">主角</span>
            <span class="sa-item-text">{{ props.protagonist }}</span>
          </div>
          <template v-if="props.characters?.length">
            <div v-for="char in props.characters" :key="char.id" class="sa-item sa-item--row">
              <span class="sa-role-tag" :class="char.role || 'supporting'">
                {{ roleLabel[char.role] || char.role || '配角' }}
              </span>
              <span class="sa-item-text truncate">{{ char.name }}</span>
              <span v-if="char.description" class="sa-item-desc truncate">{{ char.description.slice(0, 40) }}</span>
            </div>
          </template>
          <div v-if="!props.protagonist && !props.characters?.length" class="sa-empty">
            暂无人物数据
          </div>
        </div>
      </div>

      <!-- Col 3: 风格 & 时间线 -->
      <div class="sa-col">
        <div class="sa-col-title">🎨 风格 &amp; 结构</div>
        <div class="sa-col-body">
          <div v-if="props.genre" class="sa-item">
            <span class="sa-item-label">类型</span>
            <span class="sa-genre-tag">{{ props.genre }}</span>
          </div>
          <template v-if="props.segments?.length">
            <div v-for="(seg, i) in props.segments" :key="seg.id" class="sa-item sa-item--row">
              <span class="sa-time-dot" />
              <span class="sa-item-text text-[12px]">片段 {{ i + 1 }}</span>
              <span class="sa-item-desc text-[11px]">{{ seg.shots?.length || 0 }} 个分镜</span>
              <span v-if="seg.duration" class="sa-item-desc text-[11px]">{{ seg.duration }}s</span>
            </div>
          </template>
          <div v-if="!props.genre && !props.segments?.length" class="sa-empty">
            暂无结构数据
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sa-root {
  border-bottom: 1px solid #FDF4D8;
  background: #fafbfc;
  transition: all 0.2s;
  flex-shrink: 0;
}
.sa-root.collapsed {
  background: #FEF9E7;
}

.sa-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}
.sa-toggle:hover {
  background: #f0f0f5;
}

.sa-toggle-icon {
  color: #999;
  transition: transform 0.2s;
  flex-shrink: 0;
}
.sa-toggle-icon.rotated {
  transform: rotate(90deg);
}

.sa-toggle-label {
  font-size: 13px;
  font-weight: 600;
  color: #333;
}
.sa-toggle-sub {
  font-size: 12px;
  color: #999;
  margin-left: 4px;
}

.sa-content {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0;
  border-top: 1px solid #FDF4D8;
}

.sa-col {
  padding: 12px 16px;
  border-right: 1px solid #FDF4D8;
  min-height: 80px;
}
.sa-col:last-child {
  border-right: none;
}

.sa-col-title {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
}

.sa-col-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sa-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.sa-item--row {
  flex-direction: row;
  align-items: center;
  gap: 6px;
}

.sa-item-label {
  font-size: 10px;
  color: #aaa;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.sa-item-text {
  font-size: 12px;
  color: #444;
  line-height: 1.6;
}

.sa-item-desc {
  font-size: 11px;
  color: #999;
  flex-shrink: 0;
}

.sa-role-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 2px;
  background: #f3f4f6;
  color: #666;
  flex-shrink: 0;
}
.sa-role-tag.lead, .sa-role-tag.protagonist {
  background: rgba(232, 163, 23, 0.1);
  color: #E8A317;
}
.sa-role-tag.antagonist {
  background: #FEE2E2;
  color: #DC2626;
}

.sa-genre-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 2px;
  background: #FFF7ED;
  color: #EA580C;
  display: inline-block;
  align-self: flex-start;
}

.sa-time-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #D4C898;
  flex-shrink: 0;
}

.sa-empty {
  font-size: 12px;
  color: #ccc;
  font-style: italic;
}
</style>
