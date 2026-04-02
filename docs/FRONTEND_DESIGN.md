# DramaForge v2.0 — 前端设计文档

> **版本**: v2.0 Draft
> **日期**: 2026-04-01
> **参考**: [小云雀功能分析](./XIAOYUNQUE_FEATURES.md) | [后端架构](./BACKEND_ARCHITECTURE.md)

---

## 目录

1. [技术选型](#1-技术选型)
2. [整体布局设计](#2-整体布局设计)
3. [路由与页面规划](#3-路由与页面规划)
4. [核心页面设计](#4-核心页面设计)
   - 4.1 [首页 — 对话式创作入口](#41-首页--对话式创作入口)
   - 4.2 [Step 1 — 剧本大纲编辑器](#42-step-1--剧本大纲编辑器)
   - 4.3 [Step 2 — 角色与场景管理](#43-step-2--角色与场景管理)
   - 4.4 [Step 3 — 分集视频列表](#44-step-3--分集视频列表)
   - 4.5 [分镜编辑器（核心页面）](#45-分镜编辑器核心页面)
   - 4.6 [资产库](#46-资产库)
5. [组件设计](#5-组件设计)
6. [状态管理](#6-状态管理)
7. [实时通信](#7-实时通信)
8. [设计规范](#8-设计规范)

---

## 1. 技术选型

| 层级 | 技术 | 说明 |
|------|------|------|
| **框架** | Vue 3 + Composition API | 渐进式框架，生态成熟 |
| **构建** | Vite 6 | 极速 HMR |
| **语言** | TypeScript | 类型安全 |
| **路由** | Vue Router 4 | SPA 路由 |
| **状态** | Pinia | 轻量状态管理 |
| **UI 库** | Naive UI / Element Plus | 企业级组件库 |
| **样式** | TailwindCSS 4 | 原子化 CSS |
| **HTTP** | Axios + VueUse | 请求封装 |
| **WebSocket** | 原生 WS + 自动重连 | 实时任务推送 |
| **视频播放** | Video.js / xgplayer | 视频预览 |
| **拖拽** | VueDraggable+ | 时间线拖拽排序 |
| **富文本** | Tiptap | 剧本编辑 |
| **图标** | Iconify (Lucide) | 统一图标集 |

---

## 2. 整体布局设计

### 2.1 全局布局结构（对齐小云雀 02_home/03_home_full）

```
┌─────────────────────────────────────────────────────────┐
│  顶部导航栏 (56px) — 白色背景, 底部 1px #E8E8E8 边框      │
│  [Logo][品牌名]  ···flex···  [⚡0▾] [订阅] [反馈] [通知] [头像] │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│  左侧边栏  │              主内容区                        │
│  (240px)  │              (flex-1)                       │
│  白色背景  │              #FAFAFA 背景                   │
│  右边框1px │                                              │
│          │                                              │
│ +新对话   │              [Logo图标]                       │
│ 📁资产库  │   Hi, DramaForge 助你一键生成短剧             │
│          │              [输入框卡片]                      │
│ 历史记录  │              [快捷标签]                       │
│ [项目列表] │              [常用功能卡片(横向滚动)]          │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

> **顶部导航栏详情**（参考 02_home/06_project_detail 截图）：
> - 高度 56px，sticky 固定，z-index 最高
> - 左侧：Logo 图标 + 品牌名 "DramaForge"（16px, 字重 600）
> - 右侧：积分按钮（带边框圆角）+ 订阅（紫色文字）+ 反馈图标 + 通知铃铛 + 用户头像（32px 圆形）

### 2.2 布局变体

| 页面 | 左侧边栏 | 主内容区 | 右侧面板 |
|------|---------|---------|---------|
| **首页** | 历史记录列表 | 对话/创建区 | ❌ |
| **项目详情** | 步骤导航 | 步骤内容 | ❌ |
| **分镜编辑器** | 资产库面板 | 分镜脚本 | 视频预览面板 |
| **资产库** | ❌ 全宽 | 资产网格 | ❌ |

---

## 3. 路由与页面规划

```typescript
const routes = [
  // 首页 — 对话式入口
  { path: '/', name: 'Home', component: HomePage },

  // 项目列表
  { path: '/projects', name: 'Projects', component: ProjectListPage },

  // 项目详情 — 三步工作流
  {
    path: '/projects/:id',
    name: 'ProjectDetail',
    component: ProjectLayout,
    children: [
      // Step 1: 剧本
      { path: 'script', name: 'Script', component: ScriptPage },
      // Step 2: 资产
      { path: 'assets', name: 'Assets', component: AssetsPage },
      // Step 3: 分集列表
      { path: 'episodes', name: 'Episodes', component: EpisodesPage },
      // 分镜编辑器
      {
        path: 'episodes/:epId/storyboard',
        name: 'StoryboardEditor',
        component: StoryboardEditorPage
      },
    ]
  },

  // 资产库
  { path: '/assets', name: 'AssetLibrary', component: AssetLibraryPage },

  // 设置
  { path: '/settings', name: 'Settings', component: SettingsPage },
]
```

---

## 4. 核心页面设计

### 4.1 首页 — 对话式创作入口

**参考截图**: `02_home.png`、`03_home_full.png`、`11_agent_modes.png`

```
┌──────────┬──────────────────────────────────────────────┐
│          │                                              │
│  左侧边栏  │              主内容区                        │
│  240px   │                                              │
│          │   [48px Logo 图标]                            │
│ + 新对话  │   Hi, DramaForge 助你一键生成短剧（28-32px粗体）│
│ 📁 资产库 │                                              │
│          │   ┌──────────────────────────────────────┐   │
│ 历史记录  │   │  告诉我，你今天想创造一点什么？         │   │
│  全部    │   │  (placeholder, 多行文本域)              │   │
│          │   │                                        │   │
│ 更早     │   │  ┌工具栏─────────────────────────────┐│   │
│ [头像+名] │   │  │[+] [🌐Agent模式▾] [📊模型▾]       ││   │
│ [头像+名] │   │  │[田 网格] [窗 窗口]     [✨] [⬆发送]││   │
│          │   │  └───────────────────────────────────┘│   │
│          │   └──────────────────────────────────────┘   │
│          │                                              │
│          │   [都市甜宠] [古装权谋] [悬疑探案] [女频逆袭]    │
│          │                                              │
│          │   常用功能                                     │
│          │   ┌─────────┐┌─────────┐┌─────────┐┌────┐[>]│
│          │   │ 短剧Agent││Seedance ││ 爆款复刻 ││一镜 │   │
│          │   │ New标签  ││ 2.0     ││         ││到底 │   │
│          │   │ 背景图   ││ 背景图  ││ 背景图   ││背景 │   │
│          │   └─────────┘└─────────┘└─────────┘└────┘   │
└──────────┴──────────────────────────────────────────────┘
```

**左侧边栏详情**（参考 02_home 截图）：
- 宽 240px，白色背景，右边框 1px `#E8E8E8`
- `+ 新对话` 按钮：满宽，高 40px，圆角 8px，浅灰背景 + 深色文字
- `📁 资产库` 链接：图标+文字，14px 灰色
- `历史记录` 标题：12px 灰色，右侧 "全部" 链接
- 项目条目：32px 圆形头像 + 两行文字（标题+副标题），hover 背景变浅
- 右上角：侧边栏折叠按钮

**主内容区 — 输入框详情**（参考 02_home / 12_hit_clone 截图）：
- 外框：白色卡片，圆角 12px，浅色阴影，hover/focus 时边框变紫色
- 文本域：无边框，placeholder 灰色
- 工具栏（底部两行）：
  - 左侧：`[+]` 附件 → `[🌐 Agent 模式 ▾]` → `[📊 模型 ▾]` → `[田]` 网格 → `[窗]` 窗口
  - 右侧：`[✨]` 设置 → `[⬆]` 发送按钮（36px 圆形，无内容灰色，有内容黑/紫色）

**常用功能卡片详情**（参考 02_home 底部截图）：
- 标题 `常用功能`：16px 粗体，左对齐
- 横向排列，可滚动，右侧 `>` 箭头按钮
- 每张卡片：240×140px，**真实背景图 + 暗色渐变蒙层**
  - 左下角：白色标题（16px 粗体）+ 白色副标题（12px）
  - 可选 `New` 绿色小徽标（左上角）

**交互流程**:
1. 用户在输入框描述故事构想，或上传 `.docx` 剧本
2. 选择视频风格（真人写实/动漫/3D）和画面比例（16:9/9:16）
3. 点击"开始创作" → 创建项目 → 进入 Step 1 剧本页

**关键组件**:
- `CreationInput` — 多行文本输入框 + 底部工具栏（含 Agent 模式/模型选择）
- `QuickTagBar` — 胶囊快捷标签栏（border-radius 999px）
- `ProjectHistory` — 左侧历史项目列表（带头像缩略图）
- `FeatureCards` — 常用功能卡片（带背景图+渐变蒙层+标题，横向滚动）

---

### 4.2 Step 1 — 剧本大纲编辑器

**参考**: 小云雀剧本大纲页

```
┌──────────┬──────────────────────────────────────────────┐
│          │                                              │
│  步骤导航  │  📋 剧本大纲                                 │
│          │                                              │
│ ① 剧本 ●│  ┌─ 剧本元数据 ─────────────────────────┐    │
│ ② 资产   │  │ 视频风格: [真人写实 ▼]  画面比例: [16:9 ▼] │    │
│ ③ 视频   │  │ 主角: 沈念安    故事类型: [女频 ▼]       │    │
│          │  │ 一句话故事: [编辑框]                    │    │
│          │  │ 故事梗概: [编辑框]                      │    │
│          │  │ 故事背景: [编辑框]                      │    │
│          │  │ 故事设定: [编辑框]                      │    │
│          │  └──────────────────────────────────────┘    │
│          │                                              │
│          │  ┌─ 剧本内容 ──────────────────────────┐     │
│          │  │ 第1集 · 订婚惊变妹妹夺爱              │     │
│          │  │ ──────────────────────────           │     │
│          │  │ 1-1 日 内 豪华酒店宴会厅              │     │
│          │  │ 人物：司仪, 沈念安, 顾承泽            │     │
│          │  │ △ 璀璨的水晶吊灯下，...               │     │
│          │  │ 司仪（微笑）：今天，是沈家千金...      │     │
│          │  │ ...                                  │     │
│          │  │                                      │     │
│          │  │ 第2集 · 碎梦订婚宴                    │     │
│          │  │ ...                                  │     │
│          │  └──────────────────────────────────────┘     │
│          │                                              │
│          │  [改写为旁白型]            [上一步] [下一步 →] │
└──────────┴──────────────────────────────────────────────┘
```

**关键组件**:
- `StepNavigator` — 左侧三步骤导航（带当前步骤高亮）
- `ScriptMetaForm` — 剧本元数据编辑表单
- `ScriptEditor` — 富文本剧本编辑器（Tiptap）
- `EpisodeAccordion` — 分集折叠面板

**交互**:
- 所有元数据字段可在线编辑
- "改写为旁白型" 按钮调用 API 一键转换
- "下一步" 需确认（审核通过），进入 Step 2

---

### 4.3 Step 2 — 角色与场景管理

**参考截图**: `06_project_detail.png`（角色）、`07_scenes.png`（场景）

```
┌──────────┬──────────────────────────────────────────────┐
│          │                                              │
│  步骤导航  │  [全部角色 11] [全部场景 4]                    │
│          │                                              │
│ ① 剧本   │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐    │
│ ② 资产 ● │  │      │  │      │  │      │  │      │    │
│ ③ 视频   │  │ 沈念安 │  │ 顾承泽 │  │ 沈薇薇 │  │ 沈母  │    │
│          │  │ 主角  │  │ 配角  │  │ 配角  │  │ 配角  │    │
│          │  │      │  │      │  │      │  │      │    │
│          │  │ [编辑]│  │ [编辑]│  │ [编辑]│  │ [编辑]│    │
│          │  │[重新生成]│ │[重新生成]│ │[重新生成]│ │[重新生成]│   │
│          │  └──────┘  └──────┘  └──────┘  └──────┘    │
│          │                                              │
│          │  ┌──────┐  ┌──────┐  ┌──────┐  ...          │
│          │  │ 沈父  │  │ 周助理 │  │ 宾客甲 │             │
│          │  │ 配角  │  │ 龙套  │  │ 龙套  │             │
│          │  └──────┘  └──────┘  └──────┘              │
│          │                                              │
│          │  ⓘ 角色和场景设定会应用到整部剧集中，            │
│          │    建议调整完毕后再继续                         │
│          │                                              │
│          │                          [← 上一步] [下一步 →] │
└──────────┴──────────────────────────────────────────────┘
```

**角色卡片组件** (`CharacterCard`) — 对齐 06_project_detail 截图：

```
┌─────────────────┐
│ [主角] ← 紫色小标签(圆角4px, 11px, 左上角)
│ ┌─────────────┐ │
│ │             │ │ ← 角色形象图 (3:4竖向全身照)
│ │   全身照     │ │    白色/浅灰背景，无裁切
│ │             │ │
│ └─────────────┘ │
│  沈念安          │ ← 14px 粗体黑色
│  共1个形象       │ ← 12px 灰色
└─────────────────┘
```
- **布局**：7列网格（大屏），无卡片边框，无阴影
- 主角有紫色 `主角` 标签（绝对定位左上角）
- 图片直接排列，无多余装饰

**角色编辑弹窗** (`CharacterEditModal`):

```
┌──────────────────────────────────────────┐
│  编辑角色 — 沈念安                     ✕  │
├──────────────────────────────────────────┤
│                                          │
│  角色名: [沈念安           ]              │
│  角色类型: [主角 ▼]                      │
│                                          │
│  外貌描述:                               │
│  [25岁，长发及腰，气质优雅，常穿白色...]    │
│                                          │
│  音色描述:                               │
│  [女声，温柔成熟，音调中偏低，语速适中...]   │
│                                          │
│  形象图:                                 │
│  ┌──────┐ ┌──────┐ ┌──────┐            │
│  │ 形象1 │ │ 形象2 │ │ +添加 │            │
│  └──────┘ └──────┘ └──────┘            │
│                                          │
│           [取消]  [保存并重新生成形象]       │
└──────────────────────────────────────────┘
```

**场景卡片** — 对齐 07_scenes 截图：

```
┌──────────────────────┐
│ ┌──────────────────┐ │
│ │                  │ │ ← 横向图片 (16:10)
│ │    真实场景照片    │ │    真实场景照片，无裁切
│ └──────────────────┘ │
│  沈念安的豪华公寓      │ ← 14px 粗体
│  共3个场景图          │ ← 12px 灰色
└──────────────────────┘
```
- **布局**：4列网格，无卡片边框

---

### 4.4 Step 3 — 分集视频列表

**参考截图**: `09_episode_videos.png`

```
┌──────────┬──────────────────────────────────────────────┐
│          │                                              │
│  步骤导航  │  📺 分集视频 · 共 5 集          [多选] [全部生成] │
│          │                                              │
│ ① 剧本   │  ┌──────────────────────────────────────┐    │
│ ② 资产   │  │  第1集 · 订婚惊变妹妹夺爱              │    │
│ ③ 视频 ● │  │  👥 6角色  🏠 1场景  🎬 8分镜  ⏱ 01:25 │    │
│          │  │                  [预览] [编辑] [导出]   │    │
│          │  └──────────────────────────────────────┘    │
│          │                                              │
│          │  ┌──────────────────────────────────────┐    │
│          │  │  第2集 · 碎梦订婚宴                    │    │
│          │  │  👥 7角色  🏠 1场景  🎬 8分镜  ⏱ 01:34 │    │
│          │  │                  [预览] [编辑] [导出]   │    │
│          │  └──────────────────────────────────────┘    │
│          │                                              │
│          │  ┌──────────────────────────────────────┐    │
│          │  │  第3集 · 从云端跌落尘埃                 │    │
│          │  │  👥 10角色 🏠 2场景  🎬 7分镜  ⏱ 01:10 │    │
│          │  │                  [预览] [编辑] [导出]   │    │
│          │  └──────────────────────────────────────┘    │
│          │  ...                                        │
│          │                                              │
│          │                           [← 上一步] [导出全部] │
└──────────┴──────────────────────────────────────────────┘
```

**分集卡片组件** (`EpisodeCard`) — 对齐 09_episode_videos 截图：
- **布局**：2列网格，卡片有 1px 浅灰边框，圆角 12px
- **卡片内**：
  - 左侧：大号序号（24px, 灰色 300 字重）
  - 缩略图：100×130px（9:16竖屏），圆角 8px，左下角时长标签（黑底白字 10px）
  - 标题：`第 N 集：XXX`（14px 粗体）
  - 统计：`👥N 角色  🏠N 场景  🎬N 分镜`（12px 灰色）
  - 操作按钮：
    - `▶ 预览`：白底边框小按钮
    - `✏ 编辑`：白底边框小按钮
    - `⬇ 导出`：**黑底白字**小按钮（强调）

---

### 4.5 分镜编辑器（核心页面）⭐⭐⭐

**参考截图**: `10_storyboard_editor.png` — 最重要的页面

```
┌─────────────────────────────────────────────────────────────────┐
│ ← 返回  第1集 · 订婚惊变妹妹夺爱   [模型: veo-3.1-fast ▼]       │
│                                    [导出] [合成全集] [⚙️配置]    │
├───────────┬────────────────────────────────┬────────────────────┤
│           │                                │                    │
│  资产库    │  片段 1                         │   视频预览          │
│           │  ──────                        │                    │
│  角色 (7)  │  画面风格: 真人写实, 暖色调      │  ┌──────────────┐  │
│  ┌─────┐  │                                │  │              │  │
│  │ 司仪 │  │  ┌─ 分镜 1 ── ⊙ 6.0s ───┐    │  │  ▶ 视频播放   │  │
│  ├─────┤  │  │ 时间: 日               │    │  │              │  │
│  │ 沈念安│  │  │ 场景: @豪华酒店宴会厅   │    │  │  00:00/00:15 │  │
│  ├─────┤  │  │ 镜头: 中景             │    │  └──────────────┘  │
│  │ 沈母 │  │  │ 角色: @司仪            │    │                    │
│  ├─────┤  │  │ 动作: 手持话筒，微笑    │    │  分镜详情           │
│  │ 沈父 │  │  │ 台词: "今天，是沈家..." │    │  ┌──────────────┐  │
│  ├─────┤  │  │ 音色: 男声，青年音色    │    │  │ 图片: [预览]   │  │
│  │ 沈薇薇│  │  │ 运镜: 静止             │    │  │ 音频: [▶播放]  │  │
│  ├─────┤  │  │ 过渡: 切换             │    │  │ 视频: [▶播放]  │  │
│  │ 顾承泽│  │  └──────────────────────┘    │  └──────────────┘  │
│  └─────┘  │                                │                    │
│           │  ┌─ 分镜 2 ── ⊙ 3.0s ───┐    │                    │
│  场景 (1)  │  │ 时间: 日               │    │                    │
│  ┌─────┐  │  │ 场景: @豪华酒店宴会厅   │    │                    │
│  │ 宴会厅│  │  │ 镜头: 特写             │    │                    │
│  └─────┘  │  │ 角色: @沈念安           │    │                    │
│           │  │ ...                    │    │                    │
│  旁白     │  └──────────────────────┘     │                    │
│  ┌─────┐  │                                │                    │
│  │ 旁白 │  │  [编辑脚本] [再次生成]          │                    │
│  └─────┘  │                                │                    │
├───────────┴────────────────────────────────┴────────────────────┤
│  ▶ ■ 00:00 / 01:25                          [🔀多选] [按时间线播放] │
│  ┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐│
│  │片段1  ││片段2  ││片段3  ││片段4  ││片段5  ││片段6  ││片段7  ││片段8  ││
│  │00:15  ││00:14  ││00:09  ││00:04  ││00:09  ││00:10  ││00:13  ││00:11  ││
│  └──────┘└──────┘└──────┘└──────┘└──────┘└──────┘└──────┘└──────┘│
└─────────────────────────────────────────────────────────────────┘
```

**三栏布局组件拆解**:

#### 左栏 — AssetPanel (约200px)（对齐截图10左栏）

```typescript
interface AssetPanelProps {
  characters: Character[]      // 该集涉及的角色
  scenes: SceneLocation[]      // 该集涉及的场景
  narrator?: Character         // 旁白角色
  onCharacterClick: (char: Character) => void
  onSceneClick: (scene: SceneLocation) => void
}
```

- 角色列表：显示头像缩略图 + 角色名
- 场景列表：显示场景缩略图 + 场景名
- 点击角色/场景可查看详情或编辑
- 拖拽角色到分镜脚本区域可快速引用（`@角色名`）

#### 中栏 — StoryboardScript (flex-1)

```typescript
interface StoryboardScriptProps {
  segments: Segment[]
  currentSegmentIndex: number
  onShotEdit: (shotId: number, data: ShotUpdate) => void
  onSegmentRegenerate: (segmentId: number) => void
  onEditScript: () => void
}
```

- 片段标题 + 风格/类型标签
- **脚本卡片**：白色背景，圆角 12px，内边距 20px（对齐截图10中栏）
  - 顶部：`画面风格和类型: 真人写实, 电视风格, 暖色调,都市女频`
  - 分镜列表中每个分镜以自然文本段呈现（非表单）
  - `分镜N ⊙ X.0s ; 时间: 日, 场景图片: @场景名 , 镜头: 中景镜头, ...`
- **@引用标记**（关键视觉）：角色/场景引用显示为 **inline 紫色胶囊标签**
  - 格式：`[小头像] 角色名-基础形象-基础形象`
  - 背景：淡紫色胶囊（border-radius 999px）
  - 场景引用：`[小缩略图] 场景名_序号`
- 输入 `@` 弹出角色/场景选择器下拉
- "编辑脚本" 切换为纯文本编辑模式
- "再次生成" 灰色按钮，重新生成当前片段

#### 右栏 — PreviewPanel (约380px)（对齐截图10右栏）

```typescript
interface PreviewPanelProps {
  currentShot: Shot | null
  currentSegment: Segment | null
  onPlay: () => void
}
```

- **视频区**：9:16 竖屏比例，黑色背景，圆角 8px
- **播放控件**（视频底部叠加，渐变蒙层）：
  - `▶` 播放 → `00:00 | 00:15` 时间 → `🔈` 音量 → `🔲` 全屏 → `⬇` 下载
- 当前分镜的图片预览（无视频时显示静态图）
- 底部提示：`视频每秒消耗11积分，以实际生成为准`（12px 灰色）

#### 底栏 — Timeline (约130px)（对齐截图10底栏）

```typescript
interface TimelineProps {
  segments: Segment[]
  currentIndex: number
  totalDuration: number
  onSelect: (index: number) => void
  onReorder: (from: number, to: number) => void
  onMultiSelect: (indices: number[]) => void
}
```

- **播放控制行**：`▶ 00:00 / 01:25` + 右侧 `多选` 按钮
- **片段缩略图横向滚动**：
  - 每个片段：120×80px，缩略图（视频截图），圆角 8px
  - 左上角序号：紫色圆角小标签 `1` `2` `3`...
  - 底部时长：`00:15`（12px）
  - **选中态**：2px 紫色边框
  - **非选中态**：无边框，hover 灰色边框
- 支持拖拽排序
- 多选模式（批量重新生成/删除）

---

### 4.6 资产库

**参考**: 小云雀资产库页

```
┌──────────────────────────────────────────────────────────┐
│  资产库                              [新增] [刷新]        │
│                                                          │
│  [资产] [人物角色]          🔍搜索...    [筛选▼] [网格|列表] │
│                                                          │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐      │
│  │      │  │      │  │      │  │      │  │      │      │
│  │ 图片1 │  │ 图片2 │  │ 图片3 │  │ 图片4 │  │ 图片5 │      │
│  │      │  │      │  │      │  │      │  │      │      │
│  │名称   │  │名称   │  │名称   │  │名称   │  │名称   │      │
│  │来源   │  │来源   │  │来源   │  │来源   │  │来源   │      │
│  │时间   │  │时间   │  │时间   │  │时间   │  │时间   │      │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘      │
│                                                          │
│  ┌──────┐  ┌──────┐  ┌──────┐                           │
│  │      │  │      │  │      │                           │
│  │ 图片6 │  │ 图片7 │  │ 图片8 │                           │
│  │      │  │      │  │      │                           │
│  └──────┘  └──────┘  └──────┘                           │
│                                                          │
│  已加载全部                                               │
└──────────────────────────────────────────────────────────┘
```

---

## 5. 组件设计

### 5.1 组件目录结构

```
frontend/src/
├── components/
│   ├── common/                   # 通用组件
│   │   ├── AppHeader.vue         # 顶部导航栏
│   │   ├── AppSidebar.vue        # 左侧边栏
│   │   ├── StepNavigator.vue     # 三步导航
│   │   ├── LoadingOverlay.vue    # 加载遮罩
│   │   ├── ConfirmDialog.vue     # 确认弹窗
│   │   └── EmptyState.vue        # 空状态占位
│   │
│   ├── home/                     # 首页组件
│   │   ├── CreationInput.vue     # 创作输入框
│   │   ├── QuickTagBar.vue       # 快捷标签
│   │   ├── ProjectHistory.vue    # 历史项目列表
│   │   └── FeatureCards.vue      # 功能卡片
│   │
│   ├── script/                   # 剧本相关组件
│   │   ├── ScriptMetaForm.vue    # 元数据表单
│   │   ├── ScriptEditor.vue      # 剧本编辑器
│   │   ├── EpisodeAccordion.vue  # 分集折叠面板
│   │   └── NarrationToggle.vue   # 对话/旁白切换
│   │
│   ├── assets/                   # 资产相关组件
│   │   ├── CharacterCard.vue     # 角色卡片
│   │   ├── CharacterEditModal.vue# 角色编辑弹窗
│   │   ├── SceneCard.vue         # 场景卡片
│   │   ├── SceneEditModal.vue    # 场景编辑弹窗
│   │   └── AssetUploader.vue     # 资产上传器
│   │
│   ├── storyboard/               # 分镜编辑器组件 ⭐
│   │   ├── AssetPanel.vue        # 左侧资产面板
│   │   ├── StoryboardScript.vue  # 中间分镜脚本区
│   │   ├── ShotCard.vue          # 单个分镜卡片
│   │   ├── ShotEditor.vue        # 分镜编辑表单
│   │   ├── PreviewPanel.vue      # 右侧预览面板
│   │   ├── VideoPlayer.vue       # 视频播放器
│   │   ├── Timeline.vue          # 底部时间线
│   │   ├── TimelineItem.vue      # 时间线单项
│   │   ├── RefAutocomplete.vue   # @引用自动补全
│   │   └── DurationSlider.vue    # 时长滑块
│   │
│   ├── episodes/                 # 分集组件
│   │   ├── EpisodeCard.vue       # 分集卡片
│   │   └── EpisodeList.vue       # 分集列表
│   │
│   └── library/                  # 资产库组件
│       ├── AssetGrid.vue         # 资产网格
│       ├── AssetListItem.vue     # 资产列表项
│       └── AssetFilter.vue       # 资产筛选器
│
├── views/                        # 页面视图
│   ├── HomePage.vue
│   ├── ProjectListPage.vue
│   ├── ProjectLayout.vue         # 项目布局容器
│   ├── ScriptPage.vue
│   ├── AssetsPage.vue
│   ├── EpisodesPage.vue
│   ├── StoryboardEditorPage.vue  # ⭐ 核心页面
│   ├── AssetLibraryPage.vue
│   └── SettingsPage.vue
│
├── stores/                       # Pinia 状态
│   ├── project.ts
│   ├── script.ts
│   ├── assets.ts
│   ├── storyboard.ts
│   ├── timeline.ts
│   └── tasks.ts
│
├── api/                          # API 封装
│   ├── client.ts                 # Axios 实例
│   ├── projects.ts
│   ├── scripts.ts
│   ├── assets.ts
│   ├── episodes.ts
│   ├── storyboard.ts
│   └── websocket.ts
│
├── types/                        # TypeScript 类型
│   ├── project.ts
│   ├── script.ts
│   ├── character.ts
│   ├── scene.ts
│   ├── episode.ts
│   ├── segment.ts
│   ├── shot.ts
│   └── enums.ts
│
├── utils/
│   ├── format.ts                 # 格式化工具
│   ├── time.ts                   # 时间处理
│   └── prompt.ts                 # 提示词工具
│
├── App.vue
├── main.ts
└── router.ts
```

### 5.2 核心组件接口

#### ShotCard.vue — 分镜卡片

```vue
<template>
  <div class="shot-card" :class="{ active: isActive }">
    <div class="shot-header">
      <span class="shot-index">分镜 {{ shot.index }}</span>
      <DurationSlider v-model="shot.duration" :min="0.5" :max="15" />
    </div>

    <div class="shot-body">
      <div class="field">
        <label>时间</label>
        <select v-model="shot.time_of_day">
          <option value="日">日</option>
          <option value="夜">夜</option>
        </select>
      </div>

      <div class="field">
        <label>场景</label>
        <RefAutocomplete
          v-model="shot.scene_ref"
          type="scene"
          :options="scenes"
        />
      </div>

      <div class="field">
        <label>镜头</label>
        <select v-model="shot.camera_type">
          <option v-for="t in cameraTypes" :value="t.value">{{ t.label }}</option>
        </select>
        <input v-model="shot.camera_angle" placeholder="角度描述" />
      </div>

      <div class="field">
        <label>角色</label>
        <RefAutocomplete
          v-model="shot.characters"
          type="character"
          :options="characters"
          multiple
        />
      </div>

      <div class="field">
        <label>台词</label>
        <textarea v-model="shot.dialogue" rows="2" />
      </div>

      <div class="field">
        <label>音色</label>
        <input v-model="shot.voice_style" />
      </div>

      <div class="field">
        <label>运镜</label>
        <select v-model="shot.camera_movement">
          <option v-for="m in movements" :value="m.value">{{ m.label }}</option>
        </select>
      </div>
    </div>
  </div>
</template>
```

#### RefAutocomplete.vue — @引用自动补全

```vue
<template>
  <div class="ref-autocomplete">
    <input
      v-model="inputValue"
      @input="onInput"
      @keydown.enter="selectFirst"
    />
    <div v-if="showDropdown" class="dropdown">
      <div
        v-for="item in filtered"
        :key="item.id"
        class="dropdown-item"
        @click="select(item)"
      >
        <img :src="item.thumbnail" class="w-6 h-6 rounded" />
        <span>@{{ item.name }}</span>
        <span class="text-gray-400">{{ item.role || item.type }}</span>
      </div>
    </div>
  </div>
</template>
```

当用户输入 `@` 时，自动弹出角色/场景选择器，选择后插入引用。

---

## 6. 状态管理

### 6.1 Store 设计

```typescript
// stores/project.ts
export const useProjectStore = defineStore('project', () => {
  const currentProject = ref<Project | null>(null)
  const currentStep = ref<ProjectStep>('script')

  // 导航到下一步
  async function nextStep() {
    if (currentStep.value === 'script') {
      await approveScript()
      currentStep.value = 'assets'
    } else if (currentStep.value === 'assets') {
      await approveAssets()
      currentStep.value = 'video'
    }
  }

  return { currentProject, currentStep, nextStep }
})

// stores/storyboard.ts
export const useStoryboardStore = defineStore('storyboard', () => {
  const segments = ref<Segment[]>([])
  const currentSegmentIndex = ref(0)
  const currentShotIndex = ref(0)

  const currentSegment = computed(() => segments.value[currentSegmentIndex.value])
  const currentShot = computed(() =>
    currentSegment.value?.shots[currentShotIndex.value]
  )
  const totalDuration = computed(() =>
    segments.value.reduce((sum, seg) => sum + seg.duration, 0)
  )

  // 选中片段
  function selectSegment(index: number) {
    currentSegmentIndex.value = index
    currentShotIndex.value = 0
  }

  // 更新分镜
  async function updateShot(shotId: number, data: ShotUpdate) {
    await api.updateShot(shotId, data)
    // 局部刷新
  }

  // 重新生成片段
  async function regenerateSegment(segmentId: number) {
    const taskId = await api.regenerateSegment(segmentId)
    // 开始 WebSocket 监听
    useTaskStore().watchTask(taskId)
  }

  return {
    segments, currentSegmentIndex, currentShotIndex,
    currentSegment, currentShot, totalDuration,
    selectSegment, updateShot, regenerateSegment
  }
})

// stores/tasks.ts
export const useTaskStore = defineStore('tasks', () => {
  const activeTasks = ref<Map<string, TaskProgress>>(new Map())
  let ws: WebSocket | null = null

  function watchTask(taskId: string) {
    ws = new WebSocket(`/api/v2/ws/tasks/${taskId}`)
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      activeTasks.value.set(taskId, data)

      if (data.type === 'completed') {
        // 更新对应的 segment 数据
        useStoryboardStore().refreshSegment(data.result.segment_id)
      }
    }
  }

  return { activeTasks, watchTask }
})
```

---

## 7. 实时通信

### 7.1 WebSocket 管理器

```typescript
// api/websocket.ts
class WSManager {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private handlers = new Map<string, Function[]>()

  connect(taskId: string) {
    const url = `${WS_BASE}/api/v2/ws/tasks/${taskId}`
    this.ws = new WebSocket(url)

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.emit(data.type, data)
    }

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++
          this.connect(taskId)
        }, 1000 * Math.pow(2, this.reconnectAttempts))
      }
    }
  }

  on(event: string, handler: Function) {
    if (!this.handlers.has(event)) this.handlers.set(event, [])
    this.handlers.get(event)!.push(handler)
  }

  private emit(event: string, data: any) {
    this.handlers.get(event)?.forEach(h => h(data))
  }

  disconnect() {
    this.ws?.close()
    this.ws = null
  }
}

export const wsManager = new WSManager()
```

### 7.2 进度展示

```vue
<!-- components/common/TaskProgress.vue -->
<template>
  <div v-if="task" class="task-progress">
    <div class="progress-bar">
      <div
        class="progress-fill"
        :style="{ width: `${(task.current / task.total) * 100}%` }"
      />
    </div>
    <span class="progress-text">
      {{ task.message }} ({{ task.current }}/{{ task.total }})
    </span>
  </div>
</template>
```

---

## 8. 设计规范（对齐小云雀视觉风格）

### 8.1 色彩方案

```css
:root {
  /* 主色 - 紫色系（对齐小云雀高亮步骤/主按钮） */
  --primary-50:  #F3F0FF;
  --primary-100: #E8E0FF;
  --primary-300: #B8A4F8;
  --primary-500: #7C3AED;  /* 主色调 */
  --primary-600: #6C5CE7;
  --primary-700: #5B21B6;

  /* 中性色（对齐小云雀文字层级） */
  --gray-50:  #FAFAFA;     /* 页面背景 */
  --gray-100: #F5F5F5;     /* 侧边栏背景 */
  --gray-200: #E8E8E8;     /* 边框色 */
  --gray-300: #D1D5DB;     /* 分隔线 */
  --gray-400: #999999;     /* 弱文字 */
  --gray-500: #666666;     /* 次文字 */
  --gray-700: #333333;     /* 副标题 */
  --gray-800: #1A1A1A;     /* 主文字 */
  --gray-900: #111111;     /* 标题 */

  /* 功能色 */
  --success: #52C41A;
  --warning: #FAAD14;
  --error:   #FF4D4F;
  --info:    #3B82F6;

  /* 背景 */
  --bg-primary:   #FFFFFF;
  --bg-secondary: #FAFAFA;
  --bg-sidebar:   #FFFFFF;
}
```

### 8.2 字体规范（对齐小云雀字体层级）

```css
/* 字体族 */
font-family: "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
font-family-mono: "JetBrains Mono", ui-monospace, Consolas, monospace;

/* 大标题 — 问候语/页面标题（如"短剧 Agent"、"资产库"） */
.heading-hero { font-size: 28-32px; font-weight: 600; line-height: 40px; }

/* 页面标题 — 如"共 5 集"、"剧本摘要" */
.heading-1 { font-size: 20px; font-weight: 700; line-height: 28px; }

/* 区块标题 — 如"全部角色 11"、Tab 文字 */
.heading-2 { font-size: 16px; font-weight: 600; line-height: 24px; }

/* 组件标题 — 如"片段 1"、"资产库" */
.heading-3 { font-size: 14px; font-weight: 600; line-height: 22px; }

/* 正文 */
.body-1    { font-size: 14px; font-weight: 400; line-height: 22px; }  /* 主要内容 */
.body-2    { font-size: 13px; font-weight: 400; line-height: 20px; }  /* 次要内容 */

/* 辅助文字 — 如时间戳、提示、积分消耗说明 */
.caption   { font-size: 12px; font-weight: 400; line-height: 18px; color: var(--gray-400); }

/* 微型文字 — 如缩略图上的时长标签 */
.tiny      { font-size: 10px; font-weight: 400; line-height: 14px; }
```

### 8.3 间距与圆角（对齐小云雀组件规范）

```css
/* 间距 4px 倍数 */
--spacing-1: 4px;   --spacing-2: 8px;
--spacing-3: 12px;  --spacing-4: 16px;
--spacing-5: 20px;  --spacing-6: 24px;
--spacing-8: 32px;

/* 圆角（参考截图实测） */
--radius-xs: 4px;     /* 标签、小按钮（如"主角"标签） */
--radius-sm: 6px;     /* 中按钮 */
--radius-md: 8px;     /* 按钮、输入框、缩略图 */
--radius-lg: 12px;    /* 卡片、对话框、脚本区域 */
--radius-xl: 16px;    /* 大卡片、弹窗 */
--radius-full: 999px; /* 胶囊标签、圆形头像、发送按钮 */

/* 阴影（参考截图实测） */
--shadow-card: 0 2px 8px rgba(0, 0, 0, 0.06);         /* 卡片悬浮 */
--shadow-modal: 0 12px 24px rgba(0, 0, 0, 0.12);      /* 弹窗 */
--shadow-dropdown: 0 4px 16px rgba(0, 0, 0, 0.08);    /* 下拉菜单 */
```

### 8.4 响应式断点

```css
/* 移动优先 */
@media (min-width: 768px)  { /* Tablet */ }
@media (min-width: 1024px) { /* Desktop */ }
@media (min-width: 1440px) { /* Wide Desktop - 分镜编辑器最佳 */ }
```

### 8.5 动画规范

```css
/* 过渡 */
--transition-fast:   150ms ease;
--transition-normal: 250ms ease;
--transition-slow:   350ms ease;

/* 常用动画 */
.fade-enter-active { transition: opacity var(--transition-normal); }
.slide-enter-active { transition: transform var(--transition-normal); }
```

---

## 附录 A：页面截图对照

| DramaForge 页面 | 对标小云雀页面 | 截图参考 |
|----------------|-------------|---------|
| 首页 | 主页 | `02_home.png`、`03_home_full.png` |
| 首页(Agent模式/参考) | Agent 模式 | `11_agent_modes.png`、`12_hit_clone.png` |
| 短剧 Agent 入口 | 短剧 Agent | `04_drama_agent.png`、`05_ai_script.png` |
| Step 1 剧本 | 剧本大纲页 | `08_script_outline.png` |
| Step 2 角色 | 角色管理页 | `06_project_detail.png` |
| Step 2 场景 | 场景管理页 | `07_scenes.png` |
| Step 3 分集列表 | 分集视频列表 | `09_episode_videos.png` |
| 分镜编辑器 ⭐ | 分镜编辑器 | `10_storyboard_editor.png` |
| 资产库 | 资产库 | `13_asset_library.png` |
| 订阅弹窗 | 订阅页 | `14_subscription.png` |

---

## 附录 B：通用组件视觉规范

### 步骤导航器（参考 06/07/08/09 截图）
```
✓剧本大纲 ─ ─ ─ ②角色和场景 ─ ─ ─ 3 分集视频
```
- 已完成步骤：紫色 ✓ 圆圈 + 灰色文字
- 当前步骤：紫色实心数字圆圈 + 黑色加粗文字
- 未来步骤：灰色数字圆圈 + 灰色文字
- 步骤间：灰色虚线连接

### 底部操作栏（参考 06/07/08 截图）
```
┌───────────────────────────────────────────────────────────────┐
│ [🤖头像] 提示文字（灰色14px）                  [上一步] [下一步] │
└───────────────────────────────────────────────────────────────┘
```
- 固定在视口底部，白色背景，上边框 1px
- 左侧：AI 小头像 + 灰色提示文字
- 右侧：`上一步`（白底黑字边框）+ `下一步`（黑底白字实心）
- 按钮高 40px，圆角 8px

### 按钮规范
| 类型 | 样式 | 使用场景 |
|------|------|---------|
| 主按钮 | 黑底白字, 圆角 8px, 高 40px | 下一步、合成全集、导出 |
| 次按钮 | 白底黑字+1px灰边框, 圆角 8px | 上一步、编辑、预览 |
| 幽灵按钮 | 透明背景, hover 灰底 | 编辑脚本、多选 |
| 小按钮 | 同上, 高 32px, 字号 13px | 操作组中的按钮 |
| 圆形按钮 | 36px 圆形, 灰色/黑色 | 发送按钮 |

### 资产库页面（参考 13_asset_library 截图）
- 标题 `资产库`：24px 粗体
- `新增` 按钮：黑底白字，带下拉箭头
- Tab 栏：`🖼 资产` | `👤 人物角色`，选中态下划线 2px
- 5列网格，每张卡片：图片+底部操作图标（`[+]` `[♡]` `[🗑]`）
- 底部信息：`创作生成  时间戳`（12px 灰色）

---

> **总结**: 前端以 **Vue 3 + TypeScript + TailwindCSS** 为技术栈，
> 核心围绕小云雀验证过的 **三步工作流** 和 **分镜编辑器** 进行设计。
> 所有页面的布局、尺寸、颜色、按钮风格均与小云雀截图像素级对齐。
> 分镜编辑器采用三栏布局（资产库 | 脚本编辑 | 预览），底部时间线支持拖拽排序。
> 通过 WebSocket 实时推送 AI 生成进度，Pinia 管理全局状态。
> 详细视觉规范参见 `docs/UI_DESIGN_SPEC.md`。
