# DramaForge v2.0 — 后端技术架构文档

> **版本**: v2.0 Draft
> **日期**: 2026-04-01
> **参考**: [小云雀功能分析](./XIAOYUNQUE_FEATURES.md)

---

## 目录

1. [架构总览](#1-架构总览)
2. [技术选型](#2-技术选型)
3. [数据模型设计](#3-数据模型设计)
4. [三步流水线引擎](#4-三步流水线引擎)
5. [AI Hub 中台](#5-ai-hub-中台)
6. [API 接口设计](#6-api-接口设计)
7. [异步任务系统](#7-异步任务系统)
8. [存储与资产管理](#8-存储与资产管理)
9. [部署方案](#9-部署方案)

---

## 1. 架构总览

### 1.1 系统分层

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Vue 3)                  │
│         对话式 Agent UI + 分镜编辑器 + 资产库         │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────┐
│                 API Gateway (FastAPI)                │
│   REST Endpoints + WebSocket 推送 + JWT Auth         │
├─────────────────────────────────────────────────────┤
│              Pipeline Engine (核心引擎)               │
│                                                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
│  │  Step 1   │  │  Step 2   │  │  Step 3   │       │
│  │  Script   │→ │  Assets   │→ │  Video    │       │
│  │  Engine   │  │  Engine   │  │  Engine   │       │
│  └───────────┘  └───────────┘  └───────────┘       │
├─────────────────────────────────────────────────────┤
│                   AI Hub (中台)                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│  │ Chat │ │Image │ │ TTS  │ │Video │ │Prompt│     │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘     │
├─────────────────────────────────────────────────────┤
│  Task Queue (Celery/ARQ)  │  Storage (Local/OSS)    │
│  Redis + Result Backend   │   PostgreSQL     │
└─────────────────────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  laozhang.ai    │
              │  API Gateway    │
              └─────────────────┘
```

### 1.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **三步流水线** | 剧本 → 资产 → 视频，对齐小云雀工作流 |
| **中台解耦** | AI Hub 屏蔽模型细节，上层只调接口 |
| **异步优先** | 耗时任务全部异步化，WebSocket 推送进度 |
| **资产驱动** | 角色/场景作为全局资产，@引用确保一致性 |
| **可审核** | 每步之间设置人工审核节点 |

---

## 2. 技术选型

### 2.1 后端核心

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **语言** | Python | 3.11+ | 类型注解 + async/await |
| **Web 框架** | FastAPI | 0.115+ | 高性能异步框架 |
| **ORM** | SQLAlchemy | 2.0+ | 异步 ORM |
| **数据库** |  PostgreSQL | - |  PG |
| **缓存** | Redis | 7.0+ | 会话/缓存/任务队列 |
| **任务队列** | ARQ | 0.26+ | 轻量异步任务队列 |
| **数据校验** | Pydantic | 2.0+ | 请求/响应模型 |

### 2.2 AI 服务

| 能力 | 模型 | 提供商 |
|------|------|--------|
| **文本生成** | GPT-4o / DeepSeek-V3 | laozhang.ai |
| **图片生成** | sora-image / flux-pro | laozhang.ai |
| **语音合成** | tts-1-hd | laozhang.ai |
| **视频生成** | veo-3.1-fast / sora-2 | laozhang.ai |
| **提示词优化** | GPT-4o | laozhang.ai |

### 2.3 基础设施

| 组件 | 技术 | 说明 |
|------|------|------|
| **视频合成** | FFmpeg | 片段合成 + 字幕烧录 |
| **对象存储** | 本地 → MinIO/OSS | 图片/音频/视频文件 |
| **日志** | Loguru | 结构化日志 |
| **配置** | pydantic-settings | .env 环境变量 |

---

## 3. 数据模型设计

### 3.1 ER 关系图

```
┌──────────────┐
│   Project    │ ──── 一个项目 = 一部剧
├──────────────┤
│ id           │
│ title        │
│ style        │──→ VideoStyle (真人写实/动漫/3D)
│ aspect_ratio │──→ "16:9" | "9:16" | "1:1"
│ genre        │──→ DramaGenre
│ status       │──→ ProjectStep (script/assets/video/done)
│ script_type  │──→ "dialogue" | "narration"
│ created_at   │
│ updated_at   │
└──────┬───────┘
       │
       │ 1:1
       ▼
┌──────────────┐        ┌──────────────┐
│   Script     │        │  Character   │
├──────────────┤        ├──────────────┤
│ id           │        │ id           │
│ project_id   │←───┐   │ project_id   │←── Project 1:N
│ protagonist  │    │   │ name         │
│ genre        │    │   │ role         │──→ "protagonist/supporting/extra"
│ synopsis     │    │   │ description  │
│ background   │    │   │ voice_desc   │
│ setting      │    │   │ reference_images │──→ JSON [url1, url2]
│ one_liner    │    │   │ created_at   │
│ raw_content  │    │   └──────────────┘
│ is_approved  │    │
│ created_at   │    │   ┌──────────────┐
└──────┬───────┘    │   │SceneLocation │
       │            │   ├──────────────┤
       │ 1:N        │   │ id           │
       ▼            │   │ project_id   │←── Project 1:N
┌──────────────┐    │   │ name         │
│   Episode    │    │   │ description  │
├──────────────┤    │   │ time_of_day  │
│ id           │    │   │ interior     │──→ bool (内/外)
│ script_id    │────┘   │ reference_images │──→ JSON [url1, url2]
│ number       │        │ created_at   │
│ title        │        └──────────────┘
│ content      │
│ is_approved  │
│ created_at   │
└──────┬───────┘
       │
       │ 1:N
       ▼
┌──────────────┐
│  Segment     │ ──── 一个片段 = 分镜编辑器中的一个"片段"
├──────────────┤
│ id           │
│ episode_id   │
│ index        │
│ status       │──→ pending/generating/done/failed
│ video_url    │
│ audio_url    │
│ thumbnail_url│
│ duration     │
│ created_at   │
└──────┬───────┘
       │
       │ 1:N
       ▼
┌──────────────┐
│    Shot      │ ──── 一个分镜 = 最小生成单元
├──────────────┤
│ id           │
│ segment_id   │
│ index        │
│ duration     │──→ float (0~15s)
│ time_of_day  │──→ "日" | "夜"
│ scene_ref    │──→ @SceneLocation.id
│ camera_type  │──→ "close-up/medium/wide/over-shoulder"
│ camera_angle │──→ 自由文本描述
│ camera_move  │──→ "static/push/pull/pan/tilt/track"
│ characters   │──→ JSON [{char_id, appearance_idx, action}]
│ dialogue     │
│ voice_style  │
│ background   │──→ 背景描述
│ transition   │──→ "cut/crossfade/fade-black"
│ image_prompt │──→ 合成后的完整图片提示词
│ video_prompt │──→ 合成后的完整视频提示词
│ image_url    │
│ audio_url    │
│ video_url    │
│ created_at   │
└──────────────┘
```

### 3.2 v1.0 → v2.0 模型变更对比

| v1.0 模型 | v2.0 模型 | 变化说明 |
|-----------|-----------|---------|
| `Project` | `Project` | 新增 `style`, `aspect_ratio`, `script_type` |
| `Character` | `Character` | 新增 `role`, `voice_desc`, `reference_images` |
| `Script` | `Script` | 重构为大纲级，新增 `protagonist/synopsis/background/setting/one_liner` |
| - | `Episode` | 🆕 从 Script 拆出独立的分集模型 |
| - | `SceneLocation` | 🆕 全局场景资产 |
| `Storyboard` | `Segment` | 重命名，作为片段容器 |
| - | `Shot` | 🆕 最细粒度的分镜单元（核心模型） |
| `GeneratedVideo` | 合并到 `Segment` | 视频路径合并到片段模型中 |

### 3.3 枚举定义

```python
class ProjectStep(str, Enum):
    """项目当前所在步骤 — 对齐小云雀三步流"""
    SCRIPT    = "script"     # Step 1: 剧本大纲
    ASSETS    = "assets"     # Step 2: 角色和场景
    VIDEO     = "video"      # Step 3: 分集视频
    COMPLETED = "completed"  # 已完成

class VideoStyle(str, Enum):
    """视频风格"""
    REALISTIC  = "realistic"   # 真人写实
    ANIME      = "anime"       # 动漫
    THREE_D    = "3d"          # 3D 渲染
    COMIC      = "comic"       # 漫画
    INK_WASH   = "ink_wash"    # 水墨

class DramaGenre(str, Enum):
    """剧种类型"""
    FEMALE_LEAD = "female_lead"   # 女频
    MALE_LEAD   = "male_lead"     # 男频
    ROMANCE     = "romance"       # 甜宠
    SUSPENSE    = "suspense"      # 悬疑
    FANTASY     = "fantasy"       # 奇幻
    URBAN       = "urban"         # 都市
    HISTORICAL  = "historical"    # 古装
    SCI_FI      = "sci_fi"        # 科幻
    OTHER       = "other"         # 其他

class CameraType(str, Enum):
    """镜头景别"""
    EXTREME_CLOSE = "extreme_close"  # 大特写
    CLOSE_UP      = "close_up"       # 特写
    MEDIUM_CLOSE  = "medium_close"   # 中近景
    MEDIUM        = "medium"         # 中景
    MEDIUM_WIDE   = "medium_wide"    # 中远景
    WIDE          = "wide"           # 远景 / 全景
    OVER_SHOULDER = "over_shoulder"  # 过肩镜头
    POV           = "pov"            # 主观视角

class CameraMovement(str, Enum):
    """运镜方式"""
    STATIC  = "static"    # 静止
    PUSH    = "push"      # 推
    PULL    = "pull"      # 拉
    PAN     = "pan"       # 横摇
    TILT    = "tilt"      # 俯仰
    TRACK   = "track"     # 跟踪
    CRANE   = "crane"     # 升降
    ORBIT   = "orbit"     # 环绕

class CharacterRole(str, Enum):
    """角色类型"""
    PROTAGONIST = "protagonist"  # 主角
    SUPPORTING  = "supporting"   # 配角
    EXTRA       = "extra"        # 龙套
    NARRATOR    = "narrator"     # 旁白

class SegmentStatus(str, Enum):
    """片段生成状态"""
    PENDING      = "pending"       # 待生成
    SCRIPT_READY = "script_ready"  # 脚本已就绪
    GENERATING   = "generating"    # 生成中
    DONE         = "done"          # 已完成
    FAILED       = "failed"        # 失败
```

---

## 4. 三步流水线引擎

### 4.1 总体流程

```
用户输入 (文本 / .docx 文件)
         │
         ▼
┌─────────────────────────────────────────┐
│  STEP 1: Script Engine (剧本引擎)        │
│                                         │
│  输入 → LLM 生成/解析 → 结构化剧本       │
│                                         │
│  产出:                                  │
│    ├─ Script (大纲元数据)                │
│    ├─ Episode[] (分集内容)               │
│    └─ 自动识别的角色名/场景名列表         │
│                                         │
│  ⏸️ 人工审核点: 可编辑剧本内容            │
│     可一键改写为旁白型                    │
└─────────────┬───────────────────────────┘
              │ 用户点击"下一步"
              ▼
┌─────────────────────────────────────────┐
│  STEP 2: Assets Engine (资产引擎)        │
│                                         │
│  角色列表 → 并行生成角色形象图            │
│  场景列表 → 并行生成场景参考图            │
│                                         │
│  产出:                                  │
│    ├─ Character[] (含 reference_images)  │
│    └─ SceneLocation[] (含 images)        │
│                                         │
│  ⏸️ 人工审核点: 可替换/编辑角色形象       │
│     可替换/编辑场景图                     │
│     可调整角色音色描述                    │
└─────────────┬───────────────────────────┘
              │ 用户点击"下一步"
              ▼
┌─────────────────────────────────────────┐
│  STEP 3: Video Engine (视频引擎)         │
│                                         │
│  每集剧本 + 角色资产 + 场景资产           │
│    → LLM 拆分分镜脚本 (Shot[])           │
│    → 并行生成: 图片/音频/视频             │
│    → FFmpeg 合成片段                     │
│                                         │
│  产出:                                  │
│    ├─ Segment[] (每个片段的合成视频)       │
│    └─ 合成全集视频                       │
│                                         │
│  ⏸️ 操作点: 可编辑分镜脚本               │
│     可重新生成单个片段                    │
│     可预览/导出                          │
└─────────────────────────────────────────┘
```

### 4.2 Step 1: Script Engine 详细设计

```python
class ScriptEngine:
    """剧本引擎 — 负责从用户输入到结构化剧本的全过程"""

    async def create_from_text(self, user_input: str, project: Project) -> Script:
        """从用户故事构想生成完整剧本"""
        # 1. LLM 生成完整剧本
        raw_script = await ai_hub.chat.ask(
            system_prompt=SCRIPT_GENERATION_PROMPT,
            user_prompt=user_input,
            response_format="json"  # 强制 JSON 输出
        )
        # 2. 解析为结构化数据
        script = self._parse_script(raw_script)
        # 3. 自动提取角色名和场景名列表
        script.extracted_characters = self._extract_characters(raw_script)
        script.extracted_scenes = self._extract_scenes(raw_script)
        return script

    async def create_from_docx(self, file_path: str, project: Project) -> Script:
        """从上传的 .docx 文件解析剧本"""
        raw_text = self._read_docx(file_path)
        # LLM 结构化解析
        structured = await ai_hub.chat.ask(
            system_prompt=SCRIPT_PARSE_PROMPT,
            user_prompt=raw_text,
            response_format="json"
        )
        return self._parse_script(structured)

    async def rewrite_to_narration(self, script: Script) -> Script:
        """将对话型剧本改写为旁白型"""
        narration = await ai_hub.chat.ask(
            system_prompt=NARRATION_REWRITE_PROMPT,
            user_prompt=script.raw_content
        )
        script.raw_content = narration
        script.script_type = "narration"
        return script
```

**LLM 输出的结构化剧本 JSON Schema**:

```json
{
  "protagonist": "沈念安",
  "genre": "female_lead",
  "synopsis": "地位反差/身份错位...",
  "background": "现代都市。主要场景包括...",
  "setting": "主角被神秘人所救...",
  "one_liner": "在自己盛大的订婚宴上...",
  "episodes": [
    {
      "number": 1,
      "title": "订婚惊变妹妹夺爱",
      "content": "1-1 日 内 豪华酒店宴会厅\n人物：司仪, 沈念安..."
    }
  ],
  "characters": ["沈念安", "顾承泽", "沈薇薇", "沈母", "沈父"],
  "scenes": ["豪华酒店宴会厅", "沈念安的豪华公寓", "设计工作室门口"]
}
```

### 4.3 Step 2: Assets Engine 详细设计

```python
class AssetsEngine:
    """资产引擎 — 负责角色和场景的视觉资产生成"""

    async def generate_all_assets(
        self, script: Script, characters: list[str], scenes: list[str]
    ):
        """并行生成所有角色形象和场景图"""

        # 1. 为每个角色生成描述 + 形象图
        char_tasks = []
        for name in characters:
            char_tasks.append(self._generate_character(name, script))

        # 2. 为每个场景生成描述 + 参考图
        scene_tasks = []
        for scene_name in scenes:
            scene_tasks.append(self._generate_scene(scene_name, script))

        # 3. 并行执行
        char_results, scene_results = await asyncio.gather(
            asyncio.gather(*char_tasks),
            asyncio.gather(*scene_tasks)
        )
        return char_results, scene_results

    async def _generate_character(self, name: str, script: Script) -> Character:
        """为单个角色生成形象"""
        # 1. LLM 生成角色外貌描述 + 音色描述
        desc = await ai_hub.chat.ask(
            system_prompt=CHARACTER_DESC_PROMPT,
            user_prompt=f"角色名: {name}\n剧本: {script.raw_content[:2000]}"
        )
        # 2. 生成角色参考图 (全身照)
        image_url = await ai_hub.image.generate(
            prompt=f"{desc['appearance']}, full body shot, character reference sheet",
            style=script.project.style
        )
        return Character(
            name=name, role=desc['role'],
            description=desc['personality'],
            voice_desc=desc['voice'],
            reference_images=[image_url]
        )

    async def _generate_scene(self, name: str, script: Script) -> SceneLocation:
        """为单个场景生成参考图"""
        desc = await ai_hub.chat.ask(
            system_prompt=SCENE_DESC_PROMPT,
            user_prompt=f"场景: {name}\n背景: {script.background}"
        )
        images = await asyncio.gather(*[
            ai_hub.image.generate(prompt=p) for p in desc['image_prompts']
        ])
        return SceneLocation(name=name, description=desc['description'], images=images)

    async def replace_character_image(self, char_id: int, new_prompt: str) -> str:
        """用户替换角色形象"""
        return await ai_hub.image.generate(prompt=new_prompt)
```

### 4.4 Step 3: Video Engine 详细设计

```python
class VideoEngine:
    """视频引擎 — 分镜拆解 + 资产生成 + 合成"""

    async def generate_episode(
        self, episode: Episode, characters: list[Character],
        scenes: list[SceneLocation]
    ) -> list[Segment]:
        """生成单集的所有片段"""

        # 1. LLM 拆分分镜脚本
        shots_data = await self._split_storyboard(episode, characters, scenes)

        # 2. 按片段分组
        segments = self._group_into_segments(shots_data)

        # 3. 逐片段生成
        for segment in segments:
            await self._generate_segment(segment, characters, scenes)

        return segments

    async def _split_storyboard(
        self, episode: Episode, characters: list[Character],
        scenes: list[SceneLocation]
    ) -> list[dict]:
        """LLM 将剧本拆分为结构化分镜"""
        # 构建角色/场景上下文
        context = self._build_asset_context(characters, scenes)
        result = await ai_hub.chat.ask(
            system_prompt=STORYBOARD_SPLIT_PROMPT,
            user_prompt=f"{context}\n\n剧本内容:\n{episode.content}",
            response_format="json"
        )
        return result['shots']

    async def _generate_segment(
        self, segment: Segment, characters: list, scenes: list
    ):
        """并行生成单个片段的所有资产"""
        for shot in segment.shots:
            # 构建提示词 (将 @引用 替换为实际描述)
            shot.image_prompt = self._resolve_refs(shot, characters, scenes)

            # 并行生成图片、音频
            image_task = ai_hub.image.generate(prompt=shot.image_prompt)
            audio_task = None
            if shot.dialogue:
                audio_task = ai_hub.tts.speak(
                    text=shot.dialogue, voice=shot.voice_style
                )

            results = await asyncio.gather(
                image_task,
                audio_task or asyncio.sleep(0),
                return_exceptions=True
            )
            shot.image_url = results[0]
            if audio_task:
                shot.audio_url = results[1]

        # 选择视频生成策略
        strategy = self._decide_video_strategy(segment)
        if strategy == "ai_video":
            segment.video_url = await ai_hub.video.generate(
                prompt=segment.shots[0].video_prompt,
                image_url=segment.shots[0].image_url  # 图生视频
            )
        elif strategy == "image_to_video":
            # 使用 img2video
            segment.video_url = await ai_hub.video.img2video(
                image_url=segment.shots[0].image_url,
                prompt=segment.shots[0].camera_move
            )
        else:
            # 静态图片 + 音频 → FFmpeg 合成
            segment.video_url = await self._ffmpeg_compose(segment)

    def _decide_video_strategy(self, segment: Segment) -> str:
        """根据分镜内容决定视频生成策略"""
        has_action = any(
            s.camera_move != CameraMovement.STATIC for s in segment.shots
        )
        if has_action:
            return "ai_video"      # 有运镜 → AI 视频生成
        else:
            return "static_compose" # 静态 → 图片+音频合成
```

**分镜拆分 LLM 输出的 JSON Schema**:

```json
{
  "shots": [
    {
      "index": 1,
      "duration": 6.0,
      "time_of_day": "日",
      "scene_ref": "@豪华酒店宴会厅",
      "camera_type": "medium",
      "camera_angle": "从舞台正下方略仰视角度",
      "camera_movement": "static",
      "characters": [
        {"ref": "@司仪", "appearance_idx": 0, "action": "手持话筒，面带职业微笑"}
      ],
      "dialogue": "今天，是沈家千金沈念安与顾家公子顾承泽的订婚宴。",
      "voice_style": "男声，青年音色，音调中等偏高，音色明亮圆润",
      "background": "鲜花簇拥的舞台和璀璨的水晶灯",
      "transition": "cut"
    }
  ]
}
```

---

## 5. AI Hub 中台

### 5.1 已有服务 (v1.0 → 保留)

| 服务 | 模块 | 方法 |
|------|------|------|
| `ChatService` | `ai_hub.chat` | `ask()`, `ask_json()`, `ask_stream()` |
| `ImageService` | `ai_hub.image` | `generate()` |
| `TTSService` | `ai_hub.tts` | `speak()` |
| `VideoService` | `ai_hub.video` | `generate()`, `get_task_status()` |

### 5.2 新增服务 (v2.0)

```python
class PromptService:
    """提示词优化服务"""

    async def optimize(self, raw_prompt: str, context: str = "") -> str:
        """一键优化提示词"""
        return await ai_hub.chat.ask(
            system_prompt=PROMPT_OPTIMIZE_SYSTEM,
            user_prompt=f"原始提示词: {raw_prompt}\n上下文: {context}"
        )

    async def build_image_prompt(
        self, shot: Shot, characters: list, scenes: list, style: VideoStyle
    ) -> str:
        """根据分镜信息构建完整的图片生成提示词"""
        # 将 @引用 替换为实际外貌/场景描述
        # 拼接风格前缀 + 镜头语言 + 角色描述 + 场景描述 + 光影
        pass

    async def build_video_prompt(
        self, shot: Shot, characters: list, scenes: list
    ) -> str:
        """根据分镜信息构建完整的视频生成提示词"""
        pass
```

### 5.3 @引用解析器

```python
class RefResolver:
    """资产引用解析器 — 将 @角色名/@场景名 替换为实际描述"""

    def __init__(self, characters: list[Character], scenes: list[SceneLocation]):
        self._char_map = {c.name: c for c in characters}
        self._scene_map = {s.name: s for s in scenes}

    def resolve_character(self, ref: str) -> Character:
        """@沈念安 → Character 对象"""
        name = ref.lstrip("@").split("-")[0]
        return self._char_map.get(name)

    def resolve_scene(self, ref: str) -> SceneLocation:
        """@豪华酒店宴会厅 → SceneLocation 对象"""
        name = ref.lstrip("@").split("_")[0]
        return self._scene_map.get(name)

    def resolve_prompt(self, template: str) -> str:
        """将模板中的所有 @引用 替换为实际描述"""
        import re
        def replacer(match):
            ref = match.group(0)
            char = self.resolve_character(ref)
            if char:
                return char.description
            scene = self.resolve_scene(ref)
            if scene:
                return scene.description
            return ref
        return re.sub(r"@[\w\u4e00-\u9fff]+", replacer, template)
```

---

## 6. API 接口设计

### 6.1 RESTful 端点

#### 项目管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v2/projects` | 创建项目 |
| `GET` | `/api/v2/projects` | 项目列表 |
| `GET` | `/api/v2/projects/{id}` | 项目详情 |
| `PUT` | `/api/v2/projects/{id}` | 更新项目 |
| `DELETE` | `/api/v2/projects/{id}` | 删除项目 |

#### Step 1: 剧本

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v2/projects/{id}/script/generate` | AI 生成剧本 |
| `POST` | `/api/v2/projects/{id}/script/upload` | 上传 .docx 剧本 |
| `GET` | `/api/v2/projects/{id}/script` | 获取剧本 |
| `PUT` | `/api/v2/projects/{id}/script` | 编辑剧本 |
| `POST` | `/api/v2/projects/{id}/script/rewrite-narration` | 改写为旁白型 |
| `POST` | `/api/v2/projects/{id}/script/approve` | 审核通过 → 进入 Step 2 |

#### Step 2: 资产

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v2/projects/{id}/assets/generate` | 生成全部角色+场景 |
| `GET` | `/api/v2/projects/{id}/characters` | 获取角色列表 |
| `PUT` | `/api/v2/projects/{id}/characters/{cid}` | 编辑角色 |
| `POST` | `/api/v2/projects/{id}/characters/{cid}/regenerate` | 重新生成角色形象 |
| `GET` | `/api/v2/projects/{id}/scenes` | 获取场景列表 |
| `PUT` | `/api/v2/projects/{id}/scenes/{sid}` | 编辑场景 |
| `POST` | `/api/v2/projects/{id}/scenes/{sid}/regenerate` | 重新生成场景图 |
| `POST` | `/api/v2/projects/{id}/assets/approve` | 审核通过 → 进入 Step 3 |

#### Step 3: 视频

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v2/projects/{id}/episodes` | 获取分集列表 |
| `POST` | `/api/v2/projects/{id}/episodes/{eid}/storyboard` | 生成分镜脚本 |
| `GET` | `/api/v2/projects/{id}/episodes/{eid}/storyboard` | 获取分镜脚本 |
| `PUT` | `/api/v2/projects/{id}/episodes/{eid}/shots/{sid}` | 编辑单个分镜 |
| `POST` | `/api/v2/projects/{id}/episodes/{eid}/segments/{sid}/generate` | 生成单片段 |
| `POST` | `/api/v2/projects/{id}/episodes/{eid}/segments/{sid}/regenerate` | 重新生成 |
| `POST` | `/api/v2/projects/{id}/episodes/{eid}/compose` | 合成全集 |
| `POST` | `/api/v2/projects/{id}/export` | 导出项目 |

#### 资产库

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v2/assets` | 全局资产列表 |
| `POST` | `/api/v2/assets/upload` | 上传资产 |
| `DELETE` | `/api/v2/assets/{id}` | 删除资产 |
| `GET` | `/api/v2/assets/characters` | 角色资产列表 |

### 6.2 WebSocket 端点

```
WS /api/v2/ws/tasks/{task_id}
```

用于实时推送任务进度：

```json
// 进度推送
{
  "type": "progress",
  "task_id": "abc-123",
  "step": "generating_image",
  "current": 3,
  "total": 8,
  "message": "正在生成第3个分镜的图片..."
}

// 完成推送
{
  "type": "completed",
  "task_id": "abc-123",
  "result": { "segment_id": 1, "video_url": "/storage/..." }
}

// 错误推送
{
  "type": "error",
  "task_id": "abc-123",
  "error": "视频生成失败: 模型负载过高"
}
```

### 6.3 请求/响应模型示例

```python
# ---- 请求模型 ----

class ProjectCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    style: VideoStyle = VideoStyle.REALISTIC
    aspect_ratio: str = "16:9"
    genre: DramaGenre = DramaGenre.OTHER
    target_episodes: int = Field(default=5, ge=1, le=50)

class ScriptGenerateRequest(BaseModel):
    user_input: str = Field(..., min_length=10, max_length=10000)
    script_type: Literal["dialogue", "narration"] = "dialogue"

class ShotUpdate(BaseModel):
    duration: float | None = Field(None, ge=0.5, le=15)
    dialogue: str | None = None
    camera_type: CameraType | None = None
    camera_movement: CameraMovement | None = None
    voice_style: str | None = None

# ---- 响应模型 ----

class ProjectDetail(BaseModel):
    id: int
    title: str
    style: VideoStyle
    aspect_ratio: str
    genre: DramaGenre
    status: ProjectStep
    script: ScriptSummary | None
    characters_count: int
    scenes_count: int
    episodes_count: int
    created_at: datetime
    updated_at: datetime

class EpisodeOverview(BaseModel):
    id: int
    number: int
    title: str
    characters_count: int
    scenes_count: int
    shots_count: int
    duration: float
    status: str

class StoryboardDetail(BaseModel):
    episode: EpisodeOverview
    segments: list[SegmentDetail]
    total_duration: float
    style: str
```

---

## 7. 异步任务系统

### 7.1 任务类型

| 任务 | 耗时 | 优先级 | 可并行 |
|------|------|--------|--------|
| `generate_script` | 10~30s | 高 | ❌ |
| `generate_character_image` | 5~15s | 高 | ✅ |
| `generate_scene_image` | 5~15s | 高 | ✅ |
| `split_storyboard` | 10~20s | 中 | 按集并行 |
| `generate_shot_image` | 5~15s | 中 | ✅ |
| `generate_shot_audio` | 3~8s | 中 | ✅ |
| `generate_shot_video` | 30~120s | 低 | ✅ (限并发) |
| `compose_segment` | 5~15s | 中 | ✅ |
| `compose_episode` | 10~30s | 低 | ❌ |

### 7.2 ARQ 任务定义

```python
# app/tasks/video_tasks.py

async def generate_segment_task(ctx, segment_id: int):
    """生成单个片段的完整任务"""
    segment = await db.get(Segment, segment_id)
    segment.status = SegmentStatus.GENERATING
    await db.commit()

    try:
        engine = VideoEngine()
        # 通过 WebSocket 推送进度
        ws = ctx.get("ws_manager")

        for i, shot in enumerate(segment.shots):
            await ws.send_progress(segment_id, i+1, len(segment.shots))
            await engine._generate_shot_assets(shot)

        # 合成
        segment.video_url = await engine._ffmpeg_compose(segment)
        segment.status = SegmentStatus.DONE
        await ws.send_completed(segment_id, segment.video_url)

    except Exception as e:
        segment.status = SegmentStatus.FAILED
        await ws.send_error(segment_id, str(e))

    finally:
        await db.commit()
```

---

## 8. 存储与资产管理

### 8.1 目录结构

```
storage/
├── projects/
│   └── {project_id}/
│       ├── script/
│       │   └── script.json          # 结构化剧本
│       ├── characters/
│       │   ├── {char_id}_0.png      # 角色形象图 (可多套)
│       │   └── {char_id}_1.png
│       ├── scenes/
│       │   ├── {scene_id}_0.png     # 场景参考图
│       │   └── {scene_id}_1.png
│       ├── episodes/
│       │   └── {episode_num}/
│       │       ├── storyboard.json  # 分镜脚本
│       │       ├── shots/
│       │       │   ├── shot_01_img.png
│       │       │   ├── shot_01_audio.mp3
│       │       │   └── shot_01_video.mp4
│       │       ├── segments/
│       │       │   ├── segment_01.mp4
│       │       │   └── segment_02.mp4
│       │       └── final.mp4        # 合成的完整集视频
│       └── export/
│           └── final_all.mp4        # 全剧合成
├── assets/                          # 全局资产库
│   ├── uploaded/
│   └── generated/
└── temp/                            # 临时文件
```

### 8.2 资产服务

```python
class StorageService:
    """存储服务 — 管理文件读写和路径"""

    def project_path(self, project_id: int) -> Path
    def character_image_path(self, project_id: int, char_id: int, idx: int) -> Path
    def scene_image_path(self, project_id: int, scene_id: int, idx: int) -> Path
    def shot_image_path(self, project_id: int, ep_num: int, shot_idx: int) -> Path
    def shot_audio_path(self, project_id: int, ep_num: int, shot_idx: int) -> Path
    def segment_video_path(self, project_id: int, ep_num: int, seg_idx: int) -> Path
    def episode_video_path(self, project_id: int, ep_num: int) -> Path

    async def save_from_url(self, url: str, dest: Path) -> Path
    async def save_from_bytes(self, data: bytes, dest: Path) -> Path
    def get_url(self, path: Path) -> str
```

---

## 9. 部署方案

### 9.1 开发环境

```bash
# 1. 依赖安装
pip install -r requirements.txt

# 2. 环境配置
cp .env.example .env
# 编辑 .env, 填入 laozhang_api_key

# 3. 启动
uvicorn app.main:app --reload --port 8000
```

### 9.2 生产部署 (Docker)

```yaml
# docker-compose.yml
version: "3.9"
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    volumes:
      - ./storage:/app/storage
    depends_on: [redis, db]

  worker:
    build: .
    command: arq app.tasks.WorkerSettings
    env_file: .env
    depends_on: [redis, db]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: dramaforge
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data

  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [api]

volumes:
  pg_data:
```

### 9.3 requirements.txt (v2.0 预估)

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy[asyncio]>=2.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
httpx>=0.27.0
openai>=1.30.0
python-multipart>=0.0.9
python-docx>=1.1.0
arq>=0.26.0
redis>=5.0.0
loguru>=0.7.0
aiofiles>=24.0.0
Pillow>=10.0.0
```
