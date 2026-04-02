"""
DramaForge v2.0 — Character & Scene Description Prompts
=========================================================
Prompt templates for generating detailed character appearances,
personalities, voices, and scene image descriptions.
"""

CHARACTER_DESC_SYSTEM = """你是 DramaForge 的角色设计师 AI。你的输出必须是严格的 JSON 格式。
根据给定的角色名和剧本上下文，生成详细的角色描述。不要输出 JSON 以外的任何文字。"""

CHARACTER_DESC_PROMPT = """根据以下角色信息和剧本片段，生成该角色的详细描述。

【角色名】{character_name}
【角色类型】{character_role}
【剧本简介】{script_synopsis}
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
3. voice 需要明确音色特征，便于后续 TTS 配置"""


SCENE_DESC_SYSTEM = """你是 DramaForge 的场景设计师 AI。你的输出必须是严格的 JSON 格式。
根据给定的场景名和故事背景，生成详细的场景描述。不要输出 JSON 以外的任何文字。"""

SCENE_DESC_PROMPT = """根据以下场景信息和故事背景，生成该场景的详细描述。

【场景名】{scene_name}
【故事背景】{story_background}
【故事设定】{story_setting}
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
3. 每个 image_prompt 至少 50 个英文单词"""


def build_character_desc_prompt(
    character_name: str,
    character_role: str,
    script_synopsis: str,
    script_excerpt: str = "",
) -> list[dict[str, str]]:
    """Build messages for character description generation."""
    user_content = CHARACTER_DESC_PROMPT.format(
        character_name=character_name,
        character_role=character_role,
        script_synopsis=script_synopsis,
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
) -> list[dict[str, str]]:
    """Build messages for scene description generation."""
    user_content = SCENE_DESC_PROMPT.format(
        scene_name=scene_name,
        story_background=story_background,
        story_setting=story_setting,
        time_of_day=time_of_day,
        interior="室内" if interior else "室外",
    )
    return [
        {"role": "system", "content": SCENE_DESC_SYSTEM},
        {"role": "user", "content": user_content},
    ]
