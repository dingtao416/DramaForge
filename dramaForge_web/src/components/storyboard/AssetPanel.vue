<script setup lang="ts">
import { computed } from 'vue'
import { DEFAULT_SCENE_IMAGE } from '@/constants/defaultAssets'
import type { CharacterDetail } from '@/types/character'
import type { SceneDetail } from '@/types/scene'
import { firstReferenceImageUrl } from '@/utils/referenceImages'

const props = defineProps<{
  characters: CharacterDetail[]
  scenes: SceneDetail[]
  selectedCharacterId?: number
  selectedSceneId?: number
  lockedCharacterIds?: Set<number>
}>()

const emit = defineEmits<{
  selectCharacter: [char: CharacterDetail]
  selectScene: [scene: SceneDetail]
  selectNarrator: []
  addAsset: []
  toggleLock: [charId: number]
}>()

const totalAssets = computed(() => props.characters.length + props.scenes.length)

function sceneThumb(scene: SceneDetail): string {
  return firstReferenceImageUrl(scene.reference_images)
}

function characterThumb(character: CharacterDetail): string {
  return firstReferenceImageUrl(character.reference_images)
}
</script>

<template>
  <aside class="asset-panel">
    <div class="asset-shell">
      <header class="asset-head">
        <div class="asset-scope" aria-label="资产范围">
          <button class="asset-scope-btn active" type="button">本集</button>
          <button class="asset-scope-btn" type="button" disabled title="暂未接入全集资产源">全集</button>
        </div>

        <button class="asset-add-btn" type="button" title="添加资产" @click="emit('addAsset')">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
            <path d="M7.5 3.2v8.6M3.2 7.5h8.6" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
          </svg>
        </button>
      </header>

      <div class="asset-type-row" aria-label="资产类型">
        <span class="asset-type active">角色</span>
        <span class="asset-type active">场景</span>
        <span class="asset-type disabled" title="暂未接入素材数据源">素材</span>
        <span class="asset-type disabled" title="暂未接入道具数据源">道具</span>
      </div>

      <div class="asset-count-row">
        <span>{{ totalAssets }} 个资产</span>
        <span>{{ characters.length }} 角色 / {{ scenes.length }} 场景</span>
      </div>

      <div class="asset-scroll">
        <section class="asset-section asset-section--characters">
          <div class="asset-section-title">
            <span>角色</span>
            <span>{{ characters.length }}</span>
          </div>

          <div v-if="characters.length" class="character-grid">
            <button
              v-for="char in characters"
              :key="char.id"
              class="character-card"
              :class="{
                selected: props.selectedCharacterId === char.id,
                locked: props.lockedCharacterIds?.has(char.id),
              }"
              type="button"
              @click="emit('selectCharacter', char)"
            >
              <span class="asset-lock" :title="props.lockedCharacterIds?.has(char.id) ? '已锁定，点击解锁' : '锁定此角色'" @click.stop="emit('toggleLock', char.id)">
                <svg v-if="props.lockedCharacterIds?.has(char.id)" width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                  <rect x="2.5" y="5.5" width="8" height="5.8" rx="1.3" stroke="currentColor" stroke-width="1.2"/>
                  <path d="M4.1 5.5V4a2.4 2.4 0 014.8 0v1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                <svg v-else width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                  <rect x="2.5" y="5.5" width="8" height="5.8" rx="1.3" stroke="currentColor" stroke-width="1.2"/>
                  <path d="M4.1 5.5V4.2a2.3 2.3 0 014.2-1.3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
              </span>

              <span class="character-thumb">
                <img
                  v-if="characterThumb(char)"
                  :src="characterThumb(char)"
                  :alt="char.name"
                  loading="lazy"
                />
                <span v-else class="thumb-placeholder">
                  <svg width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden="true">
                    <circle cx="13" cy="9" r="4" stroke="currentColor" stroke-width="1.4"/>
                    <path d="M5.8 22c1-4 3.4-6 7.2-6s6.2 2 7.2 6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
                  </svg>
                </span>
              </span>
              <span class="asset-name" :title="char.name">{{ char.name }}</span>
              <span v-if="props.lockedCharacterIds?.has(char.id)" class="asset-state">已锁定</span>
            </button>
          </div>

          <div v-else class="asset-empty">暂无角色资产</div>
        </section>

        <section class="asset-section asset-section--scenes">
          <div class="asset-section-title">
            <span>场景</span>
            <span>{{ scenes.length }}</span>
          </div>

          <div v-if="scenes.length" class="scene-list">
            <button
              v-for="scene in scenes"
              :key="scene.id"
              class="scene-card"
              :class="{ selected: props.selectedSceneId === scene.id }"
              type="button"
              @click="emit('selectScene', scene)"
            >
              <span class="scene-thumb">
                <img
                  v-if="sceneThumb(scene)"
                  :src="sceneThumb(scene)"
                  :alt="scene.name"
                  loading="lazy"
                />
                <img
                  v-else
                  :src="DEFAULT_SCENE_IMAGE"
                  :alt="`${scene.name} 默认场景图`"
                  loading="lazy"
                />
              </span>
              <span class="asset-name" :title="scene.name">{{ scene.name }}</span>
            </button>
          </div>

          <div v-else class="asset-empty">暂无场景资产</div>
        </section>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.asset-panel {
  width: 254px;
  flex-shrink: 0;
  border-right: 1px solid rgba(168, 130, 60, 0.32);
  background:
    linear-gradient(180deg, #fff6d9 0%, #f4e7c4 100%),
    repeating-linear-gradient(0deg, rgba(93, 52, 12, 0.035) 0, rgba(93, 52, 12, 0.035) 1px, transparent 1px, transparent 10px);
  min-height: 0;
  overflow: hidden;
}

.asset-shell {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.asset-head {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  flex-shrink: 0;
}

.asset-scope {
  display: flex;
  align-items: center;
  gap: 16px;
}

.asset-scope-btn {
  position: relative;
  border: 0;
  background: transparent;
  color: #9a8050;
  font-size: 13px;
  font-weight: 600;
  line-height: 30px;
  cursor: pointer;
}

.asset-scope-btn.active {
  color: #2d2515;
}

.asset-scope-btn.active::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: 2px;
  height: 2px;
  border-radius: 2px;
  background: #2d2515;
}

.asset-scope-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.asset-add-btn {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 6px;
  background: #fff7db;
  color: #2d2515;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(80, 47, 13, 0.1);
  transition: all 0.15s ease;
}

.asset-add-btn:hover {
  color: #7a1f12;
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(80, 47, 13, 0.12);
}

.asset-type-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  padding: 0 14px 10px;
  flex-shrink: 0;
}

.asset-type {
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(168, 130, 60, 0.24);
  border-radius: 6px;
  background: rgba(255, 250, 232, 0.78);
  color: #2d2515;
  font-size: 12px;
  font-weight: 600;
}

.asset-type.disabled {
  color: #b9a980;
  background: rgba(255, 255, 255, 0.32);
}

.asset-count-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px 8px;
  color: #8c7247;
  font-size: 11px;
  flex-shrink: 0;
}

.asset-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0 14px 18px;
}

.asset-section + .asset-section {
  margin-top: 16px;
}

.asset-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 24px;
  color: #5d4a2a;
  font-size: 12px;
  font-weight: 700;
}

.character-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.character-card,
.scene-card {
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.character-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  min-width: 0;
  padding: 0;
  border-radius: 8px;
}

.character-thumb,
.scene-thumb {
  position: relative;
  display: block;
  overflow: hidden;
  background: #eadfca;
  border: 1px solid rgba(168, 130, 60, 0.16);
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

.character-thumb {
  aspect-ratio: 1 / 1;
  border-radius: 8px;
}

.scene-thumb {
  aspect-ratio: 16 / 9;
  border-radius: 8px;
}

.character-thumb img,
.scene-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-placeholder {
  width: 100%;
  height: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #b49b64;
}

.character-card:hover .character-thumb,
.scene-card:hover .scene-thumb,
.character-card.selected .character-thumb,
.scene-card.selected .scene-thumb {
  border-color: #2d2515;
  box-shadow: 0 0 0 1px rgba(45, 37, 21, 0.18), 0 8px 18px rgba(80, 47, 13, 0.12);
}

.character-card.locked .character-thumb {
  border-color: #E8A317;
  box-shadow: 0 0 0 2px rgba(232, 163, 23, 0.22);
}

.asset-lock {
  position: absolute;
  top: 7px;
  right: 7px;
  z-index: 2;
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: rgba(255, 247, 219, 0.9);
  color: #806a3b;
  opacity: 0;
  transition: opacity 0.15s ease, color 0.15s ease, background 0.15s ease;
}

.character-card:hover .asset-lock,
.character-card.locked .asset-lock {
  opacity: 1;
}

.character-card.locked .asset-lock {
  color: #2D2515;
  background: #E8A317;
}

.asset-name {
  display: block;
  min-width: 0;
  padding: 6px 4px 0;
  color: #3f321e;
  font-size: 11px;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.asset-state {
  display: block;
  padding: 1px 4px 0;
  color: #E8A317;
  font-size: 10px;
  font-weight: 600;
}

.scene-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.scene-card {
  display: block;
  min-width: 0;
}

.asset-empty {
  min-height: 86px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed rgba(168, 130, 60, 0.42);
  border-radius: 8px;
  color: #9a8050;
  font-size: 12px;
  background: rgba(255, 250, 232, 0.48);
}

@media (hover: none) {
  .asset-lock {
    opacity: 1;
  }
}
</style>
