# DramaForge v2.0 — Spec 模式开发任务规划

> **日期**: 2026-04-01
> **开发顺序**: 先全部后端 → 再全部前端
> **粒度**: 每个 Spec 对应一个具体文件的实现
> **总计**: 后端 30 个 Spec + 前端 28 个 Spec = **58 个 Spec**
> **关联文档**:
> - [后端架构](./BACKEND_ARCHITECTURE.md)
> - [前端设计](./FRONTEND_DESIGN.md)
> - [工作流](./WORKFLOW.md)

---

## 任务概览

```
后端 Phase 1 — 基础层 (Spec 1~7)        ██░░░░░░░░  Week 1
后端 Phase 2 — 剧本引擎 (Spec 8~13)     ████░░░░░░  Week 2
后端 Phase 3 — 资产引擎 (Spec 14~20)    ██████░░░░  Week 3
后端 Phase 4 — 视频引擎 (Spec 21~30)    ████████░░  Week 4~5
前端 Phase 5 — 基础框架 (Spec 31~38)    ██████████░ Week 5~6
前端 Phase 6 — 业务页面 (Spec 39~50)    ████████████ Week 6~7
前端 Phase 7 — 分镜编辑器 (Spec 51~58)  ████████████ Week 7~8
```

---

## 后端 Phase 1 — 基础层

> 目标: 搭建数据库、配置、认证等基础设施，使后续所有 Spec 可以基于此运行

### Spec 1: 数据库引擎与会话管理

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/core/database.py` |
| **依赖** | `app/core/config.py` (✅ 已实现) |
| **功能** | SQLAlchemy 2.0 异步引擎、会话工厂、Base 声明基类 |
| **要点** | <ul><li>创建 `async_engine` (基于 `settings.database_url`)</li><li>创建 `AsyncSessionLocal` 工厂</li><li>实现 `get_db()` 依赖注入</li><li>实现 `init_db()` 自动建表</li><li>声明 `Base = declarative_base()`</li></ul> |
| **验收** | 可运行 `init_db()` 在 SQLite 中自动建表 |

---

### Spec 2: Project ORM 模型

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/models/project.py` |
| **依赖** | Spec 1 (`core/database.py`) |
| **功能** | Project 表定义 |
| **字段** | `id, title, description, style(VideoStyle), aspect_ratio, genre(DramaGenre), status(ProjectStep), script_type, created_at, updated_at` |
| **要点** | <ul><li>使用 Mapped 声明式映射</li><li>枚举字段使用 `Enum` 类型</li><li>添加 `relationship` 到 Script, Character, SceneLocation</li></ul> |
| **验收** | SQLAlchemy 可正常创建 projects 表 |

---

### Spec 3: Script + Episode ORM 模型

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/models/script.py` + `app/models/episode.py` |
| **依赖** | Spec 2 |
| **功能** | Script 表 + Episode 表定义 |
| **Script 字段** | `id, project_id(FK), protagonist, genre, synopsis, background, setting, one_liner, raw_content, is_approved, created_at` |
| **Episode 字段** | `id, script_id(FK), number, title, content, is_approved, created_at` |
| **要点** | <ul><li>Script 与 Project 1:1</li><li>Episode 与 Script 1:N</li></ul> |
| **验收** | 外键关系正确，级联删除正常 |

---

### Spec 4: Character + SceneLocation ORM 模型

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/models/character.py` + `app/models/scene.py` |
| **依赖** | Spec 2 |
| **功能** | Character 表 + SceneLocation 表定义 |
| **Character 字段** | `id, project_id(FK), name, role(CharacterRole), description, voice_desc, reference_images(JSON), created_at` |
| **Scene 字段** | `id, project_id(FK), name, description, time_of_day, interior(bool), reference_images(JSON), created_at` |
| **要点** | <ul><li>`reference_images` 使用 JSON 类型存储 URL 列表</li><li>与 Project 1:N</li></ul> |
| **验收** | JSON 字段可正常读写 |

---

### Spec 5: Segment + Shot ORM 模型

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/models/segment.py` + `app/models/shot.py` |
| **依赖** | Spec 3 (Episode) |
| **功能** | Segment 表 + Shot 表定义 |
| **Segment 字段** | `id, episode_id(FK), index, status(SegmentStatus), video_url, audio_url, thumbnail_url, duration, created_at` |
| **Shot 字段** | `id, segment_id(FK), index, duration, time_of_day, scene_ref, camera_type, camera_angle, camera_movement, characters(JSON), dialogue, voice_style, background, transition, image_prompt, video_prompt, image_url, audio_url, video_url, created_at` |
| **要点** | <ul><li>Shot 是最小生成单元</li><li>`characters` JSON 存储 `[{char_id, appearance_idx, action}]`</li></ul> |
| **验收** | 完整 ER 关系链: Project → Script → Episode → Segment → Shot |

---

### Spec 6: Models 统一导出 + 枚举定义

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/models/__init__.py` |
| **依赖** | Spec 2~5 |
| **功能** | 统一导出所有模型 + 定义枚举 |
| **要点** | <ul><li>定义 `ProjectStep, VideoStyle, DramaGenre, CameraType, CameraMovement, CharacterRole, SegmentStatus` 枚举</li><li>统一 `from app.models import *` 导出</li></ul> |
| **验收** | 任何模块可通过 `from app.models import Project, Character` 导入 |

---

### Spec 7: Pydantic Schemas (全部)

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/schemas/project.py` + `script.py` + `assets.py` + `episode.py` + `storyboard.py` + `__init__.py` |
| **依赖** | Spec 6 (枚举) |
| **功能** | 所有 API 请求/响应的 Pydantic 模型 |
| **关键 Schema** | <ul><li>`ProjectCreate`, `ProjectDetail`, `ProjectList`</li><li>`ScriptGenerateRequest`, `ScriptDetail`, `ScriptUpdate`</li><li>`CharacterDetail`, `CharacterUpdate`, `SceneDetail`, `SceneUpdate`</li><li>`EpisodeOverview`, `EpisodeDetail`</li><li>`ShotDetail`, `ShotUpdate`, `SegmentDetail`, `StoryboardDetail`</li></ul> |
| **验收** | 所有 Schema 可从 `from app.schemas import ProjectCreate` 导入 |

---

## 后端 Phase 2 — 剧本引擎 (Step 1)

> 目标: 实现从用户输入到结构化剧本的完整链路

### Spec 8: 剧本生成提示词升级

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/prompts/script_prompts.py` |
| **依赖** | 无 (✅ 已有基础版本) |
| **功能** | 升级提示词模板，输出 v2.0 结构化 JSON |
| **要点** | <ul><li>新增 `SCRIPT_STRUCTURED_PROMPT` — 强制 JSON 输出</li><li>输出需包含 `protagonist, genre, synopsis, background, setting, one_liner, episodes[], characters[], scenes[]`</li><li>新增 `NARRATION_REWRITE_PROMPT` — 对话→旁白转换</li><li>保留旧的 `build_script_prompt` 向后兼容</li></ul> |
| **验收** | 提示词可正确指导 LLM 输出预期 JSON 格式 |

---

### Spec 9: 角色描述提示词

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/prompts/character_prompts.py` |
| **依赖** | 无 |
| **功能** | 角色外貌/性格/音色描述的提示词模板 |
| **要点** | <ul><li>`CHARACTER_DESC_PROMPT` — 输入角色名+剧本片段，输出 JSON: `{appearance, personality, role, voice}`</li><li>`SCENE_DESC_PROMPT` — 输入场景名+背景，输出 JSON: `{description, image_prompts[]}`</li></ul> |
| **验收** | 提示词格式规范，可生成合理的角色/场景描述 |

---

### Spec 10: ScriptEngine 实现

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/engines/script_engine.py` |
| **依赖** | Spec 7 (Schemas), Spec 8 (Prompts), AI Hub (✅ 已实现) |
| **功能** | 剧本引擎核心逻辑 |
| **方法** | <ul><li>`create_from_text(user_input, project) → Script` — AI 生成剧本</li><li>`create_from_docx(file_path, project) → Script` — 解析上传剧本</li><li>`rewrite_to_narration(script) → Script` — 改写旁白型</li><li>`_parse_script(raw_json) → Script` — JSON 解析</li><li>`_extract_characters(raw) → list[str]` — 提取角色名</li><li>`_extract_scenes(raw) → list[str]` — 提取场景名</li></ul> |
| **验收** | 输入一段故事构想，返回结构化 Script + Episode[] |

---

### Spec 11: StorageService 实现

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/services/storage.py` |
| **依赖** | Spec 1 (config) |
| **功能** | 文件存储管理服务 |
| **方法** | <ul><li>`project_path(project_id) → Path`</li><li>`character_image_path(project_id, char_id, idx) → Path`</li><li>`scene_image_path(project_id, scene_id, idx) → Path`</li><li>`shot_image_path(project_id, ep_num, shot_idx) → Path`</li><li>`shot_audio_path(...)` / `segment_video_path(...)` / `episode_video_path(...)`</li><li>`save_from_url(url, dest) → Path` — 下载远程文件到本地</li><li>`save_from_bytes(data, dest) → Path`</li><li>`get_url(path) → str` — 生成可访问的 URL</li></ul> |
| **验收** | 可正确创建目录、下载文件、返回路径 |

---

### Spec 12: Projects API 端点

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/api/v2/projects.py` |
| **依赖** | Spec 2 (Project 模型), Spec 7 (Schemas), Spec 1 (get_db) |
| **功能** | 项目 CRUD |
| **端点** | <ul><li>`POST /projects` — 创建项目</li><li>`GET /projects` — 项目列表 (分页)</li><li>`GET /projects/{id}` — 项目详情</li><li>`PUT /projects/{id}` — 更新项目</li><li>`DELETE /projects/{id}` — 删除项目</li></ul> |
| **验收** | 5 个端点全部可通过 Swagger 测试通过 |

---

### Spec 13: Scripts API 端点

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/api/v2/scripts.py` |
| **依赖** | Spec 10 (ScriptEngine), Spec 12 (Projects) |
| **功能** | 剧本生成/编辑 API |
| **端点** | <ul><li>`POST /projects/{id}/script/generate` — AI 生成剧本</li><li>`POST /projects/{id}/script/upload` — 上传 .docx</li><li>`GET /projects/{id}/script` — 获取剧本</li><li>`PUT /projects/{id}/script` — 编辑剧本</li><li>`POST /projects/{id}/script/rewrite-narration` — 改写旁白</li><li>`POST /projects/{id}/script/approve` — 审核通过</li></ul> |
| **验收** | 创建项目 → 生成剧本 → 编辑 → 审核通过，完整流程跑通 |

---

## 后端 Phase 3 — 资产引擎 (Step 2)

> 目标: 实现角色/场景的自动生成和管理

### Spec 14: AssetsEngine 实现

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/engines/assets_engine.py` |
| **依赖** | Spec 9 (Prompts), Spec 11 (Storage), AI Hub |
| **功能** | 资产引擎核心逻辑 |
| **方法** | <ul><li>`generate_all_assets(script, characters, scenes) → (Character[], SceneLocation[])` — 并行生成全部</li><li>`_generate_character(name, script) → Character` — 单角色</li><li>`_generate_scene(name, script) → SceneLocation` — 单场景</li><li>`regenerate_character_image(char_id, prompt) → str` — 重新生成</li><li>`regenerate_scene_image(scene_id, prompt) → str` — 重新生成</li></ul> |
| **验收** | 给定角色名列表和场景名列表，并行生成全部形象图 |

---

### Spec 15: Assets API 端点

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/api/v2/assets.py` |
| **依赖** | Spec 14 (AssetsEngine) |
| **功能** | 资产生成/管理 API |
| **端点** | <ul><li>`POST /projects/{id}/assets/generate` — 生成全部资产</li><li>`GET /projects/{id}/characters` — 角色列表</li><li>`PUT /projects/{id}/characters/{cid}` — 编辑角色</li><li>`POST /projects/{id}/characters/{cid}/regenerate` — 重生成角色图</li><li>`GET /projects/{id}/scenes` — 场景列表</li><li>`PUT /projects/{id}/scenes/{sid}` — 编辑场景</li><li>`POST /projects/{id}/scenes/{sid}/regenerate` — 重生成场景图</li><li>`POST /projects/{id}/assets/approve` — 审核通过</li></ul> |
| **验收** | 审核通过剧本 → 生成资产 → 编辑/替换 → 审核通过，完整流程 |

---

### Spec 16: AI Hub PromptService 实现

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/ai_hub/prompt.py` |
| **依赖** | AI Hub chat (✅ 已实现) |
| **功能** | 提示词优化 + 提示词构建 |
| **方法** | <ul><li>`optimize(raw_prompt, context) → str` — 一键优化</li><li>`build_image_prompt(shot, characters, scenes, style) → str` — 构建图片提示词</li><li>`build_video_prompt(shot, characters, scenes) → str` — 构建视频提示词</li></ul> |
| **验收** | 输入分镜数据，输出完整的、可用于图片/视频生成的英文提示词 |

---

### Spec 17: RefResolver 引用解析器

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/services/ref_resolver.py` |
| **依赖** | Spec 4 (Character, SceneLocation 模型) |
| **功能** | @引用解析 |
| **方法** | <ul><li>`__init__(characters, scenes)` — 构建查找索引</li><li>`resolve_character(ref) → Character` — `@沈念安` → 对象</li><li>`resolve_scene(ref) → SceneLocation` — `@宴会厅` → 对象</li><li>`resolve_prompt(template) → str` — 替换模板中所有 @引用</li></ul> |
| **验收** | 输入含 `@角色名` 的文本，输出替换后的完整描述 |

---

### Spec 18: 全局资产库 API

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/api/v2/assets.py` (追加) |
| **依赖** | Spec 15 |
| **功能** | 全局资产库端点 |
| **端点** | <ul><li>`GET /assets` — 全局资产列表 (分页/筛选)</li><li>`POST /assets/upload` — 上传资产</li><li>`DELETE /assets/{id}` — 删除资产</li><li>`GET /assets/characters` — 全局角色资产</li></ul> |
| **验收** | 可跨项目查看和管理资产 |

---

### Spec 19: Episodes API 端点

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/api/v2/episodes.py` |
| **依赖** | Spec 3 (Episode 模型) |
| **功能** | 分集管理 |
| **端点** | <ul><li>`GET /projects/{id}/episodes` — 分集列表 (含统计)</li><li>`GET /projects/{id}/episodes/{eid}` — 分集详情</li></ul> |
| **验收** | 返回每集的角色数、场景数、分镜数、时长统计 |

---

### Spec 20: AI Hub __init__ 升级

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/ai_hub/__init__.py` |
| **依赖** | Spec 16 (PromptService) |
| **功能** | 将 PromptService 注册到 ai_hub 门面 |
| **要点** | <ul><li>添加 `self.prompt = PromptService()` 到 AIHub</li><li>确保 `ai_hub.prompt.optimize()` 可调用</li></ul> |
| **验收** | `from app.ai_hub import ai_hub; ai_hub.prompt.optimize(...)` 正常工作 |

---

## 后端 Phase 4 — 视频引擎 (Step 3)

> 目标: 实现分镜拆解、视频生成、合成的完整链路

### Spec 21: 分镜提示词升级

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/prompts/storyboard_prompts.py` |
| **依赖** | 无 (✅ 已有基础版本) |
| **功能** | 升级为 v2.0 分镜拆解提示词 |
| **要点** | <ul><li>新增 `STORYBOARD_STRUCTURED_PROMPT` — 输出 Shot 级别 JSON</li><li>每个 Shot 包含: duration, time_of_day, scene_ref, camera_type, camera_angle, camera_movement, characters, dialogue, voice_style, background, transition</li><li>使用 @引用 格式引用角色和场景</li></ul> |
| **验收** | 给定剧本+角色+场景上下文，LLM 输出结构化 Shot[] |

---

### Spec 22: VideoEngine — 分镜拆解

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/engines/video_engine.py` |
| **依赖** | Spec 21, Spec 17 (RefResolver), AI Hub |
| **功能** | 视频引擎第 ①②步: LLM 拆分分镜 + @引用解析 |
| **方法** | <ul><li>`split_storyboard(episode, characters, scenes) → list[Shot]`</li><li>`_build_asset_context(characters, scenes) → str`</li><li>`_group_into_segments(shots) → list[Segment]`</li></ul> |
| **验收** | 给定一集剧本，输出结构化 Shot 列表并按片段分组 |

---

### Spec 23: VideoEngine — 资产生成

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/engines/video_engine.py` (追加) |
| **依赖** | Spec 22, Spec 16 (PromptService) |
| **功能** | 视频引擎第 ③步: 并行生成图片+音频 |
| **方法** | <ul><li>`_generate_shot_assets(shot, characters, scenes) → Shot` — 并行生图+TTS</li><li>`_resolve_refs(shot, characters, scenes) → str` — 生成完整提示词</li></ul> |
| **验收** | 单个 Shot 可并行生成图片和音频 |

---

### Spec 24: VideoEngine — 视频策略决策

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/engines/video_engine.py` (追加) |
| **依赖** | Spec 23 |
| **功能** | 视频引擎第 ④步: 决策视频生成策略 |
| **方法** | <ul><li>`_decide_video_strategy(segment) → str` — 返回 `"ai_video"` / `"img2video"` / `"static_compose"`</li><li>`_generate_segment_video(segment) → str` — 根据策略生成视频</li></ul> |
| **验收** | 静态镜头走 FFmpeg，运动镜头走 AI 视频 |

---

### Spec 25: FFmpeg 合成服务

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/services/ffmpeg.py` |
| **依赖** | Spec 11 (Storage) |
| **功能** | FFmpeg 视频合成操作 |
| **方法** | <ul><li>`compose_static_video(image_path, audio_path, duration, output_path)` — 图片+音频→视频</li><li>`concat_segments(segment_paths, output_path)` — 多段拼接</li><li>`add_subtitle(video_path, subtitle_text, output_path)` — 添加字幕</li><li>`compose_episode(segment_paths, output_path, bgm_path?)` — 全集合成</li></ul> |
| **验收** | 给定图片+音频，输出合成的 mp4 视频 |

---

### Spec 26: VideoEngine — 完整生成流程

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/engines/video_engine.py` (追加) |
| **依赖** | Spec 22~25 |
| **功能** | 视频引擎完整流程编排 |
| **方法** | <ul><li>`generate_episode(episode, characters, scenes) → list[Segment]` — 生成单集</li><li>`regenerate_segment(segment_id) → Segment` — 重新生成单片段</li><li>`compose_full_episode(episode_id) → str` — 合成全集视频</li></ul> |
| **验收** | 端到端: 剧本 → 分镜拆解 → 资产生成 → 视频合成 |

---

### Spec 27: Storyboard API 端点

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/api/v2/storyboard.py` |
| **依赖** | Spec 26 (VideoEngine) |
| **功能** | 分镜编辑 API |
| **端点** | <ul><li>`POST /projects/{id}/episodes/{eid}/storyboard` — 生成分镜脚本</li><li>`GET /projects/{id}/episodes/{eid}/storyboard` — 获取分镜</li><li>`PUT /projects/{id}/episodes/{eid}/shots/{sid}` — 编辑分镜</li><li>`POST .../segments/{sid}/generate` — 生成单片段</li><li>`POST .../segments/{sid}/regenerate` — 重新生成</li><li>`POST .../episodes/{eid}/compose` — 合成全集</li><li>`POST /projects/{id}/export` — 导出</li></ul> |
| **验收** | 生成分镜 → 编辑 → 生成片段 → 合成全集，完整流程 |

---

### Spec 28: 异步任务 — 资产生成

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/tasks/asset_tasks.py` |
| **依赖** | Spec 14 (AssetsEngine) |
| **功能** | 资产生成的异步任务 |
| **任务** | <ul><li>`generate_all_assets_task(project_id)` — Step 2 全部资产</li><li>`regenerate_character_task(char_id, prompt)` — 重生成角色</li></ul> |
| **验收** | 任务可入队、执行、返回结果 |

---

### Spec 29: 异步任务 — 视频生成

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/tasks/video_tasks.py` |
| **依赖** | Spec 26 (VideoEngine) |
| **功能** | 视频生成的异步任务 |
| **任务** | <ul><li>`generate_segment_task(segment_id)` — 生成单片段</li><li>`compose_episode_task(episode_id)` — 合成全集</li></ul> |
| **验收** | 任务可入队、执行、推送进度、返回结果 |

---

### Spec 30: WebSocket 实时推送

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_bac/app/api/v2/websocket.py` |
| **依赖** | Spec 28~29 |
| **功能** | WebSocket 端点 + 连接管理 |
| **端点** | `WS /api/v2/ws/tasks/{task_id}` |
| **要点** | <ul><li>`ConnectionManager` 管理活跃连接</li><li>推送 `progress` / `completed` / `error` 消息</li><li>支持断线重连</li></ul> |
| **验收** | 前端可通过 WS 实时接收任务进度 |

---

## 前端 Phase 5 — 基础框架

> 目标: 搭建 Vue 3 项目基础设施、路由、布局、状态管理

### Spec 31: 项目初始化 + 依赖安装

| 属性 | 值 |
|------|-----|
| **文件** | `dramaForge_web/package.json`, `vite.config.ts`, `tsconfig.json` |
| **功能** | 安装核心依赖 |
| **依赖包** | `vue-router, pinia, axios, tailwindcss, @iconify/vue, naive-ui` |
| **验收** | `npm run dev` 启动无报错 |

---

### Spec 32: TailwindCSS 配置 + 设计规范

| 属性 | 值 |
|------|-----|
| **文件** | `tailwind.config.ts`, `src/style.css` |
| **功能** | 按设计规范配置色彩、字体、间距 |
| **要点** | 主色 `#6366f1`、中性色、功能色、暗色模式变量 |
| **验收** | TailwindCSS 工具类可正常使用 |

---

### Spec 33: TypeScript 类型定义

| 属性 | 值 |
|------|-----|
| **文件** | `src/types/enums.ts` + `project.ts` + `script.ts` + `character.ts` + `scene.ts` + `episode.ts` + `segment.ts` + `shot.ts` |
| **功能** | 前端所有 TypeScript 类型/接口定义 (对齐后端 Schema) |
| **验收** | 所有类型可从 `@/types` 导入 |

---

### Spec 34: API 客户端 + 请求封装

| 属性 | 值 |
|------|-----|
| **文件** | `src/api/client.ts` + `projects.ts` + `scripts.ts` + `assets.ts` + `episodes.ts` + `storyboard.ts` |
| **功能** | Axios 实例配置 + 各模块 API 函数封装 |
| **要点** | Base URL、请求/响应拦截器、错误处理 |
| **验收** | `api.projects.create({...})` 可正常发请求 |

---

### Spec 35: WebSocket 客户端

| 属性 | 值 |
|------|-----|
| **文件** | `src/api/websocket.ts` |
| **功能** | WebSocket 管理器 (连接/断线重连/事件分发) |
| **验收** | 可连接后端 WS 端点并接收消息 |

---

### Spec 36: Vue Router 路由配置

| 属性 | 值 |
|------|-----|
| **文件** | `src/router.ts` |
| **功能** | 完整路由表 (9个页面 + 子路由) |
| **验收** | 所有页面路由可正常导航 |

---

### Spec 37: Pinia Store — project + tasks

| 属性 | 值 |
|------|-----|
| **文件** | `src/stores/project.ts` + `tasks.ts` |
| **功能** | 项目状态管理 + 异步任务管理 |
| **要点** | `currentProject`, `currentStep`, `nextStep()`, `activeTasks`, `watchTask()` |
| **验收** | Store 可在组件中注入使用 |

---

### Spec 38: AppHeader + AppSidebar + App.vue

| 属性 | 值 |
|------|-----|
| **文件** | `src/components/common/AppHeader.vue` + `AppSidebar.vue` + `App.vue` + `main.ts` |
| **功能** | 全局布局框架 |
| **要点** | 顶部导航栏 (logo + 导航 + 用户信息) + 可折叠侧边栏 |
| **验收** | 基础布局渲染正常，路由切换正常 |

---

## 前端 Phase 6 — 业务页面

> 目标: 实现三步工作流的所有业务页面

### Spec 39: HomePage — 首页

| 文件 | `src/views/HomePage.vue` + `components/home/*` (4个) |
| 功能 | 创作入口 (输入框 + 快捷标签 + 功能卡片 + 历史列表) |

### Spec 40: ProjectListPage — 项目列表

| 文件 | `src/views/ProjectListPage.vue` |
| 功能 | 项目卡片网格 + 搜索/筛选 |

### Spec 41: ProjectLayout + StepNavigator

| 文件 | `src/views/ProjectLayout.vue` + `components/common/StepNavigator.vue` |
| 功能 | 项目详情布局容器 + 三步导航组件 |

### Spec 42: ScriptPage — 剧本大纲 (Step 1)

| 文件 | `src/views/ScriptPage.vue` + `stores/script.ts` |
| 功能 | 剧本元数据表单 + 分集内容展示 + 审核按钮 |

### Spec 43: ScriptMetaForm + ScriptEditor

| 文件 | `src/components/script/ScriptMetaForm.vue` + `ScriptEditor.vue` |
| 功能 | 剧本元数据编辑表单 + 富文本剧本编辑器 |

### Spec 44: EpisodeAccordion + NarrationToggle

| 文件 | `src/components/script/EpisodeAccordion.vue` + `NarrationToggle.vue` |
| 功能 | 分集折叠面板 + 对话/旁白切换按钮 |

### Spec 45: AssetsPage — 角色与场景 (Step 2)

| 文件 | `src/views/AssetsPage.vue` + `stores/assets.ts` |
| 功能 | 角色/场景 Tab 切换 + 卡片网格 + 审核按钮 |

### Spec 46: CharacterCard + CharacterEditModal

| 文件 | `src/components/assets/CharacterCard.vue` + `CharacterEditModal.vue` |
| 功能 | 角色卡片 (头像+名称+类型+音色) + 编辑弹窗 |

### Spec 47: SceneCard + SceneEditModal

| 文件 | `src/components/assets/SceneCard.vue` + `SceneEditModal.vue` |
| 功能 | 场景卡片 (参考图+名称) + 编辑弹窗 |

### Spec 48: EpisodesPage — 分集列表 (Step 3)

| 文件 | `src/views/EpisodesPage.vue` + `components/episodes/EpisodeCard.vue` + `EpisodeList.vue` |
| 功能 | 分集卡片列表 (角色数/场景数/分镜数/时长/状态) |

### Spec 49: AssetLibraryPage — 资产库

| 文件 | `src/views/AssetLibraryPage.vue` + `components/library/*` (3个) |
| 功能 | 全局资产管理 (Grid/List 视图 + 上传 + 筛选 + 删除) |

### Spec 50: 通用组件补全

| 文件 | `components/common/LoadingOverlay.vue` + `ConfirmDialog.vue` + `EmptyState.vue` |
| 功能 | 加载遮罩 + 确认弹窗 + 空状态占位 |

---

## 前端 Phase 7 — 分镜编辑器

> 目标: 实现最核心的分镜编辑器页面 (三栏布局 + 时间线)

### Spec 51: StoryboardEditorPage — 页面框架

| 文件 | `src/views/StoryboardEditorPage.vue` + `stores/storyboard.ts` + `stores/timeline.ts` |
| 功能 | 三栏 + 底栏布局框架、Pinia 状态管理 |

### Spec 52: AssetPanel — 左侧资产面板

| 文件 | `src/components/storyboard/AssetPanel.vue` |
| 功能 | 角色列表 + 场景列表 + 旁白配置 (带缩略图) |

### Spec 53: StoryboardScript — 中间脚本区

| 文件 | `src/components/storyboard/StoryboardScript.vue` |
| 功能 | 片段标题 + Shot 卡片列表 + 编辑/重新生成按钮 |

### Spec 54: ShotCard + ShotEditor

| 文件 | `src/components/storyboard/ShotCard.vue` + `ShotEditor.vue` |
| 功能 | 单个分镜卡片 (所有字段展示/内联编辑) |

### Spec 55: RefAutocomplete — @引用自动补全

| 文件 | `src/components/storyboard/RefAutocomplete.vue` |
| 功能 | 输入 `@` 弹出角色/场景选择器下拉菜单 |

### Spec 56: DurationSlider — 时长滑块

| 文件 | `src/components/storyboard/DurationSlider.vue` |
| 功能 | 0~15s 可拖动时长控制器 |

### Spec 57: PreviewPanel + VideoPlayer — 右侧预览

| 文件 | `src/components/storyboard/PreviewPanel.vue` + `VideoPlayer.vue` |
| 功能 | 视频播放器 + 图片/音频预览 + 分镜详情面板 |

### Spec 58: Timeline + TimelineItem — 底部时间线

| 文件 | `src/components/storyboard/Timeline.vue` + `TimelineItem.vue` |
| 功能 | 水平时间线 (缩略图 + 时长 + 拖拽排序 + 多选 + 播放进度) |

---

## 执行清单

### 后端 (Spec 1~30)

```
Phase 1 基础层:
  □ Spec 1:  database.py — 数据库引擎
  □ Spec 2:  project.py — Project 模型
  □ Spec 3:  script.py + episode.py — Script/Episode 模型
  □ Spec 4:  character.py + scene.py — Character/Scene 模型
  □ Spec 5:  segment.py + shot.py — Segment/Shot 模型
  □ Spec 6:  models/__init__.py — 统一导出+枚举
  □ Spec 7:  schemas/*.py — 全部 Pydantic Schema

Phase 2 剧本引擎:
  □ Spec 8:  script_prompts.py — 提示词升级
  □ Spec 9:  character_prompts.py — 角色/场景提示词
  □ Spec 10: script_engine.py — 剧本引擎
  □ Spec 11: storage.py — 存储服务
  □ Spec 12: api/projects.py — 项目 API
  □ Spec 13: api/scripts.py — 剧本 API

Phase 3 资产引擎:
  □ Spec 14: assets_engine.py — 资产引擎
  □ Spec 15: api/assets.py — 资产 API
  □ Spec 16: prompt.py — PromptService
  □ Spec 17: ref_resolver.py — @引用解析
  □ Spec 18: api/assets.py — 全局资产库 API
  □ Spec 19: api/episodes.py — 分集 API
  □ Spec 20: ai_hub/__init__.py — 升级

Phase 4 视频引擎:
  □ Spec 21: storyboard_prompts.py — 提示词升级
  □ Spec 22: video_engine.py — 分镜拆解
  □ Spec 23: video_engine.py — 资产生成
  □ Spec 24: video_engine.py — 视频策略
  □ Spec 25: ffmpeg.py — FFmpeg 合成
  □ Spec 26: video_engine.py — 完整流程
  □ Spec 27: api/storyboard.py — 分镜 API
  □ Spec 28: asset_tasks.py — 资产异步任务
  □ Spec 29: video_tasks.py — 视频异步任务
  □ Spec 30: websocket.py — WS 推送
```

### 前端 (Spec 31~58)

```
Phase 5 基础框架:
  □ Spec 31: 项目初始化 + 依赖
  □ Spec 32: TailwindCSS + 设计规范
  □ Spec 33: TypeScript 类型定义
  □ Spec 34: API 客户端封装
  □ Spec 35: WebSocket 客户端
  □ Spec 36: Vue Router 路由
  □ Spec 37: Pinia Store
  □ Spec 38: 全局布局

Phase 6 业务页面:
  □ Spec 39: HomePage
  □ Spec 40: ProjectListPage
  □ Spec 41: ProjectLayout + StepNavigator
  □ Spec 42: ScriptPage
  □ Spec 43: ScriptMetaForm + ScriptEditor
  □ Spec 44: EpisodeAccordion + NarrationToggle
  □ Spec 45: AssetsPage
  □ Spec 46: CharacterCard + CharacterEditModal
  □ Spec 47: SceneCard + SceneEditModal
  □ Spec 48: EpisodesPage
  □ Spec 49: AssetLibraryPage
  □ Spec 50: 通用组件补全

Phase 7 分镜编辑器:
  □ Spec 51: StoryboardEditorPage 框架
  □ Spec 52: AssetPanel
  □ Spec 53: StoryboardScript
  □ Spec 54: ShotCard + ShotEditor
  □ Spec 55: RefAutocomplete
  □ Spec 56: DurationSlider
  □ Spec 57: PreviewPanel + VideoPlayer
  □ Spec 58: Timeline + TimelineItem
```