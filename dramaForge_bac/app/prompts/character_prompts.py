"""
DramaForge v2.0 — Character & Scene Description Prompts
=========================================================
Prompt templates for generating detailed character appearances,
personalities, voices, and scene image descriptions.
"""

CHARACTER_DESC_SYSTEM = """你是 DramaForge 的角色设计师 AI。你的输出必须是严格的 JSON 格式。
根据给定的角色名和剧本上下文，生成详细的角色描述。不要输出 JSON 以外的任何文字。"""

CHARACTER_DESC_PROMPT = """根据以下角色信息和剧本上下文，生成该角色的详细描述。

【角色名】{character_name}
【角色类型】{character_role}
【剧本简介】{script_synopsis}
【Story Bible 参考】
{story_bible_context}
【角色出现片段】
{script_excerpt}

请以 JSON 格式输出：
{{
  "appearance": "详细外貌描述（发型、五官、体型、年龄段、典型服饰等，用于AI生成形象图，需要英文描述）",
  "personality": "性格特点描述",
  "role_description": "在剧中的角色定位和作用",
  "voice": "适合的配音风格描述（音色、语速、情绪基调）",
  "image_prompt": "用于AI生成角色形象的英文提示词（详细描述外貌、服装、姿态、风格）"
}}

要求：
1. appearance 使用英文描述，适合作为 AI 绘图提示词
2. image_prompt 必须是英文，包含详细的外貌特征和服装描述
3. voice 需要明确音色特征，便于后续 TTS 配置
4. 必须严格遵循 Story Bible 中的视觉风格规则和世界观设定"""



SCENE_DESC_SYSTEM = """你是 DramaForge 的场景设计师 AI。你的输出必须是严格的 JSON 格式。
根据给定的场景名和故事背景，生成详细的场景描述。不要输出 JSON 以外的任何文字。"""

SCENE_DESC_PROMPT = """根据以下场景信息和故事背景，生成该场景的详细描述。

【场景名】{scene_name}
【故事背景】{story_background}
【故事设定】{story_setting}
【Story Bible 参考】
{story_bible_context}
【时间】{time_of_day}
【室内/室外】{interior}

请以 JSON 格式输出：
{{
  "description": "详细的场景环境描述（氛围、布局、色调、光线等）",
  "image_prompts": [
    "用于AI生成场景图的英文提示词1（白天视角）",
    "用于AI生成场景图的英文提示词2（不同角度或氛围）"
  ]
}}

要求：
1. description 使用中文，充分描绘场景氛围
2. image_prompts 使用英文，包含场景细节、光线、色调、构图
3. 每个 image_prompt 至少 50 个英文单词
4. 必须严格遵循 Story Bible 中的视觉风格规则和世界观设定"""


# ═══════════════════════════════════════════════════════════════════════
# Image Prompt Optimization (for regenerate flow)
# ═══════════════════════════════════════════════════════════════════════

IMAGE_PROMPT_OPTIMIZE_SYSTEM = """你是 DramaForge 的图像提示词优化师。你的任务是根据角色背景和形象描述，生成高质量、细节丰富的英文图像生成提示词。

输出要求：
- 必须是英文
- 包含：角色外貌特征、服装、表情、姿态、光线、构图风格、画质关键词
- 长度：80-150 个英文单词
- 风格：根据指定的剧集风格调整（写实/动漫/电影感等）

只输出优化后的英文提示词文本，不要加任何前缀、注释或 JSON 包装。"""

IMAGE_PROMPT_OPTIMIZE_USER = """请为以下角色形象优化图像生成提示词。

【角色名】{character_name}
【角色类型】{character_role}
【角色描述】{character_description}
【形象名称】{visual_name}
【形象描述】{visual_description}
【剧集风格】{drama_style}
【图像比例】{aspect_ratio}

{extra_guidance}

请输出优化后的英文图像生成提示词："""


def build_character_desc_prompt(
    character_name: str,
    character_role: str,
    script_synopsis: str,
    script_excerpt: str = "",
    story_bible_context: str = "",
) -> list[dict[str, str]]:
    """Build messages for character description generation."""
    user_content = CHARACTER_DESC_PROMPT.format(
        character_name=character_name,
        character_role=character_role,
        script_synopsis=script_synopsis,
        story_bible_context=story_bible_context or "（暂无 Story Bible 参考）",
        script_excerpt=script_excerpt or "(无具体片段)",
    )
    return [
        {"role": "system", "content": CHARACTER_DESC_SYSTEM},
        {"role": "user", "content": user_content},
    ]


def build_scene_desc_prompt(
    scene_name: str,
    story_background: str,
    story_setting: str,
    time_of_day: str = "day",
    interior: bool = True,
    story_bible_context: str = "",
) -> list[dict[str, str]]:
    """Build messages for scene description generation."""
    user_content = SCENE_DESC_PROMPT.format(
        scene_name=scene_name,
        story_background=story_background,
        story_setting=story_setting,
        story_bible_context=story_bible_context or "（暂无 Story Bible 参考）",
        time_of_day=time_of_day,
        interior="室内" if interior else "室外",
    )
    return [
        {"role": "system", "content": SCENE_DESC_SYSTEM},
        {"role": "user", "content": user_content},
    ]


def build_image_prompt_optimize(
    character_name: str,
    character_role: str,
    character_description: str,
    visual_name: str,
    visual_description: str,
    drama_style: str = "realistic",
    aspect_ratio: str = "9:16",
    extra_guidance: str = "",
) -> list[dict[str, str]]:
    """Build messages for optimizing an image generation prompt."""
    user_content = IMAGE_PROMPT_OPTIMIZE_USER.format(
        character_name=character_name,
        character_role=character_role,
        character_description=character_description or "（无）",
        visual_name=visual_name,
        visual_description=visual_description or "（标准形象）",
        drama_style=drama_style,
        aspect_ratio=aspect_ratio,
        extra_guidance=f"【用户额外指引】\n{extra_guidance}" if extra_guidance else "",
    )
    return [
        {"role": "system", "content": IMAGE_PROMPT_OPTIMIZE_SYSTEM},
        {"role": "user", "content": user_content},
    ]
