"""
DramaForge v2.0 — Storyboard Prompts
======================================
Prompt templates for splitting episodes into structured Shot-level data.
Uses @references for characters and scenes.
"""

STORYBOARD_SYSTEM = """你是 DramaForge 的分镜导演 AI。你的输出必须是严格的 JSON 格式。
根据给定的剧本内容和可用角色/场景资产，将剧本拆解为一系列分镜（Shot）。
不要输出 JSON 以外的任何文字。"""


STORYBOARD_REPAIR_SYSTEM = """你是 DramaForge 分镜 JSON 修复器。只输出严格 JSON，不输出解释。
你的任务是修复被截断或格式错误的分镜 JSON，保留已经生成的片段和镜头，必要时补齐缺失字段、括号和数组结束符。"""

STORYBOARD_STRUCTURED_PROMPT = """将以下剧本内容拆解为分镜脚本。

【Story Bible — 叙事基准】
{story_bible_context}

【本集标题】{episode_title}
【本集内容】
{episode_content}

【可用角色（含形象图参考）】
{characters_context}

【可用场景】
{scenes_context}

【每段分镜数量上限】{shots_per_segment}

【标准片段内容结构】
每个 segment 在内容设计上必须包含并贯彻以下三部分：
1. 【基础设定】：画面风格和类型、场景、主要角色、声音规则。
2. 【氛围与画质】：风格核心、视觉基调、画面质感。
3. 【画面内容】：逐条分镜内容。

写入 JSON 时不新增非约定字段，但必须把【基础设定】和【氛围与画质】折入每个 shot 的
background、dialogue、voice_style、camera_type、camera_angle、camera_movement 中。
【基础设定】和【氛围与画质】的具体内容必须根据本集剧本、角色描述、场景资产、Story Bible 中的视觉风格规则和剧情情绪动态推断。
不得套用固定题材、固定美术风格、固定宗教/神话元素、固定声音规则或示例内容。
如果剧本没有明确指定风格，也要从 Story Bible 的视觉风格规则、题材类型、时代背景、人物关系、冲突强度和可用资产中推断一个一致的视觉方案。

请严格按照以下 JSON 格式输出：

{{
  "segments": [
    {{
      "title": "片段标题（概括该段内容）",
      "shots": [
        {{
          "duration": 8,
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
- duration: 镜头时长(秒), 只能填写 4、8、12 其中之一，不得输出其它数值
- time_of_day: day/night/dawn/dusk
- scene_ref: 使用 @场景名 引用可用场景
- camera_type: close_up/medium/full/wide/extreme_close/over_shoulder/pov/aerial
- camera_angle: eye_level/low_angle/high_angle/birds_eye/dutch_angle
- camera_movement: static/pan/tilt/zoom_in/zoom_out/dolly/tracking/handheld
- characters[].name: 使用 @角色名 引用可用角色
- transition: cut/fade/dissolve/wipe

要求：
1. 输出 3~6 个 segment，每个 segment 包含 1~{shots_per_segment} 个 shots
2. 总时长合理，覆盖完整剧情；每个 shot 的 duration 必须严格从 4、8、12 中选择
3. 镜头类型和角度要有变化，增加视觉丰富度
4. dialogue 只保留该镜头需要的对白或旁白，最多 80 个中文字符，不要整段复制剧本
5. 运动镜头（非 static）用于情绪高潮或动作场景
6. background 最多 120 个中文字符，包含场景、构图、光影、角色状态和情绪，不要写成长段文学描写
7. voice_style 最多 60 个中文字符，只描述环境音、动作声、回声、对白语气，不写配乐
8. 输出必须完整闭合 JSON；如果内容太长，减少镜头数量，不要截断 JSON"""


STORYBOARD_REPAIR_PROMPT = """下面的分镜 JSON 未通过解析，可能被截断或包含格式错误。请修复为完整合法 JSON。

【必须遵守】
- 只输出 JSON 对象，根节点必须是 {{"segments": [...]}}。
- 保留已完整出现的 segment 和 shot。
- 如果最后一个 shot 缺字段或缺括号，请补齐：duration、time_of_day、scene_ref、camera_type、camera_angle、camera_movement、characters、dialogue、voice_style、background、transition。
- dialogue 最多 80 个中文字符，background 最多 120 个中文字符，voice_style 最多 60 个中文字符。
- scene_ref 和 characters[].name 必须保留 @ 前缀。
- 不要输出解释文字。

【原始输出】
{raw_output}
"""


def build_storyboard_prompt(
    episode_title: str,
    episode_content: str,
    characters_context: str,
    scenes_context: str,
    shots_per_segment: int = 5,
    story_bible_context: str = "",
) -> list[dict[str, str]]:
    """Build messages for storyboard generation."""
    user_content = STORYBOARD_STRUCTURED_PROMPT.format(
        episode_title=episode_title,
        episode_content=episode_content,
        characters_context=characters_context,
        scenes_context=scenes_context,
        shots_per_segment=shots_per_segment,
        story_bible_context=story_bible_context or "（暂无 Story Bible）",
    )
    return [
        {"role": "system", "content": STORYBOARD_SYSTEM},
        {"role": "user", "content": user_content},
    ]


def build_storyboard_repair_prompt(raw_output: str) -> list[dict[str, str]]:
    """Build messages for repairing malformed storyboard JSON."""
    user_content = STORYBOARD_REPAIR_PROMPT.format(
        raw_output=raw_output[:12000],
    )
    return [
        {"role": "system", "content": STORYBOARD_REPAIR_SYSTEM},
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
        # Include first reference image URL as visual reference hint
        ref_images = ch.get("reference_images", [])
        img_hint = ""
        if ref_images:
            first_img = ref_images[0]
            if isinstance(first_img, dict):
                img_url = first_img.get("url", "")
                img_name = first_img.get("name", "")
                if img_url:
                    img_hint = f" [形象图: {img_name or '已有'}]"
            elif isinstance(first_img, str):
                img_hint = " [已有形象图参考]"
        char_lines.append(f"- @{name}（{role}）: {desc}{img_hint}")
    characters_context = "\n".join(char_lines) if char_lines else "（无角色）"

    scene_lines = []
    for sc in scenes:
        name = sc.get("name", "")
        desc = sc.get("description", "")[:100]
        tod = sc.get("time_of_day", "day")
        interior = "室内" if sc.get("interior", True) else "室外"
        ref_images = sc.get("reference_images", [])
        img_hint = ""
        if ref_images:
            first_img = ref_images[0]
            if isinstance(first_img, dict):
                img_url = first_img.get("url", "")
                if img_url:
                    img_hint = " [已有参考图]"
            elif isinstance(first_img, str):
                img_hint = " [已有参考图]"
        scene_lines.append(f"- @{name}（{interior}/{tod}）: {desc}{img_hint}")
    scenes_context = "\n".join(scene_lines) if scene_lines else "（无场景）"

    return characters_context, scenes_context
