"""
DramaForge v2.0 — Storyboard Prompts
======================================
Prompt templates for splitting episodes into structured Shot-level data.
Uses @references for characters and scenes.
"""

STORYBOARD_SYSTEM = """你是 DramaForge 的分镜导演 AI。你的输出必须是严格的 JSON 格式。
根据给定的剧本内容和可用角色/场景资产，将剧本拆解为一系列分镜（Shot）。
不要输出 JSON 以外的任何文字。"""

STORYBOARD_STRUCTURED_PROMPT = """将以下剧本内容拆解为分镜脚本。

【本集标题】{episode_title}
【本集内容】
{episode_content}

【可用角色】
{characters_context}

【可用场景】
{scenes_context}

【每段分镜数量上限】{shots_per_segment}

请严格按照以下 JSON 格式输出：

{{
  "segments": [
    {{
      "title": "片段标题（概括该段内容）",
      "shots": [
        {{
          "duration": 5,
          "time_of_day": "day",
          "scene_ref": "@场景名",
          "camera_type": "medium",
          "camera_angle": "eye_level",
          "camera_movement": "static",
          "characters": [
            {{
              "name": "@角色名",
              "action": "角色在该镜头中的动作描述"
            }}
          ],
          "dialogue": "该镜头的对白或旁白文本",
          "voice_style": "配音风格描述（如：温柔低沉/激动 Highland）",
          "background": "画面背景和氛围描述",
          "transition": "cut"
        }}
      ]
    }}
  ]
}}

字段说明：
- duration: 镜头时长(秒), 3~15
- time_of_day: day/night/dawn/dusk
- scene_ref: 使用 @场景名 引用可用场景
- camera_type: close_up/medium/full/wide/extreme_close/over_shoulder/pov/aerial
- camera_angle: eye_level/low_angle/high_angle/birds_eye/dutch_angle
- camera_movement: static/pan/tilt/zoom_in/zoom_out/dolly/tracking/handheld
- characters[].name: 使用 @角色名 引用可用角色
- transition: cut/fade/dissolve/wipe

要求：
1. 每个 segment 包含 1~{shots_per_segment} 个 shots
2. 总时长合理，覆盖完整剧情
3. 镜头类型和角度要有变化，增加视觉丰富度
4. 对白要贴合原始剧本内容
5. 运动镜头（非 static）用于情绪高潮或动作场景"""


def build_storyboard_prompt(
    episode_title: str,
    episode_content: str,
    characters_context: str,
    scenes_context: str,
    shots_per_segment: int = 5,
) -> list[dict[str, str]]:
    """Build messages for storyboard generation."""
    user_content = STORYBOARD_STRUCTURED_PROMPT.format(
        episode_title=episode_title,
        episode_content=episode_content,
        characters_context=characters_context,
        scenes_context=scenes_context,
        shots_per_segment=shots_per_segment,
    )
    return [
        {"role": "system", "content": STORYBOARD_SYSTEM},
        {"role": "user", "content": user_content},
    ]


def build_asset_context(
    characters: list[dict],
    scenes: list[dict],
) -> tuple[str, str]:
    """
    Build character and scene context strings for the storyboard prompt.

    Returns:
        Tuple of (characters_context, scenes_context)
    """
    char_lines = []
    for ch in characters:
        name = ch.get("name", "")
        role = ch.get("role", "")
        desc = ch.get("description", "")[:100]
        char_lines.append(f"- @{name}（{role}）: {desc}")
    characters_context = "\n".join(char_lines) if char_lines else "（无角色）"

    scene_lines = []
    for sc in scenes:
        name = sc.get("name", "")
        desc = sc.get("description", "")[:100]
        tod = sc.get("time_of_day", "day")
        interior = "室内" if sc.get("interior", True) else "室外"
        scene_lines.append(f"- @{name}（{interior}/{tod}）: {desc}")
    scenes_context = "\n".join(scene_lines) if scene_lines else "（无场景）"

    return characters_context, scenes_context