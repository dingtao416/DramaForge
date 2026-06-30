# DramaForge

<p align="center">
  <a href="#中文">中文</a> |
  <a href="#english">English</a>
</p>

<p align="center">
  <img alt="Backend" src="https://img.shields.io/badge/backend-FastAPI-009688">
  <img alt="Frontend" src="https://img.shields.io/badge/frontend-Vue%203-42b883">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11-blue">
  <img alt="Node" src="https://img.shields.io/badge/node-20-green">
  <img alt="Status" src="https://img.shields.io/badge/status-active%20development-orange">
</p>

<a id="中文"></a>

## 中文

DramaForge 是一个开源的 AI 短剧生产系统，面向短剧、漫剧、网文 IP、剧情化营销和私有化 AI 视频生产场景。

它不是泛用视频生成器，而是围绕连续故事生产设计的工作台：从故事 Bible 到角色/场景资产，再到可编辑分镜源码和多模型成片。

### 核心工作流

```text
Story Bible -> 角色/场景资产 -> 分镜源码 -> 多模型成片
```

当前产品保留泛 Agent 首页和通用聊天，作为登录后的工作入口和创意入口；短剧生产链路是核心差异化能力。

### 功能特性

- 登录和用户隔离，支持团队或企业接入时的账号边界。
- 泛 Agent 首页和通用聊天，用于创意探索、项目入口和快速问答。
- 项目工作台，管理短剧项目、剧本、资产、分镜和生成状态。
- 剧本上传与 AI 生成，支持从故事构想或剧本文档进入生产链路。
- Story Bible 设计，用于维护世界观、人物关系、时间线、视觉规则和连续性约束。
- 角色/场景资产库，将角色和场景作为可复用生产资产管理。
- 分镜源码编辑，支持镜头时长、场景、角色、台词、旁白、景别、角度、运镜和提示词编辑。
- 多模型配置与生成，按 chat、image、video、tts 等能力接入不同模型。
- 单镜头生成、单片段生成、片段重试、单集合成和项目导出。
- 积分、计费和支付后端能力保留，便于企业私有化和二次开发。

### 不再作为核心方向

以下功能不再作为当前产品设计重点：

- 沉浸式短片独立模式。
- 智能长视频 / 智能长视频 2.0 独立模式。
- 爆款复刻。
- 一镜到底。
- 消费级会员订阅展示和充值弹窗。
- 以泛视频生成为中心的多 Pipeline 规划。

### 技术栈

| Layer | Stack |
| --- | --- |
| Frontend | Vue 3, TypeScript, Vite, Pinia, Tailwind CSS, Naive UI |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic, ARQ |
| Queue / Cache | Redis |
| Storage | Local storage by default, designed for OSS/MinIO style extension |
| Media | FFmpeg, Pillow |
| AI Hub | OpenAI-compatible providers, laozhang.ai relay, configurable model providers |

### 项目结构

```text
DramaForge/
├── dramaForge_bac/      # Backend service, FastAPI API, engines, tasks, storage
├── dramaForge_web/      # Frontend app, Vue 3 + TypeScript + Vite
├── docs/                # Product and technical documentation
├── storage/             # Local generated assets and runtime files
├── docker-compose.yml   # Docker deployment entry
└── .env.example         # Environment variable template
```

### 快速开始

#### 方式一：Docker Compose

```powershell
Copy-Item .env.example .env
# Edit .env and set LAOZHANG_API_KEY, JWT_SECRET_KEY, SECRET_KEY, SMTP settings if needed.
docker compose up --build
```

默认访问地址：

- Frontend: `http://localhost:3001`
- Backend API docs: `http://localhost:8001/api/docs`
- Health check: `http://localhost:8001/api/health`

#### 方式二：原生启动

准备 Redis，并确保 `.env` 中的 `REDIS_URL` 可访问。

Backend:

```powershell
cd dramaForge_bac
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd dramaForge_web
npm install
npm run dev
```

默认开发地址：

- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/api/docs`

### 关键环境变量

复制 `.env.example` 为 `.env` 后至少配置：

```env
LAOZHANG_API_KEY=your-api-key-here
LAOZHANG_BASE_URL=https://api.laozhang.ai/v1
DATABASE_URL=sqlite+aiosqlite:///./storage/dramaforge.db
REDIS_URL=redis://127.0.0.1:6379/0
JWT_SECRET_KEY=change-this-to-a-random-string
SECRET_KEY=change-this-to-a-random-string
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

邮箱验证码登录需要额外配置 SMTP 变量。详见 `.env.example`。

### 文档

- [功能设计](docs/FEATURES.md)
- [后端架构](docs/BACKEND_ARCHITECTURE.md)
- [模型清单](docs/MODELS.md)
- [原生部署指南](docs/NATIVE_DEPLOYMENT.md)

### 路线图

- P0: ✅ Story Bible 数据模型、首页入口收敛、短剧主链路设计和 5 集样片验证（进行中）。
- P1: 角色三视图、阶段形象、场景状态资产和分镜源码体验强化。
- P2: 企业接入配置、模型成本统计、私有化部署、批量生成和批量重试。

### 许可证

当前仓库尚未包含正式 `LICENSE` 文件。公开发布前请补充明确的开源许可证。

[Back to top](#dramaforge)

<a id="english"></a>

## English

DramaForge is an open-source AI short-drama production system for short dramas, animated drama workflows, web-novel IP adaptation, story-driven marketing, and private AI video production.

It is not a generic video generator. DramaForge is designed around continuous story production: from a Story Bible to reusable character and scene assets, editable storyboard source, and multi-model video generation.

### Core Workflow

```text
Story Bible -> Character / Scene Assets -> Storyboard Source -> Multi-model Video Output
```

The general Agent home page and chat experience remain part of the product. They serve as the post-login workspace and creative entry point, while the short-drama production workflow is the core differentiator.

### Features

- Authentication and user isolation for team and enterprise integration.
- General Agent home page and chat for ideation, project entry, and quick assistance.
- Project workbench for managing scripts, assets, storyboards, and generation states.
- Script upload and AI script generation from either a story idea or a screenplay file.
- Story Bible design for world rules, relationships, timelines, visual rules, and continuity constraints.
- Character and scene asset library for reusable production assets.
- Editable storyboard source, including shot duration, scene references, character references, dialogue, narration, camera language, and prompts.
- Multi-model configuration and generation across chat, image, video, and TTS capabilities.
- Shot generation, segment generation, retry, episode composition, and project export.
- Credits, billing, and payment backend capabilities retained for enterprise integration and secondary development.

### No Longer Core

The following features are no longer part of the current core product direction:

- Standalone immersive short-clip mode.
- Standalone long-video and long-video 2.0 modes.
- Viral video cloning.
- One-shot transition video generation.
- Consumer subscription pages and credit top-up modals.
- Generic multi-pipeline video-generation planning.

### Tech Stack

| Layer | Stack |
| --- | --- |
| Frontend | Vue 3, TypeScript, Vite, Pinia, Tailwind CSS, Naive UI |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic, ARQ |
| Queue / Cache | Redis |
| Storage | Local storage by default, designed for OSS/MinIO style extension |
| Media | FFmpeg, Pillow |
| AI Hub | OpenAI-compatible providers, laozhang.ai relay, configurable model providers |

### Repository Structure

```text
DramaForge/
├── dramaForge_bac/      # Backend service, FastAPI API, engines, tasks, storage
├── dramaForge_web/      # Frontend app, Vue 3 + TypeScript + Vite
├── docs/                # Product and technical documentation
├── storage/             # Local generated assets and runtime files
├── docker-compose.yml   # Docker deployment entry
└── .env.example         # Environment variable template
```

### Quick Start

#### Option 1: Docker Compose

```powershell
Copy-Item .env.example .env
# Edit .env and set LAOZHANG_API_KEY, JWT_SECRET_KEY, SECRET_KEY, SMTP settings if needed.
docker compose up --build
```

Default URLs:

- Frontend: `http://localhost:3001`
- Backend API docs: `http://localhost:8001/api/docs`
- Health check: `http://localhost:8001/api/health`

#### Option 2: Native Development

Start Redis first, and make sure `REDIS_URL` in `.env` is reachable.

Backend:

```powershell
cd dramaForge_bac
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd dramaForge_web
npm install
npm run dev
```

Default development URLs:

- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/api/docs`

### Key Environment Variables

Copy `.env.example` to `.env` and configure at least:

```env
LAOZHANG_API_KEY=your-api-key-here
LAOZHANG_BASE_URL=https://api.laozhang.ai/v1
DATABASE_URL=sqlite+aiosqlite:///./storage/dramaforge.db
REDIS_URL=redis://127.0.0.1:6379/0
JWT_SECRET_KEY=change-this-to-a-random-string
SECRET_KEY=change-this-to-a-random-string
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

Email-code login requires SMTP settings. See `.env.example` for details.

### Documentation

- [Feature Design](docs/FEATURES.md)
- [Backend Architecture](docs/BACKEND_ARCHITECTURE.md)
- [Model Catalog](docs/MODELS.md)
- [Native Deployment Guide](docs/NATIVE_DEPLOYMENT.md)

### Roadmap

- P0: ✅ Story Bible data model, home-entry consolidation, short-drama workflow design, and 5-episode demo validation (in progress).
- P1: Character turnarounds, staged appearances, scene-state assets, and stronger storyboard-source editing.
- P2: Enterprise integration settings, model cost tracking, private deployment docs, batch generation, and batch retry.

### License

This repository does not currently include a formal `LICENSE` file. Add an explicit open-source license before public release.

[Back to top](#dramaforge)
