"""
DramaForge — Enhanced Script Generation Prompts
=================================================
Incorporates professional micro-drama methodology:
- Genre-specific guidance (13 genres)
- Opening templates (6 patterns)
- Hook design (5 types)
- Satisfaction matrix (5 爽点 types)
- Rhythm curve & episode micro-structure
- Paywall card-point strategy

Reference: short-drama skill by 0xsline
"""

# ═════════════════════════════════════════════════════════════════════
# v3.0 Enhanced Structured System Prompt
# ═════════════════════════════════════════════════════════════════════

SCRIPT_STRUCTURED_SYSTEM = """你是 DramaForge 顶尖短剧编剧 AI。输出严格的 JSON 格式，用中文，字段完整。

## 核心技法
- **开场5秒必抓人**（禁止旁白铺垫/风景空镜/流水账），6种开场：直接打脸/身份反转/极端困境/倒叙悬念/高甜钩子/重生起始
- **爽点5型**（压抑→释放）：身份碾压（围观者反应是放大器）/ 打脸复仇 / 逆袭翻盘（谷底够低才有爆发力）/ 情感爆发（压抑越久越动人）/ 悬念揭秘（出人意料但合情合理）
- **钩子5型**（每集结尾必有，答案留到下集）：悬念钩/反转钩/情绪钩/信息钩/危机钩
- **节奏**：起势段快（2-3集一高潮）→ 攀升段稳（5-7集一中高潮）→ 风暴段密（3-5集一大高潮）→ 决战段最强（终极对决后2-3集收束）
- **全剧≥3种爽点类型**，最强爽点放最后，同类型不连续

## 每集格式（每集≥800字，≥3场次，≥3种景别——全景/中景/近景/特写）

```
△ （景别）场景描写，环境氛围

**角色名**（语气/动作）："台词"

△ （景别）关键动作或细节

♪ 音乐

> 🎣 本集钩子：悬念描述
> 📺 下集预告：下集看点
```

## JSON 结构
输出必须形成两类创作结果：
1. script_summary：生成可审核的全剧摘要，包含集数、故事类型、目标受众、核心梗、一句话故事、人物小传、故事概览。
2. episodes：生成分集剧本，每集有标题和完整正文。

episodes 数组中每个元素的 content 字段必须是完整剧本正文（非摘要），严格遵守上述格式。JSON 中无需转义换行符，直接使用真实换行。"""


# ═════════════════════════════════════════════════════════════════════
# Genre-specific knowledge
# ═════════════════════════════════════════════════════════════════════

GENRE_GUIDE = {
    "urban": {
        "name": "都市情感",
        "audience": "女频，20-35岁城市女性",
        "main_points": "甜宠撒糖、误会冰释、深情告白、渣男被弃",
        "settings": "公司、咖啡馆、公寓、闺蜜聚会",
        "opening": "身份反转型或倒叙悬念型",
        "main_hook": "情绪钩、悬念钩",
        "main_satisfaction": "情感爆发（60%）、身份碾压（25%）、打脸复仇（15%）",
    },
    "romance": {
        "name": "甜宠",
        "audience": "女频，18-28岁年轻女性",
        "main_points": "撒糖名场面、醋精男主、壁咚吻戏、花式宠溺",
        "settings": "校园、职场、同居、甜品店",
        "opening": "高甜钩子型",
        "main_hook": "情绪钩",
        "main_satisfaction": "情感爆发（60%）、身份碾压（25%）、悬念揭秘（15%）",
    },
    "suspense": {
        "name": "悬疑探案",
        "audience": "男女通吃，22-40岁",
        "main_points": "反转揭秘、真凶现形、推理碾压、善恶终有报",
        "settings": "案发现场、审讯室、暗线调查",
        "opening": "倒叙悬念型或极端困境型",
        "main_hook": "信息钩、悬念钩、反转钩",
        "main_satisfaction": "悬念揭秘（50%）、逆袭翻盘（30%）、打脸复仇（20%）",
    },
    "fantasy": {
        "name": "仙侠/奇幻",
        "audience": "男女通吃，18-35岁",
        "main_points": "修为突破、法宝现世、门派打脸、仙界恋情",
        "settings": "仙山、洞府、仙门、凡间",
        "opening": "极端困境型或重生起始型",
        "main_hook": "反转钩、危机钩",
        "main_satisfaction": "身份碾压（40%）、逆袭翻盘（35%）、情感爆发（25%）",
    },
    "historical": {
        "name": "古装宫廷",
        "audience": "女频，20-40岁女性",
        "main_points": "宫斗反杀、计谋得逞、扳倒对手、帝王独宠",
        "settings": "皇宫、后宫、朝堂、冷宫",
        "opening": "倒叙悬念型或极端困境型",
        "main_hook": "反转钩、危机钩",
        "main_satisfaction": "逆袭翻盘（40%）、打脸复仇（30%）、悬念揭秘（30%）",
    },
    "revenge": {
        "name": "复仇逆袭",
        "audience": "男女通吃，20-35岁",
        "main_points": "绝地翻盘、实力碾压、小人落败、华丽归来",
        "settings": "职场、商业竞争、社交场合",
        "opening": "直接打脸型或极端困境型",
        "main_hook": "悬念钩、危机钩、反转钩",
        "main_satisfaction": "打脸复仇（40%）、逆袭翻盘（40%）、身份碾压（20%）",
    },
    "thriller": {
        "name": "惊悚/末世",
        "audience": "男频为主，20-35岁",
        "main_points": "资源争夺、能力觉醒、绝境求生、团队组建",
        "settings": "末日场景、安全区、废墟",
        "opening": "重生起始型或极端困境型",
        "main_hook": "危机钩、悬念钩",
        "main_satisfaction": "逆袭翻盘（40%）、身份碾压（30%）、悬念揭秘（30%）",
    },
    "comedy": {
        "name": "喜剧",
        "audience": "全年龄",
        "main_points": "反差笑料、误会喜剧、吐槽金句、荒诞反转",
        "settings": "各种日常场景",
        "opening": "身份反转型或直接打脸型",
        "main_hook": "反转钩、情绪钩",
        "main_satisfaction": "打脸复仇（35%）、情感爆发（30%）、悬念揭秘（35%）",
    },
    "other": {
        "name": "其他题材",
        "audience": "根据具体题材灵活调整",
        "main_points": "根据题材特征确定核心爽点，常见包括身份反转、逆袭翻盘、情感爆发",
        "settings": "根据题材确定场景",
        "opening": "根据题材选择最优开场方式",
        "main_hook": "根据题材选择最合适的钩子类型",
        "main_satisfaction": "根据题材灵活调配爽点比例",
    },
}


def _build_genre_context(genre: str) -> str:
    """Build genre-specific context section from GENRE_GUIDE."""
    info = GENRE_GUIDE.get(genre)
    if not info:
        return ""

    return f"""【题材指导】
- 题材：{info['name']}
- 核心受众：{info['audience']}
- 典型爽点：{info['main_points']}
- 常见场景：{info['settings']}
- 推荐开场：{info['opening']}
- 主用钩子：{info['main_hook']}
- 爽点配比：{info['main_satisfaction']}"""


# ═════════════════════════════════════════════════════════════════════
# Structured JSON Prompt (v3.0 Enhanced)
# ═════════════════════════════════════════════════════════════════════

SCRIPT_STRUCTURED_PROMPT = """根据用户构想创作完整短剧剧本，{total_episodes} 集，每集约{duration}秒。

【用户构想】
{user_input}

【类型】{genre_label} | 风格：{style}
{genre_context}

【关键要求】
- 第1集用强开场，前3段必须有冲击力
- 每集结尾必须有钩子（悬念/反转/情绪/信息/危机）
- 前段建立角色冲突，中段升级推进，后段推向最强高潮
- 爽点要有「压抑→释放」节奏，最高潮放最后
- 原始创意只作为参考输入，不要生成 original_idea 字段
- 输出层级必须稳定为：剧本摘要 → 分集剧本
- 剧本摘要用于快速审核项目设定，分集剧本用于直接拍摄；不要把分集正文写成摘要

【输出 JSON】
{{
  "script_summary": {{
    "custom_episode_count": {total_episodes},
    "story_type": "{genre_label}",
    "target_audience": "男频/女频/大众，以及年龄段",
    "core_hook": "核心梗：主冲突+反转+爽点组合",
    "one_sentence_story": "一句话故事",
    "character_biographies": "主要角色小传，按角色分段，包含身份、视觉形象、核心标签、身份背景、成长经历、性格特点、角色关系、成长弧线",
    "story_overview": "全剧故事概览，交代三幕推进、关键反转和终局"
  }},
  "episode_outline": [
    {{"number": 1, "title": "分集标题", "summary": "本集核心冲突或爽点一句话"}}
  ],
  "protagonist": "主角姓名",
  "genre": "题材",
  "synopsis": "使用 script_summary.story_overview 的内容，150-300字",
  "background": "时代/地点/社会背景",
  "setting": "使用 script_summary.core_hook 的内容",
  "one_liner": "使用 script_summary.one_sentence_story 的内容，30-60字",
  "characters": [
    {{"name": "角色名", "role": "protagonist/antagonist/supporting", "description": "外貌+性格+动机+口头禅"}}
  ],
  "scenes": [
    {{"name": "场景名", "description": "环境描述", "time_of_day": "day/night/dawn/dusk", "interior": true}}
  ],
  "episodes": [
    {{
      "number": 1,
      "title": "吸引眼球的标题",
      "content": "△ （全景）场景环境描写，交代时间地点\\n\\n**角色名**（语气/动作）：\\"台词内容\\"\\n\\n△ （中景）人物的动作细节\\n\\n♪ 音乐氛围\\n\\n> 🎣 本集钩子：悬念描述\\n> 📺 下集预告：看点"
    }}
  ]
}}

⚠️ 重要：每集 content 必须 ≥800 字、≥3个场次（用 --- 分隔）、使用≥3种景别（全景/中景/近景/特写）。
episodes 数组长度必须 = {total_episodes}。
episode_outline 数组长度必须 = {total_episodes}，且标题与 episodes 一一对应。
characters ≥3个，scenes ≥3个。
content 是完整剧本正文，不是摘要！每句对白都要写出来！"""


# ═════════════════════════════════════════════════════════════════════
# v1.0 Legacy Prompts (backward compatibility)
# ═════════════════════════════════════════════════════════════════════

SCRIPT_SYSTEM_PROMPT = """你是一个专业的短剧编剧AI助手。你擅长创作各种类型的短剧剧本，包括甜宠、悬疑、搞笑、奇幻等。
你创作的剧本需要满足以下要求：
1. 剧情紧凑，节奏明快，适合短视频平台传播
2. 角色性格鲜明，对白自然生动
3. 每集有明确的冲突和高潮点
4. 结尾留有悬念或反转，吸引观众继续观看
5. 剧本格式清晰，包含场景描述、角色对白、旁白等要素"""


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


# ═════════════════════════════════════════════════════════════════════
# Prompt Builder Functions
# ═════════════════════════════════════════════════════════════════════

# Genre name mapping (English enum → Chinese display)
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
    genre: str = "other",
    total_episodes: int = 1,
    duration: int = 60,
    style: str = "写实",
) -> list[dict[str, str]]:
    """Build the messages list for v3.0 enhanced structured JSON script generation."""

    genre_label = _GENRE_LABELS.get(genre, genre)
    genre_context = _build_genre_context(genre)

    user_content = SCRIPT_STRUCTURED_PROMPT.format(
        user_input=user_input,
        genre_label=genre_label,
        total_episodes=total_episodes,
        duration=duration,
        style=style,
        genre_context=genre_context,
    )

    return [
        {"role": "system", "content": SCRIPT_STRUCTURED_SYSTEM},
        {"role": "user", "content": user_content},
    ]
