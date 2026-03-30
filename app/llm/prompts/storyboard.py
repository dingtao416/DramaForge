"""
DramaForge - Storyboard Generation Prompts
Prompt templates for splitting scripts into storyboard panels.
"""

STORYBOARD_SYSTEM_PROMPT = """你是一个专业的短剧分镜师AI助手。你擅长将剧本拆解为适合AI图片生成的分镜画面。
你需要确保：
1. 每个分镜的画面描述详细、具体，适合AI绘图
2. 保持角色外貌描述的一致性
3. 分镜节奏合理，旁白/对白时长与画面匹配
4. 转场效果自然流畅
5. 输出格式为严格的JSON"""

STORYBOARD_GENERATION_PROMPT = """请将以下剧本拆解为分镜列表。

【剧本内容】
{script_content}

【画面风格】{style_prompt}

【角色外貌设定】
{characters_appearance}

请以JSON格式输出，每个分镜包含以下字段：
{{
    "storyboards": [
        {{
            "sequence": 1,
            "scene_description": "场景描述（中文，供人阅读）",
            "image_prompt": "英文图片生成提示词，需包含画面风格、角色外貌、场景细节、光线氛围等。格式：[style], [scene description], [character description], [lighting/mood], [camera angle]",
            "narration": "旁白文本（如果有）",
            "dialogue": "对白文本（如果有），格式：角色名：对白内容",
            "duration": 5.0,
            "transition": "crossfade"
        }}
    ]
}}

注意：
- image_prompt 必须是英文，且尽可能详细，确保AI绘图质量
- 同一角色在不同分镜中的外貌描述必须保持一致
- duration 根据旁白/对白文字量合理估算（中文约每秒3-4个字）
- transition 可选值：crossfade(淡入淡出), fade_black(黑场过渡), cut(硬切), slide_left(左滑), slide_right(右滑), zoom_in(放大), zoom_out(缩小)
- 整体分镜数量控制在 8-20 个之间"""


def build_storyboard_prompt(
    script_content: str,
    style_prompt: str = "anime style, high quality, cinematic",
    characters: list[dict] = None,
) -> list[dict[str, str]]:
    """Build the messages list for storyboard generation."""

    characters_appearance = "无特定设定"
    if characters:
        chars = "\n".join(
            [f"- {c['name']}：{c.get('appearance', '未设定')}" for c in characters]
        )
        characters_appearance = chars

    user_content = STORYBOARD_GENERATION_PROMPT.format(
        script_content=script_content,
        style_prompt=style_prompt,
        characters_appearance=characters_appearance,
    )

    return [
        {"role": "system", "content": STORYBOARD_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
