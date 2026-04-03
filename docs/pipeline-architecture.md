# DramaForge 工作流 Pipeline 架构设计

> 后端采用 Pipeline 编排模式，每种创作模式对应一条独立的 Pipeline
> 更新日期：2026-04-03

---

## 一、核心概念

### 1.1 架构概览

```
用户请求 (CreationRequest)
    │
    ▼
┌─────────────────────────────┐
│     Pipeline Dispatcher     │  ← 根据 mode 分发到对应 Pipeline
└─────────┬───────────────────┘
          │
    ┌─────┼─────┬─────────┬──────────┬──────────┐
    ▼     ▼     ▼         ▼          ▼          ▼
 Agent  Drama  Clip   LongVideo2  Image   LongVideo
Pipeline Pipeline Pipeline Pipeline Pipeline Pipeline
    │     │     │         │          │          │
    ▼     ▼     ▼         ▼          ▼          ▼
  [Stage1 → Stage2 → Stage3 → ... → StageN]
    │
    ▼
┌─────────────────────────────┐
│      Pipeline Context       │  ← 各 Stage 共享的上下文数据
└─────────────────────────────┘
```

### 1.2 核心术语

| 概念 | 说明 |
|------|------|
| **Pipeline** | 一条完整的创作工作流，由有序的 Stage 组成 |
| **Stage** | Pipeline 中的一个处理阶段，执行具体任务 |
| **StageResult** | 每个 Stage 的执行结果（成功/失败/跳过） |
| **PipelineContext** | 贯穿整条 Pipeline 的共享上下文数据 |
| **PipelineRegistry** | Pipeline 注册表，管理所有 Pipeline 定义 |
| **PipelineRunner** | Pipeline 执行引擎，驱动 Stage 顺序执行 |
| **Hook** | 生命周期钩子（before_stage / after_stage / on_error） |

---

## 二、Pipeline 定义

### 2.1 六种模式的 Pipeline

#### Pipeline 1：Agent 模式

```
agent_pipeline:
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ 意图识别  │ →  │ 提示词优化 │ →  │ 模型路由  │ →  │ 内容生成  │ →  │ 结果编排  │
  │ Intent   │    │ Prompt   │    │ Model    │    │ Generate │    │ Compose  │
  │ Parse    │    │ Enhance  │    │ Router   │    │          │    │          │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
       │                                               │
       ▼                                               ▼
  识别用户意图：                                    根据意图调用：
  - 生成图片？                                     - 图片生成 API
  - 生成视频？                                     - 视频生成 API
  - 写脚本？                                       - 脚本生成 API
  - 多任务组合？                                    - 组合任务
```

#### Pipeline 2：沉浸式短片（Clip）

```
clip_pipeline:
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ 素材解析  │ →  │ 提示词优化 │ →  │ 参考融合  │ →  │ 视频生成  │ →  │ 后处理   │
  │ Asset    │    │ Prompt   │    │ Style    │    │ Video    │    │ Post     │
  │ Resolve  │    │ Enhance  │    │ Fusion   │    │ Generate │    │ Process  │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
       │                               │               │               │
       ▼                               ▼               ▼               ▼
  解析@引用素材                     合并参考风格        调用 Seedance    添加字幕/配乐
  + 上传素材                       + 比例参数          2.0 Fast API    + 格式转码
```

#### Pipeline 3：智能长视频 2.0

```
longvideo2_pipeline:
  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ 脚本生成  │ → │ 分镜拆解  │ → │ 素材匹配  │ → │ 逐镜生成  │ → │ 音频合成  │ → │ 视频合成  │
  │ Script   │   │ Scene    │   │ Asset    │   │ Per-Shot │   │ Audio    │   │ Video    │
  │ Generate │   │ Split    │   │ Match    │   │ Generate │   │ Compose  │   │ Compose  │
  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
       │               │               │               │               │               │
       ▼               ▼               ▼               ▼               ▼               ▼
  LLM 生成完整      按分镜点拆       为每个分镜       并行生成每       TTS + 配乐      拼接所有片段
  故事脚本          为 N 个镜头      匹配/生成素材    个镜头视频       + 音效合成      + 转场特效
```

#### Pipeline 4：生成图片

```
image_pipeline:
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ 提示词优化 │ →  │ 参数组装  │ →  │ 图片生成  │ →  │ 后处理   │
  │ Prompt   │    │ Params   │    │ Image    │    │ Post     │
  │ Enhance  │    │ Assemble │    │ Generate │    │ Process  │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘
       │               │               │               │
       ▼               ▼               ▼               ▼
  AI 扩写/翻译      比例 + 模型       调用 Seedream    超分/去噪/
  优化提示词        + 风格参数        图片生成 API     格式转换
```

#### Pipeline 5：智能长视频（基础版）

```
longvideo_pipeline:
  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ 脚本生成  │ → │ 分镜拆解  │ → │ 逐镜生成  │ → │ 音频合成  │ → │ 视频合成  │
  │ Script   │   │ Scene    │   │ Per-Shot │   │ Audio    │   │ Video    │
  │ Generate │   │ Split    │   │ Generate │   │ Compose  │   │ Compose  │
  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

#### Pipeline 6：短剧 Agent（跳转专属页面，暂不走 Pipeline）

> 短剧 Agent 有独立的工作台页面，不通过对话框 Pipeline 处理。

---

## 三、代码架构设计

### 3.1 目录结构

```
dramaforge_server/
├── pipeline/
│   ├── __init__.py
│   ├── base.py              # Pipeline 基类、Stage 基类、Context
│   ├── runner.py             # PipelineRunner 执行引擎
│   ├── registry.py           # PipelineRegistry 注册表
│   ├── context.py            # PipelineContext 上下文
│   ├── exceptions.py         # 异常定义
│   │
│   ├── stages/               # 可复用的 Stage 实现
│   │   ├── __init__.py
│   │   ├── intent_parse.py   # 意图识别
│   │   ├── prompt_enhance.py # 提示词优化
│   │   ├── model_router.py   # 模型路由
│   │   ├── asset_resolve.py  # 素材解析
│   │   ├── style_fusion.py   # 风格融合
│   │   ├── script_generate.py# 脚本生成
│   │   ├── scene_split.py    # 分镜拆解
│   │   ├── video_generate.py # 视频生成
│   │   ├── image_generate.py # 图片生成
│   │   ├── audio_compose.py  # 音频合成
│   │   ├── video_compose.py  # 视频合成
│   │   └── post_process.py   # 后处理
│   │
│   └── pipelines/            # Pipeline 定义（编排 Stage）
│       ├── __init__.py
│       ├── agent.py          # Agent 模式 Pipeline
│       ├── clip.py           # 沉浸式短片 Pipeline
│       ├── longvideo2.py     # 智能长视频 2.0 Pipeline
│       ├── image.py          # 生成图片 Pipeline
│       └── longvideo.py      # 智能长视频 Pipeline
│
├── api/
│   └── v1/
│       └── creations.py      # 创作 API 入口
│
└── models/
    └── creation.py           # Creation 数据模型
```

### 3.2 核心基类

```python
# pipeline/base.py

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional
import time
import uuid


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    status: StageStatus
    data: dict = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: int = 0


class PipelineContext:
    """贯穿整条 Pipeline 的共享上下文"""
    
    def __init__(self, creation_id: str, request: dict):
        self.creation_id = creation_id
        self.request = request          # 原始请求参数
        self.data: dict = {}            # Stage 间共享数据
        self.results: dict[str, StageResult] = {}  # 各 Stage 结果
        self.metadata: dict = {
            "start_time": time.time(),
            "pipeline": None,
            "current_stage": None,
        }
    
    def set(self, key: str, value: Any):
        """设置共享数据"""
        self.data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取共享数据"""
        return self.data.get(key, default)
    
    @property
    def prompt(self) -> str:
        return self.request.get("prompt", "")
    
    @property
    def mode(self) -> str:
        return self.request.get("mode", "agent")
    
    @property
    def model(self) -> Optional[str]:
        return self.request.get("model")
    
    @property
    def aspect_ratio(self) -> Optional[str]:
        return self.request.get("aspectRatio")


class Stage(ABC):
    """Pipeline Stage 基类"""
    
    name: str = "base_stage"
    description: str = ""
    
    def should_skip(self, ctx: PipelineContext) -> bool:
        """判断是否跳过该 Stage"""
        return False
    
    @abstractmethod
    async def execute(self, ctx: PipelineContext) -> StageResult:
        """执行 Stage 逻辑"""
        ...
    
    async def on_error(self, ctx: PipelineContext, error: Exception):
        """错误处理钩子"""
        pass
    
    async def run(self, ctx: PipelineContext) -> StageResult:
        """运行 Stage（含跳过判断、计时、错误处理）"""
        if self.should_skip(ctx):
            result = StageResult(status=StageStatus.SKIPPED)
            ctx.results[self.name] = result
            return result
        
        start = time.time()
        ctx.metadata["current_stage"] = self.name
        
        try:
            result = await self.execute(ctx)
            result.duration_ms = int((time.time() - start) * 1000)
            ctx.results[self.name] = result
            return result
        except Exception as e:
            await self.on_error(ctx, e)
            result = StageResult(
                status=StageStatus.FAILED,
                error=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )
            ctx.results[self.name] = result
            raise


class Pipeline:
    """Pipeline 基类 — 由有序的 Stage 列表组成"""
    
    name: str = "base_pipeline"
    description: str = ""
    
    def __init__(self):
        self.stages: list[Stage] = []
        self.hooks: dict[str, list] = {
            "before_pipeline": [],
            "after_pipeline": [],
            "before_stage": [],
            "after_stage": [],
            "on_error": [],
        }
    
    def add_stage(self, stage: Stage) -> "Pipeline":
        """添加 Stage"""
        self.stages.append(stage)
        return self
    
    def add_stages(self, *stages: Stage) -> "Pipeline":
        """批量添加 Stage"""
        self.stages.extend(stages)
        return self
    
    def add_hook(self, event: str, callback):
        """添加生命周期钩子"""
        self.hooks[event].append(callback)
        return self
    
    def get_stage_names(self) -> list[str]:
        """获取所有 Stage 名称"""
        return [s.name for s in self.stages]
```

### 3.3 Pipeline Runner 执行引擎

```python
# pipeline/runner.py

import logging
from .base import Pipeline, PipelineContext, StageStatus, StageResult

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Pipeline 执行引擎"""
    
    async def run(self, pipeline: Pipeline, ctx: PipelineContext) -> PipelineContext:
        """执行一条完整的 Pipeline"""
        ctx.metadata["pipeline"] = pipeline.name
        logger.info(f"[Pipeline:{pipeline.name}] 开始执行，creation_id={ctx.creation_id}")
        
        # Before pipeline hooks
        for hook in pipeline.hooks["before_pipeline"]:
            await hook(ctx)
        
        try:
            for i, stage in enumerate(pipeline.stages):
                logger.info(
                    f"[Pipeline:{pipeline.name}] "
                    f"Stage {i+1}/{len(pipeline.stages)}: {stage.name}"
                )
                
                # Before stage hooks
                for hook in pipeline.hooks["before_stage"]:
                    await hook(ctx, stage)
                
                # 更新进度
                await self._update_progress(ctx, i, len(pipeline.stages), stage.name)
                
                # 执行 Stage
                result = await stage.run(ctx)
                
                # After stage hooks
                for hook in pipeline.hooks["after_stage"]:
                    await hook(ctx, stage, result)
                
                # 如果 Stage 失败，终止 Pipeline
                if result.status == StageStatus.FAILED:
                    logger.error(
                        f"[Pipeline:{pipeline.name}] "
                        f"Stage {stage.name} 失败: {result.error}"
                    )
                    await self._update_status(ctx, "failed", result.error)
                    break
                
                logger.info(
                    f"[Pipeline:{pipeline.name}] "
                    f"Stage {stage.name} 完成 ({result.duration_ms}ms)"
                )
            
            else:
                # 所有 Stage 执行完毕
                await self._update_status(ctx, "completed")
                logger.info(f"[Pipeline:{pipeline.name}] 全部完成")
        
        except Exception as e:
            logger.exception(f"[Pipeline:{pipeline.name}] 异常终止: {e}")
            for hook in pipeline.hooks["on_error"]:
                await hook(ctx, e)
            await self._update_status(ctx, "failed", str(e))
        
        finally:
            # After pipeline hooks
            for hook in pipeline.hooks["after_pipeline"]:
                await hook(ctx)
        
        return ctx
    
    async def _update_progress(
        self, ctx: PipelineContext, 
        current: int, total: int, stage_name: str
    ):
        """更新创作任务进度（写入数据库 + WebSocket 推送）"""
        progress = int((current / total) * 100)
        # TODO: 写入数据库
        # await db.creations.update(ctx.creation_id, progress=progress, current_stage=stage_name)
        # TODO: WebSocket 推送给前端
        # await ws_manager.send(ctx.creation_id, {"progress": progress, "stage": stage_name})
    
    async def _update_status(
        self, ctx: PipelineContext, 
        status: str, error: str = None
    ):
        """更新创作任务状态"""
        # TODO: 写入数据库
        # await db.creations.update(ctx.creation_id, status=status, error=error)
        pass
```

### 3.4 Pipeline 注册表

```python
# pipeline/registry.py

from typing import Optional
from .base import Pipeline


class PipelineRegistry:
    """Pipeline 注册表 — 管理所有 Pipeline 定义"""
    
    _pipelines: dict[str, Pipeline] = {}
    
    @classmethod
    def register(cls, mode: str, pipeline: Pipeline):
        """注册 Pipeline"""
        cls._pipelines[mode] = pipeline
    
    @classmethod
    def get(cls, mode: str) -> Optional[Pipeline]:
        """根据模式获取 Pipeline"""
        return cls._pipelines.get(mode)
    
    @classmethod
    def list_all(cls) -> dict[str, Pipeline]:
        """列出所有已注册的 Pipeline"""
        return cls._pipelines.copy()
    
    @classmethod
    def modes(cls) -> list[str]:
        """列出所有支持的模式"""
        return list(cls._pipelines.keys())
```

---

## 四、具体 Pipeline 实现

### 4.1 Stage 实现示例

```python
# pipeline/stages/prompt_enhance.py

from ..base import Stage, PipelineContext, StageResult, StageStatus


class PromptEnhanceStage(Stage):
    """提示词优化 Stage"""
    
    name = "prompt_enhance"
    description = "使用 AI 优化用户提示词，扩写细节、翻译为英文"
    
    def __init__(self, auto_enhance: bool = True):
        self.auto_enhance = auto_enhance
    
    def should_skip(self, ctx: PipelineContext) -> bool:
        # 如果用户已手动优化过，跳过
        return ctx.request.get("skip_enhance", False)
    
    async def execute(self, ctx: PipelineContext) -> StageResult:
        original_prompt = ctx.prompt
        
        # 调用 LLM 优化提示词
        enhanced = await self._call_llm(original_prompt, ctx.mode)
        
        # 存入上下文供后续 Stage 使用
        ctx.set("original_prompt", original_prompt)
        ctx.set("enhanced_prompt", enhanced)
        
        return StageResult(
            status=StageStatus.SUCCESS,
            data={
                "original": original_prompt,
                "enhanced": enhanced,
            }
        )
    
    async def _call_llm(self, prompt: str, mode: str) -> str:
        """调用大模型优化提示词"""
        system_prompts = {
            "clip": "你是短视频创意专家，请优化以下提示词，使其更适合生成 15 秒沉浸式短片...",
            "image": "你是图片生成专家，请优化以下提示词，补充画面细节、光影、构图描述...",
            "longvideo": "你是长视频导演，请将以下提示词扩展为适合多分镜视频的详细描述...",
            "agent": "你是全能创作助手，请分析用户意图并优化提示词...",
        }
        # TODO: 调用实际 LLM API
        # response = await llm.chat(system=system_prompts.get(mode, ""), user=prompt)
        # return response.content
        return prompt  # placeholder
```

```python
# pipeline/stages/video_generate.py

from ..base import Stage, PipelineContext, StageResult, StageStatus


class VideoGenerateStage(Stage):
    """视频生成 Stage"""
    
    name = "video_generate"
    description = "调用视频生成 API 生成视频"
    
    async def execute(self, ctx: PipelineContext) -> StageResult:
        prompt = ctx.get("enhanced_prompt", ctx.prompt)
        model = ctx.model or "seedance_2.0_fast"
        ratio = ctx.aspect_ratio or "16:9"
        duration = ctx.request.get("duration", 10)
        reference_ids = ctx.request.get("referenceAssetIds", [])
        style_ref = ctx.request.get("styleReferenceId")
        
        # 调用视频生成 API
        result = await self._generate_video(
            prompt=prompt,
            model=model,
            ratio=ratio,
            duration=duration,
            reference_ids=reference_ids,
            style_ref=style_ref,
        )
        
        ctx.set("video_url", result["url"])
        ctx.set("video_id", result["id"])
        
        return StageResult(
            status=StageStatus.SUCCESS,
            data=result,
        )
    
    async def _generate_video(self, **kwargs) -> dict:
        """调用外部视频生成 API"""
        # TODO: 调用 Seedance API
        # response = await seedance_client.generate(**kwargs)
        # return {"id": response.id, "url": response.url}
        return {"id": "vid_xxx", "url": ""}  # placeholder
```

```python
# pipeline/stages/intent_parse.py

from ..base import Stage, PipelineContext, StageResult, StageStatus


class IntentParseStage(Stage):
    """意图识别 Stage（Agent 模式专用）"""
    
    name = "intent_parse"
    description = "分析用户输入，识别创作意图"
    
    async def execute(self, ctx: PipelineContext) -> StageResult:
        prompt = ctx.prompt
        
        # 调用 LLM 识别意图
        intent = await self._parse_intent(prompt)
        
        ctx.set("intent", intent["type"])           # image / video / script / composite
        ctx.set("intent_params", intent["params"])
        ctx.set("sub_tasks", intent.get("sub_tasks", []))
        
        return StageResult(
            status=StageStatus.SUCCESS,
            data=intent,
        )
    
    async def _parse_intent(self, prompt: str) -> dict:
        """调用 LLM 解析意图"""
        # TODO: 实际 LLM 调用
        # 返回格式：
        # {
        #   "type": "video",       # image / video / script / composite
        #   "params": { ... },
        #   "sub_tasks": [ ... ],  # 组合任务时的子任务列表
        #   "confidence": 0.95
        # }
        return {"type": "video", "params": {}, "confidence": 0.9}
```

### 4.2 Pipeline 编排定义

```python
# pipeline/pipelines/agent.py

from ..base import Pipeline
from ..registry import PipelineRegistry
from ..stages.intent_parse import IntentParseStage
from ..stages.prompt_enhance import PromptEnhanceStage
from ..stages.model_router import ModelRouterStage
from ..stages.video_generate import VideoGenerateStage
from ..stages.image_generate import ImageGenerateStage
from ..stages.post_process import PostProcessStage


def create_agent_pipeline() -> Pipeline:
    """Agent 模式 Pipeline"""
    pipeline = Pipeline()
    pipeline.name = "agent"
    pipeline.description = "全能创作 Agent Pipeline"
    
    pipeline.add_stages(
        IntentParseStage(),         # 1. 意图识别
        PromptEnhanceStage(),       # 2. 提示词优化
        ModelRouterStage(),         # 3. 模型路由（根据意图选择模型）
        # Stage 4 动态执行（由 ModelRouterStage 决定）
        PostProcessStage(),         # 5. 后处理
    )
    
    return pipeline


# 注册
PipelineRegistry.register("agent", create_agent_pipeline())
```

```python
# pipeline/pipelines/clip.py

from ..base import Pipeline
from ..registry import PipelineRegistry
from ..stages.asset_resolve import AssetResolveStage
from ..stages.prompt_enhance import PromptEnhanceStage
from ..stages.style_fusion import StyleFusionStage
from ..stages.video_generate import VideoGenerateStage
from ..stages.post_process import PostProcessStage


def create_clip_pipeline() -> Pipeline:
    """沉浸式短片 Pipeline"""
    pipeline = Pipeline()
    pipeline.name = "clip"
    pipeline.description = "沉浸式短片 Pipeline — Seedance 2.0"
    
    pipeline.add_stages(
        AssetResolveStage(),        # 1. 解析 @引用素材 + 上传素材
        PromptEnhanceStage(),       # 2. 提示词优化
        StyleFusionStage(),         # 3. 融合参考风格 + 比例参数
        VideoGenerateStage(),       # 4. 调用 Seedance 视频生成
        PostProcessStage(),         # 5. 后处理（字幕/配乐/转码）
    )
    
    return pipeline


PipelineRegistry.register("clip", create_clip_pipeline())
```

```python
# pipeline/pipelines/longvideo2.py

from ..base import Pipeline
from ..registry import PipelineRegistry
from ..stages.script_generate import ScriptGenerateStage
from ..stages.scene_split import SceneSplitStage
from ..stages.asset_match import AssetMatchStage
from ..stages.per_shot_generate import PerShotGenerateStage
from ..stages.audio_compose import AudioComposeStage
from ..stages.video_compose import VideoComposeStage


def create_longvideo2_pipeline() -> Pipeline:
    """智能长视频 2.0 Pipeline"""
    pipeline = Pipeline()
    pipeline.name = "longvideo2"
    pipeline.description = "智能长视频 2.0 — 多分镜自动编排"
    
    pipeline.add_stages(
        ScriptGenerateStage(),      # 1. LLM 生成完整脚本
        SceneSplitStage(),          # 2. 将脚本拆解为 N 个分镜
        AssetMatchStage(),          # 3. 为每个分镜匹配/生成素材
        PerShotGenerateStage(),     # 4. 并行生成每个镜头视频
        AudioComposeStage(),        # 5. TTS + 配乐 + 音效合成
        VideoComposeStage(),        # 6. 拼接所有片段 + 转场特效
    )
    
    return pipeline


PipelineRegistry.register("longvideo2", create_longvideo2_pipeline())
```

```python
# pipeline/pipelines/image.py

from ..base import Pipeline
from ..registry import PipelineRegistry
from ..stages.prompt_enhance import PromptEnhanceStage
from ..stages.params_assemble import ParamsAssembleStage
from ..stages.image_generate import ImageGenerateStage
from ..stages.post_process import PostProcessStage


def create_image_pipeline() -> Pipeline:
    """生成图片 Pipeline"""
    pipeline = Pipeline()
    pipeline.name = "image"
    pipeline.description = "生成图片 Pipeline — Seedream"
    
    pipeline.add_stages(
        PromptEnhanceStage(),       # 1. 提示词优化
        ParamsAssembleStage(),      # 2. 组装参数（比例+模型+风格）
        ImageGenerateStage(),       # 3. 调用 Seedream 图片生成
        PostProcessStage(),         # 4. 超分/格式转换
    )
    
    return pipeline


PipelineRegistry.register("image", create_image_pipeline())
```

---

## 五、API 入口设计

### 5.1 统一创作 API

```python
# api/v1/creations.py

from fastapi import APIRouter, BackgroundTasks
from pipeline.registry import PipelineRegistry
from pipeline.runner import PipelineRunner
from pipeline.base import PipelineContext
import uuid

router = APIRouter()


@router.post("/api/v1/creations")
async def create(request: CreationRequest, bg: BackgroundTasks):
    """统一创作入口"""
    
    # 1. 查找对应 Pipeline
    pipeline = PipelineRegistry.get(request.mode)
    if not pipeline:
        raise HTTPException(400, f"不支持的创作模式: {request.mode}")
    
    # 2. 创建任务记录
    creation_id = str(uuid.uuid4())
    creation = await db.creations.create({
        "id": creation_id,
        "mode": request.mode,
        "prompt": request.prompt,
        "status": "pending",
        "pipeline": pipeline.name,
        "stages": pipeline.get_stage_names(),
        "params": request.dict(),
    })
    
    # 3. 后台执行 Pipeline
    ctx = PipelineContext(creation_id, request.dict())
    runner = PipelineRunner()
    bg.add_task(runner.run, pipeline, ctx)
    
    # 4. 立即返回任务 ID
    return {
        "id": creation_id,
        "status": "pending",
        "pipeline": pipeline.name,
        "stages": pipeline.get_stage_names(),
    }


@router.get("/api/v1/creations/{creation_id}")
async def get_creation(creation_id: str):
    """查询创作状态和进度"""
    creation = await db.creations.get(creation_id)
    return {
        "id": creation.id,
        "status": creation.status,       # pending / running / completed / failed
        "progress": creation.progress,    # 0-100
        "current_stage": creation.current_stage,
        "stages": creation.stages,        # 所有 Stage 列表
        "result": creation.result,        # 完成后的结果
        "error": creation.error,          # 失败时的错误信息
    }


@router.get("/api/v1/creations/{creation_id}/stages")
async def get_stages(creation_id: str):
    """查询各 Stage 执行详情"""
    creation = await db.creations.get(creation_id)
    return {
        "stages": [
            {
                "name": name,
                "status": result.status,
                "duration_ms": result.duration_ms,
                "data": result.data,
            }
            for name, result in creation.stage_results.items()
        ]
    }
```

### 5.2 WebSocket 进度推送

```python
# api/v1/ws.py

from fastapi import WebSocket

@router.websocket("/ws/creations/{creation_id}")
async def creation_progress(ws: WebSocket, creation_id: str):
    """WebSocket 实时推送 Pipeline 执行进度"""
    await ws.accept()
    
    try:
        # 订阅该 creation_id 的进度更新
        async for event in progress_channel.subscribe(creation_id):
            await ws.send_json({
                "type": "progress",
                "data": {
                    "stage": event.stage_name,
                    "progress": event.progress,
                    "status": event.status,
                    "message": event.message,
                }
            })
            
            if event.status in ("completed", "failed"):
                break
    finally:
        await ws.close()
```

---

## 六、Pipeline 执行流程图

```
                     用户点击「发送」
                          │
                          ▼
              ┌──── POST /api/v1/creations ────┐
              │                                │
              │  1. 根据 mode 查找 Pipeline     │
              │  2. 创建 Creation 记录          │
              │  3. 返回 creation_id            │
              │  4. 后台启动 PipelineRunner     │
              └───────────┬────────────────────┘
                          │
        前端拿到 id ───────┤──────── 后台异步执行
              │           │               │
              ▼           │               ▼
     跳转结果页面          │      PipelineRunner.run()
              │           │         │
              ▼           │         ▼
     WS 连接进度推送       │    Stage1.run(ctx)
     /ws/creations/:id    │         │ ✓
              │           │         ▼
              │           │    Stage2.run(ctx)
     实时显示：            │         │ ✓
     ┌──────────────┐    │         ▼
     │ ⏳ 优化提示词  │    │    Stage3.run(ctx)
     │ ✅ 素材解析   │    │         │ ✓
     │ 🔄 视频生成中 │    │         ▼
     │ ⬜ 后处理     │    │    Stage4.run(ctx)
     └──────────────┘    │         │ ✓
              │           │         ▼
              ▼           │    Pipeline 完成
     显示最终结果 ◄────────┘    更新 DB 状态
```

---

## 七、Pipeline 的扩展能力

### 7.1 新增模式

只需 3 步：

```python
# 1. 实现新 Stage（如有新需求）
class NewStage(Stage):
    name = "new_stage"
    async def execute(self, ctx): ...

# 2. 编排 Pipeline
def create_new_pipeline():
    pipeline = Pipeline()
    pipeline.name = "new_mode"
    pipeline.add_stages(
        PromptEnhanceStage(),   # 复用已有 Stage
        NewStage(),             # 新 Stage
        PostProcessStage(),     # 复用
    )
    return pipeline

# 3. 注册
PipelineRegistry.register("new_mode", create_new_pipeline())
```

### 7.2 Stage 复用率

| Stage | Agent | Clip | LV2.0 | Image | LV |
|-------|-------|------|-------|-------|----|
| PromptEnhance | ✅ | ✅ | — | ✅ | — |
| AssetResolve | — | ✅ | — | — | — |
| IntentParse | ✅ | — | — | — | — |
| ModelRouter | ✅ | — | — | — | — |
| StyleFusion | — | ✅ | — | — | — |
| ScriptGenerate | — | — | ✅ | — | ✅ |
| SceneSplit | — | — | ✅ | — | ✅ |
| VideoGenerate | ✅ | ✅ | — | — | — |
| ImageGenerate | ✅ | — | — | ✅ | — |
| PerShotGenerate | — | — | ✅ | — | ✅ |
| AudioCompose | — | — | ✅ | — | ✅ |
| VideoCompose | — | — | ✅ | — | ✅ |
| PostProcess | ✅ | ✅ | ✅ | ✅ | ✅ |

> **PostProcess** 是唯一在所有 Pipeline 中都复用的 Stage

### 7.3 条件分支

```python
class ConditionalStage(Stage):
    """条件 Stage — 根据上下文动态选择执行路径"""
    
    name = "conditional"
    
    def __init__(self, condition_fn, true_stage: Stage, false_stage: Stage):
        self.condition_fn = condition_fn
        self.true_stage = true_stage
        self.false_stage = false_stage
    
    async def execute(self, ctx: PipelineContext) -> StageResult:
        if self.condition_fn(ctx):
            return await self.true_stage.run(ctx)
        else:
            return await self.false_stage.run(ctx)

# 使用：
pipeline.add_stage(
    ConditionalStage(
        condition_fn=lambda ctx: ctx.get("intent") == "image",
        true_stage=ImageGenerateStage(),
        false_stage=VideoGenerateStage(),
    )
)
```

### 7.4 并行执行

```python
class ParallelStage(Stage):
    """并行 Stage — 同时执行多个子 Stage"""
    
    name = "parallel"
    
    def __init__(self, stages: list[Stage]):
        self.sub_stages = stages
    
    async def execute(self, ctx: PipelineContext) -> StageResult:
        import asyncio
        tasks = [stage.run(ctx) for stage in self.sub_stages]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 检查是否有失败
        for r in results:
            if isinstance(r, Exception):
                return StageResult(status=StageStatus.FAILED, error=str(r))
        
        return StageResult(
            status=StageStatus.SUCCESS,
            data={"sub_results": [r.data for r in results]},
        )

# 使用（长视频逐镜并行生成）：
pipeline.add_stage(
    ParallelStage([
        VideoGenerateStage(scene_index=i) for i in range(scene_count)
    ])
)
```

---

## 八、数据模型

```python
# models/creation.py

from sqlalchemy import Column, String, JSON, Integer, DateTime, Enum
from datetime import datetime


class Creation(Base):
    __tablename__ = "creations"
    
    id = Column(String(36), primary_key=True)
    mode = Column(String(20), nullable=False)          # agent / clip / ...
    prompt = Column(String(5000), nullable=False)
    status = Column(String(20), default="pending")     # pending/running/completed/failed
    pipeline = Column(String(50))                      # Pipeline 名称
    
    # 参数
    params = Column(JSON)                              # 完整请求参数
    
    # 执行进度
    progress = Column(Integer, default=0)              # 0-100
    current_stage = Column(String(50))                 # 当前执行的 Stage
    stage_results = Column(JSON, default=dict)         # 各 Stage 结果
    
    # 结果
    result = Column(JSON)                              # 最终输出
    error = Column(String(2000))                       # 错误信息
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 关联
    user_id = Column(String(36))
    project_id = Column(String(36))
```

---

## 九、总结

| 维度 | 设计方案 |
|------|---------|
| **架构模式** | Pipeline 编排 — 线性 Stage 顺序执行 |
| **核心组件** | Pipeline + Stage + Context + Runner + Registry |
| **5 条 Pipeline** | Agent / Clip / LongVideo2 / Image / LongVideo |
| **13 个可复用 Stage** | 意图识别、提示词优化、模型路由、素材解析、风格融合、脚本生成、分镜拆解、逐镜生成、图片生成、视频生成、音频合成、视频合成、后处理 |
| **扩展能力** | 新增模式仅需 3 步、支持条件分支、支持并行执行 |
| **进度推送** | WebSocket 实时推送各 Stage 执行状态 |
| **执行方式** | FastAPI BackgroundTasks 后台异步执行 |
