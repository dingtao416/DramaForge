# 🔥 DramaForge - AI Short Drama Engine

AI驱动的短剧自动化生产平台。用AI锻造短剧，从剧本创作到视频合成，一站式短剧制作。

## ✨ 功能特性

- 🤖 **多模型支持**：OpenAI GPT / Claude / DeepSeek / 通义千问 / 智谱 等 LLM 可配置切换
- 📝 **AI 剧本生成**：自动生成大纲、角色设定、分集剧本
- 🎨 **智能分镜**：AI 将剧本拆解为分镜画面，自动生成图片提示词
- 🖼️ **多源图片生成**：支持 DALL-E 3 / ComfyUI / Stable Diffusion WebUI
- 🔊 **TTS 配音**：Edge TTS（免费）/ Azure TTS / Fish Audio 多声色配音
- 🎬 **自动合成视频**：图片 + 音频 + 字幕 + 转场效果自动合成
- 👨‍💻 **人工审核环节**：剧本和分镜生成后支持人工审核、编辑后再继续

## 📋 工作流程

```
创意输入 → AI生成大纲 → AI生成剧本 → 人工审核
    → AI拆解分镜 → 人工审核 → AI生成图片
    → AI配音 → 自动合成视频 → 完成 🎉
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd D:/pycode/dramaforge

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

```bash
# 复制配置文件
copy .env.example .env

# 编辑 .env 文件，填入你的 API Key
```

### 3. 启动服务

```bash
python main.py
```

服务启动后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 📡 API 接口

### 项目管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/projects/` | 创建项目 |
| GET | `/api/projects/` | 项目列表 |
| GET | `/api/projects/{id}` | 项目详情 |
| PUT | `/api/projects/{id}` | 更新项目 |
| DELETE | `/api/projects/{id}` | 删除项目 |

### 生产流水线

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/pipeline/outline` | 生成大纲 |
| POST | `/api/pipeline/script` | 生成剧本 |
| POST | `/api/pipeline/storyboards` | 生成分镜 |
| POST | `/api/pipeline/storyboards/approve` | 审核分镜 |
| POST | `/api/pipeline/generate-images` | 生成图片 |
| POST | `/api/pipeline/generate-audio` | 生成配音 |
| POST | `/api/pipeline/compose-video` | 合成视频 |

## 🏗️ 项目结构

```
dramaforge/
├── main.py                     # 启动入口
├── requirements.txt            # Python 依赖
├── .env.example                # 配置模板
├── config/
│   └── __init__.py             # 全局配置 (Settings)
├── app/
│   ├── main.py                 # FastAPI 应用
│   ├── api/
│   │   ├── projects.py         # 项目管理 API
│   │   └── pipeline.py         # 流水线 API
│   ├── models/
│   │   └── database.py         # 数据库模型
│   ├── agents/
│   │   ├── base_agent.py       # Agent 基类
│   │   ├── script_agent.py     # 剧本生成 Agent
│   │   ├── storyboard_agent.py # 分镜拆解 Agent
│   │   ├── image_agent.py      # 图片生成 Agent
│   │   ├── tts_agent.py        # 配音 Agent
│   │   └── video_agent.py      # 视频合成 Agent
│   ├── llm/
│   │   ├── provider.py         # LLM 统一接口
│   │   └── prompts/            # Prompt 模板
│   │       ├── script.py
│   │       └── storyboard.py
│   └── pipeline/
│       └── orchestrator.py     # 流水线编排器
├── storage/                    # 生成的资产
│   ├── images/
│   ├── audio/
│   └── videos/
└── tests/
```

## 🔧 技术栈

- **后端框架**：FastAPI + Uvicorn
- **数据库**：SQLAlchemy + SQLite (可切换 PostgreSQL)
- **LLM**：LiteLLM (多模型统一接口)
- **图片生成**：DALL-E 3 / ComfyUI / SD WebUI
- **TTS**：Edge TTS / Azure TTS
- **视频合成**：MoviePy + FFmpeg
- **日志**：Loguru

## 📝 使用示例

### 1. 创建一个甜宠短剧项目

```bash
curl -X POST http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "霸道总裁爱上我",
    "description": "平凡女孩误入豪门，与霸道总裁展开一段甜蜜爱情故事",
    "genre": "romance",
    "target_duration": 60,
    "target_episodes": 5,
    "style_prompt": "anime style, romantic, soft lighting, pastel colors"
  }'
```

### 2. 生成大纲

```bash
curl -X POST http://localhost:8000/api/pipeline/outline \
  -H "Content-Type: application/json" \
  -d '{"project_id": 1}'
```

### 3. 生成剧本 → 审核 → 生成分镜 → 审核 → 生成资产 → 合成视频

按照流水线 API 依次调用即可。

## 📄 License

MIT License
