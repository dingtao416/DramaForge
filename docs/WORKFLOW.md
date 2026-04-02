# DramaForge v2.0 — 工作流设计文档

> **版本**: v2.0
> **日期**: 2026-04-01
> **状态**: 与后端架构 / 前端设计 / 代码结构 完全同步
> **关联文档**:
> - [后端架构](./BACKEND_ARCHITECTURE.md)
> - [前端设计](./FRONTEND_DESIGN.md)
> - [竞品分析](./XIAOYUNQUE_FEATURES.md)

---

## 目录

1. [工作流总览](#1-工作流总览)
2. [Step 1 — 剧本引擎](#2-step-1--剧本引擎)
3. [Step 2 — 资产引擎](#3-step-2--资产引擎)
4. [Step 3 — 视频引擎](#4-step-3--视频引擎)
5. [数据流转图](#5-数据流转图)
6. [AI 服务调用链](#6-ai-服务调用链)
7. [用户操作路径](#7-用户操作路径)
8. [异步任务与进度推送](#8-异步任务与进度推送)
9. [代码文件映射](#9-代码文件映射)
10. [实施路线图](#10-实施路线图)

---

## 1. 工作流总览

### 1.1 三步核心流水线

DramaForge v2.0 采用 **三步流水线架构**（对齐小云雀验证的产品逻辑），每步之间设有人工审核节点：

```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   用户输入 (故事构想 / .docx 剧本)                                      ║
║        │                                                              ║
║        ▼                                                              ║
║   ┌─────────────────────────────────────────────────────────────┐     ║
║   │  STEP 1: Script Engine (剧本引擎)                            │     ║
║   │                                                             │     ║
║   │  输入 → LLM 生成/解析 → 结构化剧本                           │     ║
║   │  产出: Script + Episode[] + 角色名列表 + 场景名列表           │     ║
║   │                                                             │     ║
║   │  📄 dramaForge_bac/app/engines/script_engine.py             │     ║
║   │  🌐 POST /api/v2/projects/{id}/script/generate              │     ║
║   │  🖥️ dramaForge_web/src/views/ScriptPage.vue                │     ║
║   └─────────────────────────┬───────────────────────────────────┘     ║
║                             │                                         ║
║                        ⏸️ 人工审核                                     ║
║                   可编辑剧本、可改写为旁白型                              ║
║                   POST /api/v2/projects/{id}/script/approve            ║
║                             │                                         ║
║                             ▼                                         ║
║   ┌─────────────────────────────────────────────────────────────┐     ║
║   │  STEP 2: Assets Engine (资产引擎)                            │     ║
║   │                                                             │     ║
║   │  角色名列表 → 并行生成角色形象图                               │     ║
║   │  场景名列表 → 并行生成场景参考图                               │     ║
║   │  产出: Character[] (含 reference_images) + SceneLocation[]  │     ║
║   │                                                             │     ║
║   │  📄 dramaForge_bac/app/engines/assets_engine.py             │     ║
║   │  🌐 POST /api/v2/projects/{id}/assets/generate              │     ║
║   │  🖥️ dramaForge_web/src/views/AssetsPage.vue                │     ║
║   └─────────────────────────┬───────────────────────────────────┘     ║
║                             │                                         ║
║                        ⏸️ 人工审核                                     ║
║                   可替换角色形象、编辑场景图、调整音色                      ║
║                   POST /api/v2/projects/{id}/assets/approve            ║
║                             │                                         ║
║                             ▼                                         ║
║   ┌─────────────────────────────────────────────────────────────┐     ║
║   │  STEP 3: Video Engine (视频引擎)                             │     ║
║   │                                                             │     ║
║   │  每集剧本 + 角色资产 + 场景资产                                │     ║
║   │    → LLM 拆分分镜脚本 (Shot[])                               │     ║
║   │    → 并行生成: 图片 / 音频 / 视频                             │     ║
║   │    → FFmpeg 合成片段 → 合成全集                               │     ║
║   │  产出: Segment[] + 合成视频                                  │     ║
║   │                                                             │     ║
║   │  📄 dramaForge_bac/app/engines/video_engine.py              │     ║
║   │  🌐 POST /api/v2/projects/{id}/episodes/{eid}/storyboard    │     ║
║   │  🖥️ dramaForge_web/src/views/StoryboardEditorPage.vue      │     ║
║   └─────────────────────────────────────────────────────────────┘     ║
║                             │                                         ║
║                        操作节点                                       ║
║                   可编辑分镜、可重新生成单个片段                          ║
║                   可预览、可导出、可合成全集                              ║
║                             │                                         ║
║                             ▼                                         ║
║                     🎬 完整短剧视频                                     ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### 1.2 设计原则

| 原则 | 说明 | 体现 |
|------|------|------|
| **三步流水线** | 剧本 → 资产 → 视频 | 对齐小云雀工作流，每步独立可回退 |
| **中台解耦** | AI Hub 屏蔽模型细节 | 上层 Engine 不关心用的是 GPT-4o 还是 DeepSeek |
| **异步优先** | 耗时任务全部异步化 | WebSocket 实时推送生成进度 |
| **资产驱动** | 角色/场景作为全局资产 | @引用系统确保一致性 |
| **可审核** | 每步之间设人工审核节点 | 前端 StepNavigator 控制流转 |
| **可重试** | 单个片段可独立重新生成 | 不影响其他已完成的片段 |

---

## 2. Step 1 — 剧本引擎

### 2.1 输入

| 输入方式 | 说明 | API |
|---------|------|-----|
| **AI 生成** | 用户输入故事构想（10~10000字） | `POST /api/v2/projects/{id}/script/generate` |
| **上传剧本** | 上传 `.docx` 文件（≤10万字） | `POST /api/v2/projects/{id}/script/upload` |

### 2.2 处理流程

```
用户输入 / .docx 文件
        │
        ▼
┌─────────────────────────┐
│  LLM 生成/解析           │  AI Hub: ai_hub.chat.ask_json()
│  (GPT-4o / DeepSeek)    │  Prompt: prompts/script_prompts.py
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  结构化输出 (JSON)       │
│                         │
│  ├─ protagonist         │  主角名
│  ├─ genre               │  故事类型
│  ├─ synopsis            │  故事梗概
│  ├─ background          │  故事背景
│  ├─ setting             │  故事设定
│  ├─ one_liner           │  一句话故事
│  ├─ episodes[]          │  分集内容
│  ├─ characters[]        │  识别的角色名列表
│  └─ scenes[]            │  识别的场景名列表
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  写入数据库              │
│  Script + Episode[]     │  models/script.py + models/episode.py
└─────────────────────────┘
```

### 2.3 产出物

| 模型 | 说明 | 数据库表 |
|------|------|---------|
| `Script` | 剧本大纲（元数据） | scripts |
| `Episode[]` | 分集内容 | episodes |
| `characters[]` (名称列表) | 传递给 Step 2 | (内存) |
| `scenes[]` (名称列表) | 传递给 Step 2 | (内存) |

### 2.4 人工审核点

| 操作 | API | 前端组件 |
|------|-----|---------|
| 编辑剧本元数据 | `PUT /api/v2/projects/{id}/script` | `ScriptMetaForm.vue` |
| 编辑分集内容 | `PUT /api/v2/projects/{id}/script` | `ScriptEditor.vue` |
| 改写为旁白型 | `POST .../script/rewrite-narration` | `NarrationToggle.vue` |
| 审核通过 → 进入 Step 2 | `POST .../script/approve` | `StepNavigator.vue` |

---

## 3. Step 2 — 资产引擎

### 3.1 输入

| 输入 | 来源 |
|------|------|
| 角色名列表 | Step 1 自动提取 |
| 场景名列表 | Step 1 自动提取 |
| 剧本原文 | 用于 LLM 理解角色/场景上下文 |
| 视频风格 | 项目设置 (真人写实/动漫/3D) |

### 3.2 处理流程

```
角色名列表 + 场景名列表
        │
        ├─── 并行 ───────────────────────┐
        │                                │
        ▼                                ▼
┌─────────────────┐            ┌─────────────────┐
│  角色形象生成     │            │  场景参考图生成    │
│                 │            │                 │
│  For each 角色:  │            │  For each 场景:  │
│  ① LLM 生成描述  │            │  ① LLM 生成描述  │
│    - 外貌描述    │            │    - 场景描述     │
│    - 性格/角色类型│            │    - 内/外/时间   │
│    - 音色描述    │            │  ② Image 生成    │
│  ② Image 生成   │            │    场景参考图     │
│    角色全身照    │            │    (可多张)      │
│                 │            │                 │
│  AI Hub:        │            │  AI Hub:        │
│  chat.ask_json()│            │  chat.ask_json()│
│  image.generate()│           │  image.generate()│
└────────┬────────┘            └────────┬────────┘
         │                              │
         ├──────────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  写入数据库 + 保存图片    │
│  Character[] +           │  models/character.py
│  SceneLocation[]         │  models/scene.py
│                         │  services/storage.py
│  storage/projects/{id}/  │
│    characters/           │
│    scenes/               │
└─────────────────────────┘
```

### 3.3 产出物

| 模型 | 字段 | 说明 |
|------|------|------|
| `Character` | name, role, description, voice_desc, reference_images[] | 角色资产 |
| `SceneLocation` | name, description, time_of_day, interior, reference_images[] | 场景资产 |

### 3.4 人工审核点

| 操作 | API | 前端组件 |
|------|-----|---------|
| 查看角色列表 | `GET /api/v2/projects/{id}/characters` | `CharacterCard.vue` |
| 编辑角色 | `PUT .../characters/{cid}` | `CharacterEditModal.vue` |
| 重新生成角色形象 | `POST .../characters/{cid}/regenerate` | `CharacterCard.vue` |
| 查看场景列表 | `GET /api/v2/projects/{id}/scenes` | `SceneCard.vue` |
| 编辑场景 | `PUT .../scenes/{sid}` | `SceneEditModal.vue` |
| 重新生成场景图 | `POST .../scenes/{sid}/regenerate` | `SceneCard.vue` |
| 审核通过 → 进入 Step 3 | `POST .../assets/approve` | `StepNavigator.vue` |

### 3.5 关键设计：资产全局复用

```
Step 2 生成的角色和场景是 全局资产：
  ┌─────────────────────────────────────────┐
  │  Project 级别                           │
  │                                         │
  │  Character: 沈念安 (ref_images: [...])  │──→ 所有集共用
  │  Character: 顾承泽 (ref_images: [...])  │──→ 所有集共用
  │  SceneLocation: 宴会厅 (images: [...])  │──→ 所有集共用
  │                                         │
  │  在 Step 3 中通过 @引用 绑定到分镜       │
  └─────────────────────────────────────────┘
```

---

## 4. Step 3 — 视频引擎

### 4.1 输入

| 输入 | 来源 |
|------|------|
| Episode[] | Step 1 产出 |
| Character[] | Step 2 产出 |
| SceneLocation[] | Step 2 产出 |

### 4.2 处理流程（单集）

```
Episode 剧本 + Character[] + SceneLocation[]
        │
        ▼
┌─────────────────────────────────────────┐
│  ① LLM 拆分分镜脚本                      │
│                                         │
│  AI Hub: ai_hub.chat.ask_json()         │
│  Prompt: prompts/storyboard_prompts.py  │
│                                         │
│  产出: Shot[] (每个 Shot 包含:)          │
│    - duration (0~15s)                   │
│    - time_of_day (日/夜)                │
│    - scene_ref (@场景名)                │
│    - camera_type (特写/中景/远景)        │
│    - camera_angle (角度描述)             │
│    - camera_movement (静止/推/拉/摇)     │
│    - characters (@角色名+动作)           │
│    - dialogue (台词)                    │
│    - voice_style (音色描述)              │
│    - background (背景描述)              │
│    - transition (切换方式)              │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│  ② @引用解析                             │
│                                         │
│  services/ref_resolver.py               │
│                                         │
│  @沈念安 → Character.description         │
│  @宴会厅 → SceneLocation.description     │
│                                         │
│  产出: 完整的 image_prompt / video_prompt │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│  ③ 并行生成资产 (per Shot)               │
│                                         │
│  ┌──────────┐  ┌──────────┐             │
│  │ 图片生成  │  │ 音频生成  │  ← 并行     │
│  │          │  │          │             │
│  │ ai_hub.  │  │ ai_hub.  │             │
│  │ image.   │  │ tts.     │             │
│  │ generate │  │ speak    │             │
│  └────┬─────┘  └────┬─────┘             │
│       │              │                   │
│       ▼              ▼                   │
│  shot.image_url  shot.audio_url          │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│  ④ 视频策略决策                          │
│                                         │
│  camera_movement == STATIC ?            │
│    ├─ Yes → 静态合成 (图片+音频→FFmpeg)   │
│    └─ No  → AI 视频生成                  │
│             ├─ 有参考图 → img2video      │
│             └─ 无参考图 → text2video     │
│                                         │
│  AI Hub: ai_hub.video.generate()        │
│  FFmpeg: services/ffmpeg.py             │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│  ⑤ 片段合成                             │
│                                         │
│  多个 Shot → 一个 Segment 视频           │
│  services/ffmpeg.py (拼接+转场+字幕)     │
│                                         │
│  产出: segment.video_url                │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│  ⑥ 全集合成                             │
│                                         │
│  多个 Segment → 一集完整视频             │
│  services/ffmpeg.py (合并+BGM+片头片尾)  │
│                                         │
│  产出: episode.final_video_url          │
└─────────────────────────────────────────┘
```

### 4.3 产出物

| 模型 | 说明 | 存储路径 |
|------|------|---------|
| `Shot` | 最小分镜单元 | `storage/projects/{id}/episodes/{n}/shots/` |
| `Segment` | 片段视频 | `storage/projects/{id}/episodes/{n}/segments/` |
| 全集视频 | 合成的完整集视频 | `storage/projects/{id}/episodes/{n}/final.mp4` |

### 4.4 操作节点

| 操作 | API | 前端组件 |
|------|-----|---------|
| 查看分集列表 | `GET /api/v2/projects/{id}/episodes` | `EpisodeCard.vue` |
| 生成分镜脚本 | `POST .../episodes/{eid}/storyboard` | `EpisodeList.vue` |
| 查看分镜脚本 | `GET .../episodes/{eid}/storyboard` | `StoryboardScript.vue` |
| 编辑单个分镜 | `PUT .../episodes/{eid}/shots/{sid}` | `ShotCard.vue` |
| 生成单片段 | `POST .../segments/{sid}/generate` | `Timeline.vue` |
| 重新生成片段 | `POST .../segments/{sid}/regenerate` | `Timeline.vue` |
| 合成全集 | `POST .../episodes/{eid}/compose` | 顶栏"合成全集"按钮 |
| 导出 | `POST /api/v2/projects/{id}/export` | 顶栏"导出"按钮 |

---

## 5. 数据流转图

### 5.1 模型关系

```
Project (1个项目 = 1部剧)
  │
  ├── Script (1:1)           ← Step 1 产出
  │     └── Episode[] (1:N)   ← Step 1 产出
  │
  ├── Character[] (1:N)      ← Step 2 产出 (全局资产)
  │
  ├── SceneLocation[] (1:N)  ← Step 2 产出 (全局资产)
  │
  └── Episode → Segment[] (1:N)   ← Step 3 产出
                  └── Shot[] (1:N)  ← Step 3 产出 (最小单元)
```

### 5.2 数据流转

```
         Step 1                Step 2                  Step 3
     ┌───────────┐        ┌───────────┐          ┌───────────────┐
     │           │        │           │          │               │
     │  Script   │───────→│Character[]│──────┐   │  Shot[]       │
     │  Episode[]│───┐    │SceneLoc[] │──┐   │   │  Segment[]    │
     │           │   │    │           │  │   │   │  final.mp4    │
     └───────────┘   │    └───────────┘  │   │   └───────────────┘
                     │                   │   │         ▲
                     │    characters     │   │         │
                     └────names[]────────┘   └─────────┘
                          scenes              @引用绑定
                          names[]
```

### 5.3 文件存储结构

```
storage/projects/{project_id}/
├── script/
│   └── script.json              ← Step 1
├── characters/
│   ├── {char_id}_0.png          ← Step 2
│   └── {char_id}_1.png
├── scenes/
│   ├── {scene_id}_0.png         ← Step 2
│   └── {scene_id}_1.png
└── episodes/
    └── {episode_num}/
        ├── storyboard.json      ← Step 3.①
        ├── shots/
        │   ├── shot_01_img.png  ← Step 3.③
        │   ├── shot_01_audio.mp3
        │   └── shot_01_video.mp4
        ├── segments/
        │   ├── segment_01.mp4   ← Step 3.⑤
        │   └── segment_02.mp4
        └── final.mp4            ← Step 3.⑥
```

---

## 6. AI 服务调用链

### 6.1 每步使用的 AI Hub 服务

| 步骤 | AI Hub 服务 | 模型 | 调用方式 |
|------|------------|------|---------|
| **Step 1** | `ai_hub.chat.ask_json()` | GPT-4o / DeepSeek-V3 | 同步 |
| **Step 1** | `ai_hub.chat.ask()` | GPT-4o | 同步 (旁白改写) |
| **Step 2** | `ai_hub.chat.ask_json()` | GPT-4o | 同步 (角色/场景描述) |
| **Step 2** | `ai_hub.image.generate()` | sora-image | 同步 (角色形象图) |
| **Step 2** | `ai_hub.image.generate()` | sora-image | 同步 (场景参考图) |
| **Step 3** | `ai_hub.chat.ask_json()` | GPT-4o | 同步 (分镜拆解) |
| **Step 3** | `ai_hub.image.generate()` | sora-image | 异步任务 (分镜图片) |
| **Step 3** | `ai_hub.tts.speak()` | tts-1-hd | 异步任务 (台词音频) |
| **Step 3** | `ai_hub.video.generate()` | veo-3.1-fast | 异步任务 (AI 视频) |
| **Step 3** | `ai_hub.prompt.optimize()` | GPT-4o | 同步 (提示词优化) |

### 6.2 费用估算（per 集）

| 资源 | 数量 | 单价 | 小计 |
|------|------|------|------|
| LLM (剧本+分镜) | ~3 次 | ~$0.02/次 | $0.06 |
| 图片 (角色+场景+分镜) | ~15 张 | $0.01/张 | $0.15 |
| TTS (台词) | ~8 段 | ~$0.01/段 | $0.08 |
| 视频 (AI 生成) | ~4 段 (选择性) | ~$0.30/段 | $1.20 |
| **纯图片模式** | - | - | **~$0.30/集** |
| **混合视频模式** | - | - | **~$1.50/集** |

---

## 7. 用户操作路径

### 7.1 完整路径

```
首页 (HomePage)
  │
  │  输入故事构想 / 上传剧本
  │  选择风格 + 比例
  │  点击"开始创作"
  │
  ▼
创建项目 → 自动进入 Step 1
  │
  ▼
ScriptPage (剧本大纲)          ← /projects/{id}/script
  │
  │  查看/编辑剧本元数据
  │  查看/编辑分集内容
  │  [可选] 改写为旁白型
  │  点击"下一步"
  │
  ▼
AssetsPage (角色与场景)         ← /projects/{id}/assets
  │
  │  查看自动生成的角色列表
  │  查看自动生成的场景列表
  │  [可选] 编辑/重新生成任意角色或场景
  │  点击"下一步"
  │
  ▼
EpisodesPage (分集视频列表)     ← /projects/{id}/episodes
  │
  │  查看所有集的概览
  │  点击某集的"编辑"按钮
  │
  ▼
StoryboardEditorPage (分镜编辑器) ← /projects/{id}/episodes/{epId}/storyboard
  │
  │  左栏: 资产面板 (角色+场景)
  │  中栏: 分镜脚本 (可编辑每个 Shot)
  │  右栏: 视频预览
  │  底栏: 时间线 (片段缩略图)
  │
  │  操作:
  │  ├─ 编辑分镜参数 (时长/镜头/台词/运镜)
  │  ├─ 重新生成单个片段
  │  ├─ 合成全集
  │  └─ 导出
  │
  ▼
🎬 完成
```

### 7.2 前端页面与后端 API 对照

| 前端页面 | 路由 | 核心后端 API | 后端 Engine |
|---------|------|-------------|------------|
| `HomePage.vue` | `/` | `POST /projects` | - |
| `ScriptPage.vue` | `/projects/{id}/script` | `POST/GET/PUT .../script` | `ScriptEngine` |
| `AssetsPage.vue` | `/projects/{id}/assets` | `POST/GET .../assets` | `AssetsEngine` |
| `EpisodesPage.vue` | `/projects/{id}/episodes` | `GET .../episodes` | - |
| `StoryboardEditorPage.vue` | `/projects/{id}/episodes/{epId}/storyboard` | `POST/GET/PUT .../storyboard` | `VideoEngine` |
| `AssetLibraryPage.vue` | `/assets` | `GET/POST/DELETE /assets` | - |

---

## 8. 异步任务与进度推送

### 8.1 任务分类

| 任务类型 | 触发时机 | 预计耗时 | 并行度 | 代码文件 |
|---------|---------|---------|--------|---------|
| `generate_script` | Step 1 创建 | 10~30s | 1 | `tasks/asset_tasks.py` |
| `generate_character_image` | Step 2 创建 | 5~15s | ✅ N并行 | `tasks/asset_tasks.py` |
| `generate_scene_image` | Step 2 创建 | 5~15s | ✅ N并行 | `tasks/asset_tasks.py` |
| `split_storyboard` | Step 3 按集触发 | 10~20s | ✅ 按集并行 | `tasks/video_tasks.py` |
| `generate_shot_assets` | Step 3 按片段触发 | 5~15s | ✅ 图片+音频并行 | `tasks/video_tasks.py` |
| `generate_segment_video` | Step 3 按片段触发 | 30~120s | ✅ 限并发3 | `tasks/video_tasks.py` |
| `compose_episode` | 用户点击"合成全集" | 10~30s | 1 | `tasks/video_tasks.py` |

### 8.2 WebSocket 推送协议

```
WS /api/v2/ws/tasks/{task_id}
```

| 消息类型 | 字段 | 说明 |
|---------|------|------|
| `progress` | task_id, step, current, total, message | 进度更新 |
| `completed` | task_id, result | 任务完成 |
| `error` | task_id, error | 任务失败 |

前端通过 `stores/tasks.ts` + `api/websocket.ts` 管理 WebSocket 连接和进度状态。

---

## 9. 代码文件映射

### 9.1 后端 (`dramaForge_bac/`)

```
app/
├── main.py                          # FastAPI 入口
├── core/
│   ├── config.py                    # 全局配置 (Settings)
│   ├── database.py                  # SQLAlchemy 异步引擎
│   └── security.py                  # JWT 认证
│
├── models/                          # ORM 数据模型 (7个)
│   ├── project.py                   # Project
│   ├── script.py                    # Script
│   ├── episode.py                   # Episode
│   ├── character.py                 # Character
│   ├── scene.py                     # SceneLocation
│   ├── segment.py                   # Segment
│   └── shot.py                      # Shot
│
├── schemas/                         # Pydantic 请求/响应模型
│   ├── project.py                   # ProjectCreate, ProjectDetail
│   ├── script.py                    # ScriptGenerateRequest
│   ├── assets.py                    # CharacterUpdate, SceneUpdate
│   ├── episode.py                   # EpisodeOverview
│   └── storyboard.py               # ShotUpdate, StoryboardDetail
│
├── engines/                         # ⭐ 三步流水线引擎
│   ├── script_engine.py             # Step 1: 剧本引擎
│   ├── assets_engine.py             # Step 2: 资产引擎
│   └── video_engine.py              # Step 3: 视频引擎
│
├── ai_hub/                          # AI 中台 (已实现)
│   ├── _client.py                   # BaseClient (HTTP+OpenAI+Retry)
│   ├── _models.py                   # 数据模型
│   ├── chat.py                      # ChatService
│   ├── image.py                     # ImageService
│   ├── tts.py                       # TTSService
│   ├── video.py                     # VideoService (多模型fallback)
│   ├── prompt.py                    # PromptService (待实现)
│   └── __init__.py                  # ai_hub 单例门面
│
├── api/v2/                          # REST API 端点
│   ├── projects.py                  # 项目 CRUD
│   ├── scripts.py                   # 剧本生成/编辑
│   ├── assets.py                    # 资产生成/管理
│   ├── episodes.py                  # 分集管理
│   ├── storyboard.py               # 分镜编辑
│   └── websocket.py                # WS 任务推送
│
├── services/                        # 业务服务
│   ├── storage.py                   # 文件存储管理
│   ├── ref_resolver.py              # @引用解析器
│   └── ffmpeg.py                    # FFmpeg 合成
│
├── tasks/                           # 异步任务
│   ├── asset_tasks.py               # 资产生成任务
│   └── video_tasks.py               # 视频生成任务
│
└── prompts/                         # LLM 提示词模板
    ├── script_prompts.py            # 剧本生成 (已实现)
    ├── storyboard_prompts.py        # 分镜拆解 (已实现)
    └── character_prompts.py         # 角色描述 (待实现)
```

### 9.2 前端 (`dramaForge_web/`)

```
src/
├── views/                           # 页面视图 (9个)
│   ├── HomePage.vue                 # 首页入口
│   ├── ProjectListPage.vue          # 项目列表
│   ├── ProjectLayout.vue            # 项目布局容器
│   ├── ScriptPage.vue               # Step 1 剧本
│   ├── AssetsPage.vue               # Step 2 资产
│   ├── EpisodesPage.vue             # Step 3 分集列表
│   ├── StoryboardEditorPage.vue     # ⭐ 分镜编辑器
│   ├── AssetLibraryPage.vue         # 资产库
│   └── SettingsPage.vue             # 设置
│
├── components/                      # 业务组件 (34个)
│   ├── common/      (6)            # 通用: Header, Sidebar, StepNavigator...
│   ├── home/        (4)            # 首页: CreationInput, QuickTagBar...
│   ├── script/      (4)            # 剧本: ScriptEditor, EpisodeAccordion...
│   ├── assets/      (5)            # 资产: CharacterCard, SceneCard...
│   ├── storyboard/  (10)           # ⭐ 分镜: ShotCard, Timeline, RefAutocomplete...
│   ├── episodes/    (2)            # 分集: EpisodeCard, EpisodeList
│   └── library/     (3)            # 资产库: AssetGrid, AssetFilter...
│
├── stores/          (6)            # Pinia: project, script, assets, storyboard, timeline, tasks
├── api/             (7)            # Axios: client, projects, scripts, assets, episodes, storyboard, websocket
├── types/           (8)            # TS类型: project, script, character, scene, episode, segment, shot, enums
└── utils/           (3)            # 工具: format, time, prompt
```

---

## 10. 实施路线图

### Phase 1 — 基础搭建 (Week 1~2)

| 任务 | 优先级 | 涉及文件 |
|------|--------|---------|
| 数据库模型实现 | P0 | `models/*.py`, `core/database.py` |
| Pydantic Schema 实现 | P0 | `schemas/*.py` |
| 项目 CRUD API | P0 | `api/v2/projects.py` |
| 前端路由 + 基础布局 | P0 | `router.ts`, `ProjectLayout.vue`, `AppHeader.vue` |
| 前端 API 客户端 | P0 | `api/client.ts` |

### Phase 2 — Step 1 剧本引擎 (Week 2~3)

| 任务 | 优先级 | 涉及文件 |
|------|--------|---------|
| ScriptEngine 实现 | P0 | `engines/script_engine.py` |
| 剧本 API 端点 | P0 | `api/v2/scripts.py` |
| ScriptPage 前端 | P0 | `ScriptPage.vue`, `ScriptEditor.vue`, `ScriptMetaForm.vue` |
| StepNavigator 组件 | P0 | `StepNavigator.vue` |

### Phase 3 — Step 2 资产引擎 (Week 3~4)

| 任务 | 优先级 | 涉及文件 |
|------|--------|---------|
| AssetsEngine 实现 | P0 | `engines/assets_engine.py` |
| 角色/场景 API | P0 | `api/v2/assets.py` |
| AssetsPage 前端 | P0 | `AssetsPage.vue`, `CharacterCard.vue`, `SceneCard.vue` |
| StorageService 实现 | P0 | `services/storage.py` |

### Phase 4 — Step 3 视频引擎 (Week 4~6)

| 任务 | 优先级 | 涉及文件 |
|------|--------|---------|
| VideoEngine 分镜拆解 | P0 | `engines/video_engine.py` |
| RefResolver 引用解析 | P0 | `services/ref_resolver.py` |
| 异步任务系统 | P0 | `tasks/video_tasks.py` |
| WebSocket 推送 | P0 | `api/v2/websocket.py`, `api/websocket.ts` |
| StoryboardEditorPage | P0 | 分镜编辑器全部 10 个组件 |
| FFmpeg 合成 | P1 | `services/ffmpeg.py` |

### Phase 5 — 打磨与上线 (Week 6~8)

| 任务 | 优先级 | 涉及文件 |
|------|--------|---------|
| 资产库全局管理 | P1 | `AssetLibraryPage.vue` |
| 提示词优化服务 | P1 | `ai_hub/prompt.py` |
| Docker 部署 | P1 | `docker-compose.yml` |
| 错误处理与边界情况 | P1 | 全局 |
| 性能优化与测试 | P2 | `tests/` |

---

> **文档版本管理**:
> 本文档与 `BACKEND_ARCHITECTURE.md`、`FRONTEND_DESIGN.md` 保持同步。
> 当任何一份文档的设计发生变更时，需同步更新其余文档。
>
> **同步校验点**:
> - 三步流水线：三份文档中一致 ✅
> - 数据模型 (7个)：后端架构 ↔ 工作流 一致 ✅
> - API 端点 (28个)：后端架构 ↔ 工作流 一致 ✅
> - 前端页面 (9个)：前端设计 ↔ 工作流 一致 ✅
> - 前端组件 (34个)：前端设计 ↔ 工作流 一致 ✅
> - AI Hub 服务 (6个)：后端架构 ↔ 工作流 一致 ✅
> - 代码文件路径：工作流 ↔ 实际目录结构 一致 ✅