# DramaForge 对话框功能需求与实现方案

> 基于当前 UI 设计，系统梳理对话框涉及的全部功能模块、前后端交互设计和实现方案
> 更新日期：2026-04-03

---

## 一、功能需求总览

### 1.1 功能模块全景图

```
┌─────────────────────────────────────────────────────────────────┐
│                        对话框 (ChatBox)                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ [Textarea 输入区]                                        │   │
│  │  · 多行文本输入                                           │   │
│  │  · 动态 placeholder（随模式切换）                          │   │
│  │  · @引用素材（沉浸式短片模式）                              │   │
│  │  · 快捷键支持（Enter 发送 / Shift+Enter 换行）             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ [工具栏 Toolbar]                                         │   │
│  │                                                          │   │
│  │  左侧（动态）:                                            │   │
│  │  ① 上传素材  ② 模式切换  ③ 模型偏好  ④ @引用             │   │
│  │  ⑤ 画幅比例  ⑥ 参考风格  ⑦ 时长选择  ⑧ 创作偏好          │   │
│  │  ⑨ 预设提示词                                            │   │
│  │                                                          │   │
│  │  右侧（固定）:                                            │   │
│  │  ⑩ 一键优化提示词  ⑪ 发送按钮                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 功能优先级

| 优先级 | 功能模块 | 说明 |
|--------|---------|------|
| **P0 核心** | 文本输入 + 发送 | 用户输入提示词并提交创作请求 |
| **P0 核心** | 模式切换 | 切换 6 种创作模式，动态改变工具栏 |
| **P0 核心** | 上传素材 | 本地上传 + 资产库选择，作为创作参考 |
| **P1 重要** | 模型偏好 | 选择视频/图片生成模型 |
| **P1 重要** | 画幅比例 | 设置输出画面比例 |
| **P1 重要** | 一键优化提示词 | AI 自动优化用户输入的提示词 |
| **P2 增强** | 预设提示词 | CRUD 管理常用提示词模板 |
| **P2 增强** | @引用素材 | 在输入框中 @ 引用已有素材 |
| **P2 增强** | 参考风格 | 上传/选择参考图，控制生成风格 |
| **P2 增强** | 时长选择 | 设置视频生成时长 |
| **P3 锦上添花** | 创作偏好 | 智能长视频 2.0 专属参数设置 |
| **P3 锦上添花** | 快捷标签 | 首页快捷标签一键填入 |

---

## 二、各功能模块详细设计

### 2.1 文本输入 + 发送（P0）

#### 功能需求
- 多行文本输入，自动扩展高度（最大 5 行）
- Enter 发送，Shift+Enter 换行
- 发送时携带当前所有设置参数（模式、模型、比例等）
- 发送后清空输入框，显示 loading 状态
- 空内容时发送按钮禁用

#### 实现方案

```typescript
// ─── 类型定义 ─── 
interface CreationRequest {
  mode: Mode                          // 创作模式
  prompt: string                      // 用户提示词
  model?: string                      // 选择的模型（null 则后端自动选）
  aspectRatio?: string                // 画幅比例
  duration?: number                   // 视频时长（秒）
  referenceAssetIds?: string[]        // 上传/引用的素材 ID 列表
  styleReferenceId?: string           // 风格参考素材 ID
  presetId?: string                   // 使用的预设 ID
}

// ─── API 接口 ─── 
// POST /api/v1/creations
// Body: CreationRequest
// Response: { id: string, status: 'pending', redirectUrl: string }
```

```typescript
// ─── 前端实现 ─── 
async function startCreation() {
  if (!userInput.value.trim() || loading.value) return
  loading.value = true
  
  const request: CreationRequest = {
    mode: currentMode.value,
    prompt: userInput.value,
    model: modelAuto.value ? undefined : selectedModel.value,
    aspectRatio: selectedRatio.value === 'auto' ? undefined : selectedRatio.value,
    duration: currentMode.value === 'clip' ? selectedDuration.value : undefined,
    referenceAssetIds: uploadedAssets.value.map(a => a.id),
    styleReferenceId: styleReference.value?.id,
  }
  
  try {
    const { data } = await creationsApi.create(request)
    // 根据模式跳转不同页面
    if (request.mode === 'agent') {
      router.push(`/chat/${data.id}`)          // Agent 对话页
    } else if (request.mode === 'clip') {
      router.push(`/creations/${data.id}`)     // 生成结果页
    } else if (['longvideo', 'longvideo2'].includes(request.mode)) {
      router.push(`/projects/${data.id}/script`) // 脚本编辑页
    } else if (request.mode === 'image') {
      router.push(`/creations/${data.id}`)     // 图片结果页
    }
    userInput.value = ''
  } catch (e) {
    message.error('创作请求失败，请重试')
  } finally {
    loading.value = false
  }
}
```

**技术要点：**
- Textarea 自动高度：监听 `input` 事件，动态设置 `style.height = scrollHeight + 'px'`
- 键盘事件：`@keydown.enter.exact.prevent="startCreation"` + `@keydown.shift.enter` 换行

---

### 2.2 模式切换（P0）

#### 功能需求
- 6 种创作模式，工具栏图标动态显示/隐藏
- 短剧 Agent 直接跳转独立页面
- 切换模式时重置相关参数（模型、时长等）
- 记住用户上次选择的模式（localStorage）

#### 实现方案

```typescript
// ─── 状态管理 ─── 
// 建议使用 Pinia Store 管理，跨组件共享
// stores/chatbox.ts

export const useChatboxStore = defineStore('chatbox', () => {
  const currentMode = ref<Mode>(
    (localStorage.getItem('df_mode') as Mode) || 'agent'
  )
  
  function setMode(mode: Mode) {
    currentMode.value = mode
    localStorage.setItem('df_mode', mode)
    // 重置模式相关参数
    resetModeParams(mode)
  }
  
  function resetModeParams(mode: Mode) {
    // 切换模式时，某些参数需要重置
    if (mode !== 'clip') {
      selectedDuration.value = 10
      styleReference.value = null
    }
  }
  
  return { currentMode, setMode }
})
```

**工具栏可见性映射表（已实现，作为参考）：**

```typescript
const toolbarVisibility = computed(() => ({
  modelPreference: ['agent', 'image', 'longvideo'].includes(currentMode.value),
  atReference:     currentMode.value === 'clip',
  aspectRatio:     true, // 所有模式
  styleReference:  currentMode.value === 'clip',
  duration:        currentMode.value === 'clip',
  creationPref:    currentMode.value === 'longvideo2',
  preset:          ['agent', 'clip', 'longvideo2', 'image', 'longvideo'].includes(currentMode.value),
}))
```

---

### 2.3 上传素材（P0）

#### 功能需求
- **本地上传**：支持图片（jpg/png/webp）、视频（mp4/mov），单文件最大 100MB
- **资产库选择**：弹出资产库弹窗，选择已有素材
- 上传后在输入框上方显示素材缩略图预览
- 支持多文件上传（最多 9 个）
- 可删除已上传的素材

#### 实现方案

```typescript
// ─── 类型定义 ─── 
interface UploadedAsset {
  id: string
  name: string
  type: 'image' | 'video'
  thumbnailUrl: string
  url: string
  size: number
  uploading?: boolean
  progress?: number
}

// ─── 状态 ─── 
const uploadedAssets = ref<UploadedAsset[]>([])
const MAX_ASSETS = 9

// ─── API 接口 ─── 
// POST /api/v1/assets/upload  (multipart/form-data)
// GET  /api/v1/assets         (资产库列表，已有)

// ─── 前端实现 ─── 
async function handleLocalUpload() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*,video/mp4,video/quicktime'
  input.multiple = true
  input.onchange = async (e) => {
    const files = Array.from((e.target as HTMLInputElement).files || [])
    const remaining = MAX_ASSETS - uploadedAssets.value.length
    const toUpload = files.slice(0, remaining)
    
    for (const file of toUpload) {
      const tempAsset: UploadedAsset = {
        id: `temp_${Date.now()}`,
        name: file.name,
        type: file.type.startsWith('video') ? 'video' : 'image',
        thumbnailUrl: URL.createObjectURL(file),
        url: '',
        size: file.size,
        uploading: true,
        progress: 0,
      }
      uploadedAssets.value.push(tempAsset)
      
      try {
        const { data } = await assetsApi.upload(file, (progress) => {
          tempAsset.progress = progress
        })
        Object.assign(tempAsset, { ...data, uploading: false })
      } catch {
        uploadedAssets.value = uploadedAssets.value.filter(a => a.id !== tempAsset.id)
        message.error(`${file.name} 上传失败`)
      }
    }
  }
  input.click()
}

function handleAssetSelect(assets: Asset[]) {
  // 从资产库弹窗回调
  const remaining = MAX_ASSETS - uploadedAssets.value.length
  const toAdd = assets.slice(0, remaining).map(a => ({
    id: a.id,
    name: a.name,
    type: a.type,
    thumbnailUrl: a.thumbnailUrl,
    url: a.url,
    size: a.size,
  }))
  uploadedAssets.value.push(...toAdd)
}

function removeAsset(id: string) {
  uploadedAssets.value = uploadedAssets.value.filter(a => a.id !== id)
}
```

**UI 组件：** 在 Textarea 上方添加素材预览区

```html
<!-- 素材预览区 -->
<div v-if="uploadedAssets.length" class="asset-preview-bar">
  <div v-for="asset in uploadedAssets" :key="asset.id" class="asset-thumb">
    <img :src="asset.thumbnailUrl" />
    <div v-if="asset.uploading" class="upload-progress">
      <div :style="{ width: asset.progress + '%' }" />
    </div>
    <button class="remove-btn" @click="removeAsset(asset.id)">×</button>
  </div>
</div>
```

---

### 2.4 模型偏好（P1）

#### 功能需求
- 自动模式（默认开启）：后端根据提示词自动选择最优模型
- 手动模式：用户可选择指定模型
- 视频模型 Tab / 图片模型 Tab 切换
- 模型列表从后端 API 动态获取
- 选中状态持久化（localStorage）

#### 实现方案

```typescript
// ─── API 接口 ─── 
// GET /api/v1/models?type=video  → VideoModel[]
// GET /api/v1/models?type=image  → ImageModel[]

interface ModelInfo {
  id: string
  name: string
  desc: string
  type: 'video' | 'image'
  version: string
  speed: 'fast' | 'standard' | 'quality'
  isDefault: boolean
}

// ─── 状态 ─── 
const modelAuto = ref(true)
const selectedVideoModel = ref<string | null>(null)
const selectedImageModel = ref<string | null>(null)
const videoModels = ref<ModelInfo[]>([])
const imageModels = ref<ModelInfo[]>([])

// ─── 初始化加载 ─── 
onMounted(async () => {
  const [vRes, iRes] = await Promise.all([
    modelsApi.list('video'),
    modelsApi.list('image'),
  ])
  videoModels.value = vRes.data
  imageModels.value = iRes.data
  // 默认选中 isDefault 的模型
  selectedVideoModel.value = vRes.data.find(m => m.isDefault)?.id || null
  selectedImageModel.value = iRes.data.find(m => m.isDefault)?.id || null
})
```

**发送时逻辑：**
- `modelAuto: true` → 不传 model 字段，后端自动选择
- `modelAuto: false` → 根据当前模式传 `selectedVideoModel` 或 `selectedImageModel`

---

### 2.5 画幅比例（P1）

#### 功能需求
- 5 种比例选项：自动、16:9、9:16、4:3、3:4
- 单选，选中显示紫色勾
- 不同模式可能有不同的默认比例
- 选中状态持久化

#### 实现方案

```typescript
// ─── 已基本实现，补充逻辑 ─── 
const selectedRatio = ref(localStorage.getItem('df_ratio') || 'auto')

watch(selectedRatio, (val) => {
  localStorage.setItem('df_ratio', val)
})

// 发送时：
// aspectRatio: selectedRatio.value === 'auto' ? undefined : selectedRatio.value
```

**无需后端接口**，比例选项为前端固定配置，发送创作请求时作为参数传递。

---

### 2.6 一键优化提示词（P1）

#### 功能需求
- 点击后将当前输入的提示词发送给 AI 优化
- 优化过程中按钮显示 loading 动画
- 优化结果替换输入框内容（或弹窗对比选择）
- 空输入时按钮禁用

#### 实现方案

```typescript
// ─── API 接口 ─── 
// POST /api/v1/prompts/optimize
// Body: { prompt: string, mode: Mode }
// Response: { optimized: string, changes: string[] }

const optimizing = ref(false)

async function optimizePrompt() {
  if (!userInput.value.trim() || optimizing.value) return
  optimizing.value = true
  
  try {
    const { data } = await promptsApi.optimize({
      prompt: userInput.value,
      mode: currentMode.value,
    })
    // 方案 A：直接替换
    userInput.value = data.optimized
    
    // 方案 B：弹窗对比（更友好）
    // showOptimizeDialog(userInput.value, data.optimized, data.changes)
  } catch {
    message.error('优化失败，请重试')
  } finally {
    optimizing.value = false
  }
}
```

---

### 2.7 预设提示词（P2）

#### 功能需求
- **CRUD**：新建、编辑、删除预设
- **搜索**：关键词过滤
- **导入/导出**：JSON 格式
- **使用**：点击预设填入输入框
- 预设支持分类标签
- 用户级别数据（登录后云端同步）

#### 实现方案

```typescript
// ─── 类型定义 ─── 
interface Preset {
  id: string
  title: string
  content: string          // 提示词内容
  tags: string[]           // 分类标签
  mode?: Mode              // 适用模式（null = 通用）
  createdAt: string
  updatedAt: string
}

// ─── API 接口 ─── 
// GET    /api/v1/presets?search=xxx&mode=agent  → Preset[]
// POST   /api/v1/presets                         → Preset
// PUT    /api/v1/presets/:id                     → Preset
// DELETE /api/v1/presets/:id
// POST   /api/v1/presets/import  (JSON file)
// GET    /api/v1/presets/export  → JSON download

// ─── 状态 ─── 
const presets = ref<Preset[]>([])
const presetSearch = ref('')
const showPresetEditor = ref(false)
const editingPreset = ref<Preset | null>(null)

const filteredPresets = computed(() => {
  const q = presetSearch.value.toLowerCase()
  return presets.value.filter(p => 
    p.title.toLowerCase().includes(q) || p.content.toLowerCase().includes(q)
  )
})

// ─── 操作 ─── 
function usePreset(preset: Preset) {
  userInput.value = preset.content
  closeAllMenus()
}

async function createPreset(data: Partial<Preset>) {
  const { data: created } = await presetsApi.create(data)
  presets.value.unshift(created)
}

async function deletePreset(id: string) {
  await presetsApi.delete(id)
  presets.value = presets.value.filter(p => p.id !== id)
}

async function exportPresets() {
  const blob = new Blob([JSON.stringify(presets.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'dramaforge-presets.json'
  a.click()
}
```

---

### 2.8 @引用素材（P2，仅沉浸式短片）

#### 功能需求
- 输入 `@` 触发素材选择浮层
- 显示最近使用的素材 + 搜索
- 选中后在输入框中插入素材引用标记 `@[素材名](asset_id)`
- 提交时解析引用标记，提取 asset_id 列表

#### 实现方案

```typescript
// ─── 触发逻辑 ─── 
const showAtMention = ref(false)
const mentionAssets = ref<Asset[]>([])

function handleTextareaInput(e: Event) {
  const textarea = e.target as HTMLTextAreaElement
  const value = textarea.value
  const cursorPos = textarea.selectionStart
  
  // 检查光标前是否有 @
  const beforeCursor = value.slice(0, cursorPos)
  const atMatch = beforeCursor.match(/@([^@\s]*)$/)
  
  if (atMatch) {
    showAtMention.value = true
    const searchTerm = atMatch[1]
    // 过滤素材列表
    mentionAssets.value = allAssets.value.filter(a => 
      a.name.toLowerCase().includes(searchTerm.toLowerCase())
    )
  } else {
    showAtMention.value = false
  }
}

function insertMention(asset: Asset) {
  // 将 @[素材名](asset_id) 插入输入框
  const textarea = document.querySelector('.input-textarea') as HTMLTextAreaElement
  const cursorPos = textarea.selectionStart
  const value = textarea.value
  const beforeAt = value.slice(0, value.lastIndexOf('@', cursorPos))
  const after = value.slice(cursorPos)
  
  userInput.value = `${beforeAt}@[${asset.name}](${asset.id}) ${after}`
  showAtMention.value = false
}

// ─── 提交时解析 ─── 
function parseReferences(text: string): string[] {
  const regex = /@\[.*?\]\((.*?)\)/g
  const ids: string[] = []
  let match
  while ((match = regex.exec(text)) !== null) {
    ids.push(match[1])
  }
  return ids
}
```

---

### 2.9 参考风格（P2，仅沉浸式短片）

#### 功能需求
- 上传一张参考图/视频，用于控制生成风格
- 预览参考素材缩略图
- 可更换/删除

#### 实现方案

```typescript
const styleReference = ref<UploadedAsset | null>(null)

async function selectStyleReference() {
  // 复用上传逻辑，但只允许单选
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*,video/mp4'
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return
    const { data } = await assetsApi.upload(file)
    styleReference.value = data
  }
  input.click()
}

// 发送时：
// styleReferenceId: styleReference.value?.id
```

---

### 2.10 时长选择（P2，仅沉浸式短片）

#### 功能需求
- 选项：5s / 10s / 15s（默认 10s）
- 点击时长按钮弹出选择菜单
- 选中后按钮显示当前时长

#### 实现方案

```typescript
const durationOptions = [5, 10, 15]
const selectedDuration = ref(10)
const showDurationMenu = ref(false)

// 发送时：
// duration: currentMode.value === 'clip' ? selectedDuration.value : undefined
```

---

### 2.11 创作偏好（P3，仅智能长视频2.0）

#### 功能需求
- 设置分镜数量范围（4-20）
- 每个分镜时长（3-10秒）
- 画面风格偏好（写实/动画/3D/水墨等）
- 配乐偏好（无/自动/上传）

#### 实现方案

```typescript
interface CreationPreference {
  sceneCount: [number, number]    // [min, max] 分镜数量
  sceneDuration: number           // 每镜时长（秒）
  visualStyle: string             // 画面风格
  music: 'none' | 'auto' | string // 配乐
}

const creationPref = ref<CreationPreference>({
  sceneCount: [6, 12],
  sceneDuration: 5,
  visualStyle: 'realistic',
  music: 'auto',
})
```

---

## 三、后端 API 设计汇总

### 3.1 新增 API 列表

| 方法 | 路径 | 说明 | 优先级 |
|------|------|------|--------|
| `POST` | `/api/v1/creations` | 统一创作入口 | P0 |
| `GET` | `/api/v1/creations/:id` | 查询创作状态 | P0 |
| `POST` | `/api/v1/assets/upload` | 上传素材 | P0 |
| `GET` | `/api/v1/models` | 获取可用模型列表 | P1 |
| `POST` | `/api/v1/prompts/optimize` | AI 优化提示词 | P1 |
| `GET` | `/api/v1/presets` | 获取预设列表 | P2 |
| `POST` | `/api/v1/presets` | 创建预设 | P2 |
| `PUT` | `/api/v1/presets/:id` | 更新预设 | P2 |
| `DELETE` | `/api/v1/presets/:id` | 删除预设 | P2 |
| `POST` | `/api/v1/presets/import` | 导入预设 | P2 |
| `GET` | `/api/v1/presets/export` | 导出预设 | P2 |

### 3.2 统一创作请求 Schema

```json
{
  "mode": "agent | clip | longvideo2 | image | longvideo",
  "prompt": "用户输入的提示词",
  "model": "seedance_2.0_fast",           // 可选，null=自动
  "aspectRatio": "16:9",                   // 可选，null=自动
  "duration": 10,                          // 可选，仅 clip 模式
  "referenceAssetIds": ["asset_xxx"],      // 可选，上传的参考素材
  "styleReferenceId": "asset_yyy",         // 可选，风格参考
  "presetId": "preset_zzz",               // 可选，使用的预设
  "creationPreference": {                  // 可选，仅 longvideo2
    "sceneCount": [6, 12],
    "sceneDuration": 5,
    "visualStyle": "realistic",
    "music": "auto"
  }
}
```

---

## 四、前端架构实现方案

### 4.1 组件拆分

当前所有逻辑集中在 `HomePage.vue`，建议拆分为独立组件：

```
components/chatbox/
├── ChatBox.vue              # 主容器（组合所有子组件）
├── ChatInput.vue            # Textarea 输入区 + 素材预览
├── ChatToolbar.vue          # 工具栏容器
├── ToolbarUpload.vue        # + 上传按钮 + 菜单
├── ToolbarModeSwitch.vue    # 模式切换按钮 + 选择浮层
├── ToolbarModelPref.vue     # 模型偏好按钮 + 面板
├── ToolbarRatio.vue         # 画幅比例按钮 + 菜单
├── ToolbarPreset.vue        # 预设提示词按钮 + 面板
├── ToolbarAtMention.vue     # @引用素材（clip 模式）
├── ToolbarReference.vue     # 参考风格（clip 模式）
├── ToolbarDuration.vue      # 时长选择（clip 模式）
├── ToolbarCreationPref.vue  # 创作偏好（longvideo2 模式）
└── ToolbarOptimize.vue      # 一键优化提示词
```

### 4.2 状态管理

```
stores/
├── chatbox.ts       # 对话框全局状态（模式、参数、素材等）
├── models.ts        # 模型列表缓存
└── presets.ts       # 预设提示词 CRUD
```

```typescript
// stores/chatbox.ts
export const useChatboxStore = defineStore('chatbox', () => {
  // ─── 核心状态 ─── 
  const currentMode = ref<Mode>('agent')
  const userInput = ref('')
  const loading = ref(false)
  
  // ─── 参数状态 ─── 
  const modelAuto = ref(true)
  const selectedVideoModel = ref<string | null>(null)
  const selectedImageModel = ref<string | null>(null)
  const selectedRatio = ref('auto')
  const selectedDuration = ref(10)
  const uploadedAssets = ref<UploadedAsset[]>([])
  const styleReference = ref<UploadedAsset | null>(null)
  const creationPref = ref<CreationPreference>(defaultPref)
  
  // ─── 计算属性 ─── 
  const currentModel = computed(() => {
    if (modelAuto.value) return null
    if (['clip', 'longvideo', 'longvideo2'].includes(currentMode.value)) {
      return selectedVideoModel.value
    }
    if (currentMode.value === 'image') return selectedImageModel.value
    return null  // agent 模式由后端决定
  })
  
  // ─── Actions ─── 
  async function submit() { ... }
  function setMode(mode: Mode) { ... }
  function reset() { ... }
  
  return { ... }
})
```

### 4.3 点击外部关闭菜单

```typescript
// composables/useClickOutside.ts
import { onMounted, onUnmounted, Ref } from 'vue'

export function useClickOutside(
  target: Ref<HTMLElement | null>,
  callback: () => void
) {
  function handler(e: MouseEvent) {
    if (target.value && !target.value.contains(e.target as Node)) {
      callback()
    }
  }
  onMounted(() => document.addEventListener('click', handler))
  onUnmounted(() => document.removeEventListener('click', handler))
}

// 使用方式：
// const toolbarRef = ref<HTMLElement>()
// useClickOutside(toolbarRef, closeAllMenus)
```

---

## 五、实施路线图

### Phase 1（1 周）— P0 核心功能

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 重构 ChatBox 组件拆分 | 2d | 从 HomePage.vue 拆出独立组件 |
| Pinia Store 状态管理 | 1d | chatbox.ts + 持久化 |
| 统一创作 API 对接 | 1d | POST /api/v1/creations |
| 本地上传 + 素材预览 | 1d | 上传、进度、预览、删除 |
| 键盘快捷键 + 自动高度 | 0.5d | Enter 发送、自适应高度 |

### Phase 2（1 周）— P1 重要功能

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 模型列表 API + 前端 | 1d | 动态加载模型，选中状态 |
| 画幅比例持久化 | 0.5d | localStorage + 发送参数 |
| 一键优化提示词 API | 1d | 后端 AI 优化 + 前端交互 |
| 资产库弹窗选择 | 1.5d | 复用 AssetLibraryPage 组件 |
| 点击外部关闭 + 动画优化 | 1d | composable + CSS transition |

### Phase 3（1-2 周）— P2 增强功能

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 预设提示词 CRUD | 2d | 新建/编辑弹窗 + API |
| 预设导入导出 | 1d | JSON 文件 |
| @引用素材 | 2d | Mention 解析 + 浮层 + 插入 |
| 参考风格上传 | 1d | 单文件选择 + 预览 |
| 时长选择菜单 | 0.5d | 下拉菜单 |

### Phase 4（1 周）— P3 锦上添花

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 创作偏好面板 | 1.5d | 滑块、选择器组件 |
| 快捷标签联动 | 0.5d | 标签点击填入 + 自动选模式 |
| 模式切换动画 | 1d | 工具栏图标过渡动画 |
| 整体性能优化 | 1d | 组件懒加载、素材缩略图优化 |

---

## 六、技术栈确认

| 层级 | 技术 |
|------|------|
| 框架 | Vue 3 + TypeScript |
| 状态管理 | Pinia（持久化插件 pinia-plugin-persistedstate） |
| HTTP | Axios（已有封装） |
| 路由 | Vue Router 4 |
| 样式 | Tailwind CSS + Scoped CSS |
| 文件上传 | 原生 File API + Axios upload |
| 动画 | CSS Transition + Animate |
