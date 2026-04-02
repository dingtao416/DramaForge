"""
DramaForge - Script Generation Prompts
Prompt templates for generating drama scripts.
"""

# ═════════════════════════════════════════════════════════════════════
# v1.0 Free Form Prompts
# ═════════════════════════════════════════════════════════════════════

SCRIPT_SYSTEM_PROMPT = """你是一个专业的短剧编剧AI助手。你擅长创作各种类型的短剧剧本，包括甜宠、悬疑、搞笑、奇幻等。
你创作的剧本需要满足以下要求：
1. 剧情紧凑，节奏明快，适合短视频平台传播
2. 角色性格鲜明，对白自然生动
3. 每集有明确的冲突和高潮点
4. 结尾留有悬念或反转，吸引观众继续观看
5. 剧本格式清晰，包含场景描述、角色对白、旁白等要素"""


# ═════════════════════════════════════════════════════════════════════
# v2.0 Structured JSON Prompts
# ═════════════════════════════════════════════════════════════════════

SCRIPT_STRUCTURED_SYSTEM = """你是 DramaForge 的短剧编剧 AI。你的输出必须是严格的 JSON 格式。
所有内容使用中文。所有字段必须填写。不要输出 JSON 以外的任何文字。"""

SCRIPT_STRUCTURED_PROMPT = """根据用户的创意构想，创作一部完整的短剧剧本。

【用户构想】
{user_input}

【要求】
- 类型：{genre}
- 集数：{total_episodes} 集
- 每集时长：约 {duration} 秒
- 风格：{style}

请严格按照以下 JSON 格式输出：

{{
  "protagonist": "主角名字",
  "genre": "剧种类型",
  "synopsis": "整体故事梗概（200字以内）",
  "background": "故事背景设定",
  "setting": "主要场景环境",
  "one_liner": "一句话概括（30字以内）",
  "characters": [
    {{
      "name": "角色名",
      "role": "protagonist/antagonist/supporting",
      "description": "角色简介（外貌、性格、背景）"
    }}
  ],
  "scenes": [
    {{
      "name": "场景名称",
      "description": "场景描述",
      "time_of_day": "day/night/dawn/dusk",
      "interior": true
    }}
  ],
  "episodes": [
    {{
      "number": 1,
      "title": "本集标题",
      "content": "完整的本集剧本内容，包含场景描述、对白、旁白、动作指示等"
    }}
  ]
}}

确保：
1. characters 至少包含 2 个角色
2. scenes 至少包含 2 个场景
3. episodes 数量等于要求的集数
4. 每集 content 内容丰富，至少 500 字"""


NARRATION_REWRITE_PROMPT = """将以下对话型剧本改写为旁白叙述型。

要求：
1. 去除所有角色直接对话，改为第三人称旁白叙述
2. 保留核心剧情和情节推进
3. 增加画面描写和氛围渲染
4. 适合用于 AI 语音旁白配音
5. 输出纯文本，不需要 JSON

【原始剧本】
{script_content}

【改写后的旁白剧本】"""


# ═════════════════════════════════════════════════════════════════════
# v1.0 Legacy Prompts (backward compatibility)
# ═════════════════════════════════════════════════════════════════════

SCRIPT_GENERATION_PROMPT = """请根据以下信息创作一个短剧剧本：

【剧种类型】{genre}
【主题/关键词】{topic}
【目标时长】约{duration}秒
【集数】第{episode}集（共{total_episodes}集）
{outline_section}
{characters_section}
{style_section}

请按照以下格式输出剧本：

---
## 标题：[本集标题]

### 角色表
- [角色名]：[简要角色描述]

### 剧本正文

**场景1：[场景名称/地点]**
[场景环境描述]

（旁白）[旁白内容]

[角色名]：[对白内容]（[表情/动作描述]）

[角色名]：[对白内容]

（旁白）[旁白内容]

**场景2：[场景名称/地点]**
...

### 本集结尾悬念
[结尾悬念或反转说明]
---

请确保剧本内容丰富、引人入胜，对白自然流畅。"""


SCRIPT_OUTLINE_PROMPT = """请根据以下信息为一部短剧生成大纲：

【剧种类型】{genre}
【主题/关键词】{topic}
【总集数】{total_episodes}集
【每集时长】约{duration}秒

请以JSON格式输出，结构如下：
{{
    "title": "剧名",
    "synopsis": "整体剧情概要（100字以内）",
    "characters": [
        {{
            "name": "角色名",
            "description": "角色描述",
            "appearance": "外貌描述（用于AI绘图，需详细描述发型、服饰、体型等特征）"
        }}
    ],
    "episodes": [
        {{
            "episode": 1,
            "title": "本集标题",
            "summary": "本集剧情概要",
            "key_scenes": ["关键场景1", "关键场景2"],
            "cliffhanger": "结尾悬念"
        }}
    ]
}}"""


def build_script_prompt(
    genre: str,
    topic: str,
    duration: int = 60,
    episode: int = 1,
    total_episodes: int = 1,
    outline: str = "",
    characters: list[dict] = None,
    style: str = "",
) -> list[dict[str, str]]:
    """Build the messages list for script generation (v1 legacy)."""

    outline_section = f"【大纲】\n{outline}" if outline else ""
    characters_section = ""
    if characters:
        chars = "\n".join(
            [f"- {c['name']}：{c.get('description', '')}（外貌：{c.get('appearance', '')}）"
             for c in characters]
        )
        characters_section = f"【角色设定】\n{chars}"

    style_section = f"【画面风格】{style}" if style else ""

    user_content = SCRIPT_GENERATION_PROMPT.format(
        genre=genre,
        topic=topic,
        duration=duration,
        episode=episode,
        total_episodes=total_episodes,
        outline_section=outline_section,
        characters_section=characters_section,
        style_section=style_section,
    )

    return [
        {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def build_outline_prompt(
    genre: str,
    topic: str,
    total_episodes: int = 1,
    duration: int = 60,
) -> list[dict[str, str]]:
    """Build the messages list for outline generation (v1 legacy)."""

    user_content = SCRIPT_OUTLINE_PROMPT.format(
        genre=genre,
        topic=topic,
        total_episodes=total_episodes,
        duration=duration,
    )

    return [
        {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def build_structured_prompt(
    user_input: str,
    genre: str = "其他",
    total_episodes: int = 1,
    duration: int = 60,
    style: str = "写实",
) -> list[dict[str, str]]:
    """Build the messages list for v2.0 structured JSON script generation."""

    user_content = SCRIPT_STRUCTURED_PROMPT.format(
        user_input=user_input,
        genre=genre,
        total_episodes=total_episodes,
        duration=duration,
        style=style,
    )

    return [
        {"role": "system", "content": SCRIPT_STRUCTURED_SYSTEM},
        {"role": "user", "content": user_content},
    ]
