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

SCRIPT_STRUCTURED_SYSTEM = """你是 DramaForge 的顶尖短剧编剧 AI，精通短视频平台的爆款短剧创作方法论。

## 核心创作原则

### 黄金5秒法则
- 第1秒：画面冲击或悬念抛出
- 第3秒：核心冲突或身份反差建立
- 第5秒：观众必须产生"接下来会怎样"的好奇心
- 绝对禁止：大段旁白介绍背景、慢节奏风景空镜、日常生活流水账

### 每集微结构（1-3分钟）
每集都是完整的"微型三幕剧"：
1. **前30秒（钩子段）**：承接上集悬念，抛出本集核心冲突，建立情绪基调
2. **中间（冲突升级段）**：层层递进，每个场次有递进关系，不能有信息真空
3. **最后30秒（爽点/钩子段）**：释放本集爽点 + 制造下集期待（每集结尾必须有悬念钩子）

### 5大爽点类型
1. **身份碾压**：被看不起→蓄力→身份揭露→全场震惊。围观者反应是爽感放大器
2. **打脸复仇**：被欺负→隐忍→反击→恶人当众出丑。以彼之道还施彼身
3. **逆袭翻盘**：跌入谷底→绝望→转机→步步翻盘→站上巅峰。谷底要够低、转机要有伏笔
4. **情感爆发**：压抑→积累→极限→爆发/告白/和解。压抑越久爆发越动人
5. **悬念揭秘**：谜题建立→线索积累→真相逼近→终极揭秘→震惊。真相必须出人意料但合情合理

### 5种钩子类型（每集结尾必用其一）
1. **悬念钩**：抛出关键疑问，答案留到下一集（身份悬念/结果悬念/来者悬念/发现悬念）
2. **反转钩**：最后一刻颠覆观众预期（身份反转/局势反转/关系反转/动机反转）
3. **情绪钩**：情绪推到最高点切断（甜蜜中断/心碎中断/告白打断/重逢未认）
4. **信息钩**：透露改变全局的关键信息，只说一半（证据揭露/秘密泄露/线索串联）
5. **危机钩**：突发重大危机，主角来不及反应（突袭/背刺/暴露/倒计时/绝境）

### 节奏控制
- 起势段（前15%）：节奏偏快，每2-3集小高潮，密集建立信息
- 攀升段（15%-45%）：节奏稳定上升，每5-7集中高潮，付费卡点最密集
- 风暴段（45%-80%）：节奏最快，每3-5集大高潮，反转密度最高
- 决战段（最后20%）：终极对决→迅速收束→情感余韵

### 6种爆款开场模板
1. 直接打脸型：主角被当众羞辱→施辱者嚣张→主角微妙反应暗示不简单
2. 身份反转型：角色A对B低评价→立刻揭露B的真实身份远超想象→巨大认知反差
3. 极端困境型：主角绝境/死亡边缘→不可思议转折（重生/穿越/觉醒）→获得第二次机会
4. 倒叙悬念型：先展示高冲击结果→"XX天前"→回到故事开端
5. 高甜钩子型：尴尬情境亲密接触→化学反应→一句心动台词
6. 重生起始型：从重生/穿越/回归瞬间开始→快速确认现状→立刻展示改变计划

## 输出格式要求

你必须输出严格的 JSON 格式。所有内容使用中文。所有字段必须填写。

每集的 content 字段使用以下专业剧本格式：

```
△ （景别）场景环境描写，交代时间地点氛围

**角色名**（语气/动作指示）："台词内容"

△ （景别）关键动作或细节描写

♪ 音乐提示：氛围描述

> 🎣 本集钩子：悬念描述
> 📺 下集预告：下一集核心看点
```

景别提示必须使用：全景（建立空间）/ 中景（人物动作）/ 近景（表情反应）/ 特写（关键细节）
每集至少使用3种景别，至少3个场次，800字以上。
角色对白带语气或动作指示，台词口语化自然。
不要输出 JSON 以外的任何文字。"""


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

SCRIPT_STRUCTURED_PROMPT = """根据用户的创意构想，创作一部完整的短剧剧本。

【用户构想】
{user_input}

【创作要求】
- 类型：{genre_label}
- 集数：{total_episodes} 集
- 每集时长：约 {duration} 秒
- 风格：{style}

{genre_context}

【剧本结构要求】
- 第1集必须用强开场模板，前3段抓住观众
- 前30%集数建立角色和核心冲突，每2-3集一个小高潮
- 中间40%集数推进主线和感情线，冲突逐步升级
- 最后30%集数推向高潮，终极对决后2-3集内收束
- 每集结尾必须有悬念钩子（5种钩子类型中选择）
- 全剧至少包含3种以上的爽点类型
- 爽点要有前期压抑→释放的节奏，不能"无铺垫直接爽"
- 全剧最强爽点放在最后阶段

请严格按照以下 JSON 格式输出：

{{
  "protagonist": "主角名字",
  "genre": "剧种类型",
  "synopsis": "整体故事梗概（150-200字，含核心冲突和三幕结构概述）",
  "background": "故事时空背景（时代、地点、社会环境）",
  "setting": "主要场景环境描述",
  "one_liner": "一句话概括（30字以内）",
  "characters": [
    {{
      "name": "角色名",
      "role": "protagonist/antagonist/supporting",
      "description": "角色简介，含外貌特征(2-3句)、性格关键词(3-5个)、核心动机、口头禅"
    }}
  ],
  "scenes": [
    {{
      "name": "场景名称",
      "description": "场景环境描述",
      "time_of_day": "day/night/dawn/dusk",
      "interior": true
    }}
  ],
  "episodes": [
    {{
      "number": 1,
      "title": "本集标题（吸引眼球）",
      "content": "完整的本集剧本内容。使用专业剧本格式：\\n△ （景别）场景描写\\n**角色名**（语气）：\\"台词\\"\\n△ （景别）动作细节\\n♪ 音乐提示\\n> 🎣 本集钩子\\n> 📺 下集预告"
    }}
  ]
}}

严格确保：
1. characters 至少包含 3 个角色（主角、对手、配角）
2. scenes 至少包含 3 个场景
3. episodes 数量 = {total_episodes}
4. 每集 content 使用专业剧本格式，800字以上
5. 每集至少3个场次，使用至少3种景别（全景/中景/近景/特写）
6. 第1集必须用强开场，前5秒有冲击力
7. 每集结尾必须有悬念钩子，标注 🎣
8. 角色对白带语气或动作指示，口语化自然
9. 全剧高潮点合理分布，最高潮放在最后几集"""


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
