# DramaForge — 老张 API 模型清单与推荐方案
> 数据来源：https://api.laozhang.ai/account/pricing
> 更新时间：2026-04-03

---

## 一、概览

| 类型 | 总数 | 平台数 |
|------|------|--------|
| Chat (文本/多模态) | 367+ | OpenAI / Anthropic / Google / 阿里 / DeepSeek / 智谱 / Moonshot / xAI |
| 视频生成 | 311+ | Kling / Hailuo / VEO / Vidu / Wan / Sora / SeeDance / Runway |
| 图片生成 | 102+ | Ideogram / Midjourney / gpt-image-1 系列 |

---

## 二、视频生成平台详情

### 1. Kling 可灵 — 47 项
- 按 `模型版本 + 模式(std/pro) + 时长 + 音频` 计费
- 版本：kling-v1, kling-v1.5, kling-v1.6, kling-v2.0, kling-v2.1
- 模式：standard / professional
- 时长：5s / 10s
- 音频：可选音频生成

### 2. Hailuo 海螺 (MiniMax) — 20 项
- 按 `模型版本 + 分辨率 + 时长` 计费
- 版本：hailuo-01, hailuo-01-director
- 分辨率：720p / 1080p
- 时长：5s / 10s

### 3. VEO (Google Vertex AI) — 32 项
- 按秒计费：`模型版本 + 分辨率 + 音频`
- 版本：veo-2.0, veo-3.0, veo-3.1-fast
- 分辨率：720p / 1080p
- 默认 8 秒视频

### 4. Vidu — 155 项
- 按 `模型版本 + 分辨率 + 时长` 计费（积分制）
- 版本：vidu-2.0, vidu-2.5
- 分辨率：720p / 1080p
- 时长：4s / 8s

### 5. Wan 万象 (阿里) — 12 项
- 按秒计费：`模型版本 + 类型`
- 版本：wan-v2.1
- 类型：t2v (文生视频) / i2v (图生视频)

### 6. Sora (OpenAI) — 3 项
- 按秒计费
- 版本：sora-720p / sora-1080p / sora-pro
- 分辨率：720p / 1080p

### 7. SeeDance 火山引擎 — 32 项
- 按 `模型 + 宽高比 + 分辨率 + 时长` 计费（元）
- 版本：seedance-1.0, seedance-2.0
- 宽高比：1:1 / 9:16 / 16:9
- 时长：5s / 10s

### 8. Runway — 12 项
- 按 `动作类型 + 模型版本 + 时长` 计费
- 版本：gen-3, gen-4
- 类型：t2v / i2v

---

## 三、图片生成平台详情

### 1. Ideogram — 17 项
- 按 `模型版本` 计费
- 版本：ideogram-v2, ideogram-v3

### 2. Midjourney — 85 项
- 按 `操作类型` 计费
- 操作：imagine / upscale / variation / blend / describe

### 3. GPT Image — OpenAI 原生
- gpt-image-1：$5 输入 / $32 输出 per 1M tokens
- gpt-image-1-mini：$2 输入 / $8 输出 per 1M tokens
- gpt-image-1.5：$5 输入 / $32 输出 per 1M tokens

---

## 四、Chat 模型精选

| 模型 | 提示价格 | 补全价格 | 备注 |
|------|----------|----------|------|
| gpt-4o | $2.50/1M | $10.00/1M | OpenAI 主力 |
| gpt-5-chat | $1.25/1M | $10.00/1M | 最新 GPT-5 |
| gpt-4.1 | $2.00/1M | $8.00/1M | 高性价比 |
| gpt-4.1-mini | $0.40/1M | $1.60/1M | 轻量快速 |
| claude-sonnet-4 | $3.00/1M | $15.00/1M | Anthropic 主力 |
| claude-haiku-4-5 | $1.00/1M | $5.00/1M | 快速轻量 |
| gemini-3-flash-preview | $0.44/1M | $2.64/1M | Google 快速 |
| gemini-3-pro-preview | $1.80/1M | $10.80/1M | Google 高质量 |
| qwen-max | $1.60/1M | $6.40/1M | 阿里主力 |
| qwen3-235b-a22b | $1.00/1M | $10.00/1M | 阿里最强 |
| deepseek-v3.1 | $0.50/1M | $1.50/1M | 高性价比 |
| kimi-k2 | $0.56/1M | $2.24/1M | 性价比优秀 |
| glm-4.5-flash | $0.01/1M | $0.04/1M | **极低价格** |

---

## 五、DramaForge 推荐模型方案

### ⭐ Chat/Agent 对话（剧本创作 & 对话助手）

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| **默认对话** | `gpt-4.1-mini` | $0.40/M，快速且够用 |
| **剧本创作** | `gpt-4o` | 创意能力强，多模态理解 |
| **深度编剧** | `claude-sonnet-4` | 长文本输出质量最佳 |
| **极速回复** | `glm-4.5-flash` | $0.01/M，接近免费 |
| **高性价比** | `deepseek-v3.1` | 中文理解好，价格低 |

### 🎬 视频生成

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| **默认视频** | `seedance-2.0 · 9:16 · 720p · 5s` | 火山引擎，元计费，高性价比 |
| **高质量视频** | `kling-v2.1 · pro · 10s` | 可灵最新版，效果最佳 |
| **快速出片** | `veo-3.1-fast · 720p` | Google VEO 快速版 |
| **图生视频** | `wan-v2.1-i2v` | 阿里万象，图生视频 |

### 🖼️ 图片生成

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| **默认图片** | `gpt-image-1-mini` | OpenAI 原生，质量好 |
| **高质量图片** | `midjourney-imagine` | 艺术质量最高 |
| **设计海报** | `ideogram-v3` | 文字渲染能力强 |

---

## 六、API 调用说明

- **Base URL**: `https://api.laozhang.ai/v1`
- **鉴权方式**: `Authorization: Bearer <API_KEY>`
- **兼容 OpenAI SDK**：所有 Chat 模型可直接使用 OpenAI Python SDK
- **视频/图片模型**：通过异步任务 API 调用
