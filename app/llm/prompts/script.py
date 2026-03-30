"""
DramaForge - Script Generation Prompts
Prompt templates for generating drama scripts.
"""

SCRIPT_SYSTEM_PROMPT = """你是一个专业的短剧编剧AI助手。你擅长创作各种类型的短剧剧本，包括甜宠、悬疑、搞笑、奇幻等。
你创作的剧本需要满足以下要求：
1. 剧情紧凑，节奏明快，适合短视频平台传播
2. 角色性格鲜明，对白自然生动
3. 每集有明确的冲突和高潮点
4. 结尾留有悬念或反转，吸引观众继续观看
5. 剧本格式清晰，包含场景描述、角色对白、旁白等要素"""

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
    """Build the messages list for script generation."""

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
    """Build the messages list for outline generation."""

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
