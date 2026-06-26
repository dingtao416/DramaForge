"""
DramaForge runtime prompts for stable script generation.

This module is the single product source of truth for AI script generation.
It keeps the useful micro-drama methodology in runtime prompts and avoids
external multi-step skill workflows.
"""

from __future__ import annotations

import json


SCRIPT_STRUCTURED_SYSTEM = """你是 DramaForge 的短剧编剧与结构化数据生成 AI。你必须输出严格 JSON，不输出 Markdown，不输出解释文字。

创作方法论：
- 开场 5 秒必须抓人，优先使用直接打脸、身份反转、极端困境、倒叙悬念、高甜钩子或重生起始。
- 爽点采用压抑到释放：身份碾压、打脸复仇、逆袭翻盘、情感爆发、悬念揭秘；全剧至少覆盖 3 种爽点。
- 每集结尾必须有钩子，类型包括悬念钩、反转钩、情绪钩、信息钩、危机钩。
- 节奏按起势、攀升、风暴、决战推进，高潮逐步增强，最强爽点放在后段。
- 角色体系必须包含主角、主要对手和推动剧情的配角；反派可以分为小反派、中反派、终极对手或隐藏反派。
- 每集正文用于直接拍摄，不能写成摘要；每集至少 3 个场次，使用全景/中景/近景/特写等景别。

结构化要求：
- 最终 JSON 必须包含 counts、script_summary、episode_outline、protagonist、genre、synopsis、background、setting、one_liner、characters、scenes、episodes。
- counts 必须等于数组真实长度。
- characters 和 scenes 的 name 必须非空、唯一、稳定。
- episodes 数组长度必须等于用户要求集数。
- 每集必须包含 character_refs 和 scene_refs，且每个引用都必须存在于 characters.name 或 scenes.name。
- content 字段必须是完整剧本正文，包含场景描写、角色对白、音乐提示、结尾钩子和下集预告。
"""


GENRE_GUIDE = {
    "urban": {
        "name": "都市情感",
        "audience": "女频，20-35岁城市女性",
        "main_points": "甜宠撒糖、误会冰释、深情告白、渣男被弃",
        "settings": "公司、咖啡馆、公寓、闺蜜聚会",
        "opening": "身份反转型或倒叙悬念型",
        "main_hook": "情绪钩、悬念钩",
        "main_satisfaction": "情感爆发、身份碾压、打脸复仇",
    },
    "romance": {
        "name": "甜宠",
        "audience": "女频，18-28岁年轻女性",
        "main_points": "撒糖名场面、醋精男主、壁咚吻戏、花式宠溺",
        "settings": "校园、职场、同居、甜品店",
        "opening": "高甜钩子型",
        "main_hook": "情绪钩",
        "main_satisfaction": "情感爆发、身份碾压、悬念揭秘",
    },
    "suspense": {
        "name": "悬疑探案",
        "audience": "男女通吃，22-40岁",
        "main_points": "反转揭秘、真凶现形、推理碾压、善恶终有报",
        "settings": "案发现场、审讯室、暗线调查",
        "opening": "倒叙悬念型或极端困境型",
        "main_hook": "信息钩、悬念钩、反转钩",
        "main_satisfaction": "悬念揭秘、逆袭翻盘、打脸复仇",
    },
    "fantasy": {
        "name": "仙侠奇幻",
        "audience": "男女通吃，18-35岁",
        "main_points": "修为突破、法宝现世、门派打脸、仙界恋情",
        "settings": "仙山、洞府、仙门、凡间",
        "opening": "极端困境型或重生起始型",
        "main_hook": "反转钩、危机钩",
        "main_satisfaction": "身份碾压、逆袭翻盘、情感爆发",
    },
    "historical": {
        "name": "古装宫廷",
        "audience": "女频，20-40岁女性",
        "main_points": "宫斗反杀、计谋得逞、扳倒对手、帝王独宠",
        "settings": "皇宫、后宫、朝堂、冷宫",
        "opening": "倒叙悬念型或极端困境型",
        "main_hook": "反转钩、危机钩",
        "main_satisfaction": "逆袭翻盘、打脸复仇、悬念揭秘",
    },
    "revenge": {
        "name": "复仇逆袭",
        "audience": "男女通吃，20-35岁",
        "main_points": "绝地翻盘、实力碾压、小人落败、华丽归来",
        "settings": "职场、商业竞争、社交场合",
        "opening": "直接打脸型或极端困境型",
        "main_hook": "悬念钩、危机钩、反转钩",
        "main_satisfaction": "打脸复仇、逆袭翻盘、身份碾压",
    },
    "thriller": {
        "name": "惊悚末世",
        "audience": "男频为主，20-35岁",
        "main_points": "资源争夺、能力觉醒、绝境求生、团队组建",
        "settings": "末日场景、安全区、废墟",
        "opening": "重生起始型或极端困境型",
        "main_hook": "危机钩、悬念钩",
        "main_satisfaction": "逆袭翻盘、身份碾压、悬念揭秘",
    },
    "comedy": {
        "name": "喜剧",
        "audience": "全年龄",
        "main_points": "反差笑料、误会喜剧、吐槽金句、荒诞反转",
        "settings": "日常、职场、家庭、社交场合",
        "opening": "身份反转型或直接打脸型",
        "main_hook": "反转钩、情绪钩",
        "main_satisfaction": "打脸复仇、情感爆发、悬念揭秘",
    },
    "other": {
        "name": "其他",
        "audience": "根据题材灵活调整",
        "main_points": "身份反转、逆袭翻盘、情感爆发",
        "settings": "根据题材确定场景",
        "opening": "根据题材选择最强开场",
        "main_hook": "根据题材选择钩子",
        "main_satisfaction": "多种爽点交替",
    },
}


_GENRE_LABELS = {
    "urban": "都市情感",
    "romance": "甜宠",
    "suspense": "悬疑探案",
    "fantasy": "仙侠奇幻",
    "historical": "古装宫廷",
    "revenge": "复仇逆袭",
    "thriller": "惊悚末世",
    "comedy": "喜剧",
    "other": "其他",
}


def _build_genre_context(genre: str) -> str:
    info = GENRE_GUIDE.get(genre)
    if not info:
        return ""

    return f"""【题材指导】
- 题材：{info["name"]}
- 核心受众：{info["audience"]}
- 典型爽点：{info["main_points"]}
- 常见场景：{info["settings"]}
- 推荐开场：{info["opening"]}
- 主用钩子：{info["main_hook"]}
- 爽点组合：{info["main_satisfaction"]}"""


SCRIPT_STRUCTURED_PROMPT = """根据用户构想创作完整短剧剧本，{total_episodes} 集，每集约 {duration} 秒。

【用户构想】
{user_input}

【类型】{genre_label} | 风格：{style}
{genre_context}

【输出 JSON Schema】
{{
  "counts": {{
    "episode_count": {total_episodes},
    "character_count": 0,
    "scene_count": 0
  }},
  "script_summary": {{
    "custom_episode_count": {total_episodes},
    "story_type": "{genre_label}",
    "target_audience": "男频/女频/大众，以及年龄段",
    "core_hook": "核心梗：主冲突+反转+爽点组合",
    "one_sentence_story": "一句话故事",
    "character_biographies": "主要角色小传，按角色分段",
    "story_overview": "全剧故事概览，交代三幕推进、关键反转和终局"
  }},
  "episode_outline": [
    {{"number": 1, "title": "分集标题", "summary": "本集核心冲突或爽点一句话"}}
  ],
  "protagonist": "主角姓名",
  "genre": "{genre_label}",
  "synopsis": "使用 script_summary.story_overview 的内容，150-300字",
  "background": "时代/地点/社会背景",
  "setting": "使用 script_summary.core_hook 的内容",
  "one_liner": "使用 script_summary.one_sentence_story 的内容，30-60字",
  "characters": [
    {{"name": "角色名", "role": "protagonist/antagonist/supporting", "description": "外貌+性格+动机+语言特征"}}
  ],
  "scenes": [
    {{"name": "场景名", "description": "环境描述", "time_of_day": "day/night/dawn/dusk", "interior": true}}
  ],
  "episodes": [
    {{
      "number": 1,
      "title": "吸引眼球的标题",
      "character_refs": ["本集出现的角色名"],
      "scene_refs": ["本集出现的场景名"],
      "content": "△ （全景）场景环境描写，交代时间地点\\n\\n**角色名**（语气/动作）：\\"台词内容\\"\\n\\n---\\n\\n△ （中景）下一场次动作细节\\n\\n♪ 音乐氛围\\n\\n> 🎣 本集钩子：悬念描述\\n> 📺 下集预告：看点"
    }}
  ]
}}

硬性要求：
- episodes 数组长度必须 = {total_episodes}。
- episode_outline 数组长度必须 = {total_episodes}，且 number 与 episodes 一一对应。
- characters 至少 3 个，scenes 至少 3 个。
- counts.character_count 必须等于 characters 数组长度，counts.scene_count 必须等于 scenes 数组长度。
- 每个 episode.character_refs 和 episode.scene_refs 必须只引用上方清单中真实存在的 name。
- 每集 content 必须是完整剧本正文，不能是摘要。"""


SCRIPT_REPAIR_SYSTEM = """你是 DramaForge JSON 修复器。只输出修复后的完整 JSON，不输出解释。
你必须保留原故事、角色、场景和分集正文的创作意图，只修复结构、计数、缺失引用和不一致字段。"""


SCRIPT_REPAIR_PROMPT = """下面的剧本 JSON 未通过后端校验。请修复为完整合法 JSON。

【期望集数】
{expected_episodes}

【校验错误】
{issues}

【原始 JSON】
{raw_json}

修复要求：
- counts 必须与数组真实长度一致。
- episodes 数组长度必须等于期望集数。
- 每集必须有 character_refs 和 scene_refs。
- 每个引用都必须存在于 characters.name 或 scenes.name。
- 不要删除完整正文；必要时补齐角色、场景或引用。"""


UPLOAD_ANALYSIS_SYSTEM = """你是 DramaForge 剧本解析器。你只输出严格 JSON。
你的任务是从用户上传的完整剧本文本中抽取显式字段里的角色、场景、分集标题和每集引用关系。
不要根据对白、剧情描述、作者、类型、时间、地点、字数等元信息推断角色或场景。"""


UPLOAD_ANALYSIS_PROMPT = """请从下面上传剧本文本中抽取结构化信息。

【期望集数】
{total_episodes}

【剧本文本】
{script_text}

输出 JSON：
{{
  "counts": {{"episode_count": {total_episodes}, "character_count": 0, "scene_count": 0}},
  "protagonist": "主角姓名，如无法判断则为空字符串",
  "characters": [
    {{"name": "角色名", "role": "protagonist/antagonist/supporting", "description": "从文本推断的身份、性格或关系"}}
  ],
  "scenes": [
    {{"name": "场景名", "description": "从文本推断的环境", "time_of_day": "day/night/dawn/dusk", "interior": true}}
  ],
  "episodes": [
    {{"number": 1, "title": "分集标题", "character_refs": ["角色名"], "scene_refs": ["场景名"]}}
  ]
}}

要求：
- characters 只能来自明确字段：角色表、角色清单、主要角色、人物、出场人物。
- scenes 只能来自明确字段：场景、场景表、场景清单、拍摄场景。
- 剧本、作者、类型、题材、字数、时间、地点、风格、集数是元信息，不得作为角色或场景。
- 不要从对白行、剧情简介、动作描述中推断角色和场景。
- 如果缺少上述字段，对应数组必须返回空数组，counts 中对应数量为 0。
- 不要生成剧本正文，不要改写用户文本。
- 每集 character_refs 和 scene_refs 只能引用已经从明确字段抽取出的名称。"""


NARRATION_REWRITE_PROMPT = """将以下对话型剧本改写为旁白叙述型。

要求：
1. 去除所有角色直接对话，改为第三人称旁白叙述。
2. 保留核心剧情和情节推进。
3. 增加画面描写和氛围渲染。
4. 适合用于 AI 语音旁白配音。
5. 输出纯文本，不需要 JSON。

【原始剧本】
{script_content}

【改写后的旁白剧本】"""


def build_structured_prompt(
    user_input: str,
    genre: str = "other",
    total_episodes: int = 1,
    duration: int = 60,
    style: str = "写实",
) -> list[dict[str, str]]:
    genre_label = _GENRE_LABELS.get(genre, genre)
    user_content = SCRIPT_STRUCTURED_PROMPT.format(
        user_input=user_input,
        genre_label=genre_label,
        total_episodes=total_episodes,
        duration=duration,
        style=style,
        genre_context=_build_genre_context(genre),
    )

    return [
        {"role": "system", "content": SCRIPT_STRUCTURED_SYSTEM},
        {"role": "user", "content": user_content},
    ]


def build_repair_prompt(raw_json: dict, issues: list[str], expected_episodes: int) -> list[dict[str, str]]:
    user_content = SCRIPT_REPAIR_PROMPT.format(
        expected_episodes=expected_episodes,
        issues="\n".join(f"- {issue}" for issue in issues),
        raw_json=json.dumps(raw_json, ensure_ascii=False, indent=2),
    )
    return [
        {"role": "system", "content": SCRIPT_REPAIR_SYSTEM},
        {"role": "user", "content": user_content},
    ]


def build_upload_analysis_prompt(
    script_text: str,
    total_episodes: int,
) -> list[dict[str, str]]:
    user_content = UPLOAD_ANALYSIS_PROMPT.format(
        total_episodes=total_episodes,
        script_text=script_text,
    )
    return [
        {"role": "system", "content": UPLOAD_ANALYSIS_SYSTEM},
        {"role": "user", "content": user_content},
    ]
