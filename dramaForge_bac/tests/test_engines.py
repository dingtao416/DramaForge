import json
import importlib

import pytest

from app.ai_hub._models import ChatResponse
from app.engines.script_engine import ScriptEngine
from app.engines.video_engine import VideoEngine
from app.models.character import Character, CharacterRole
from app.models.episode import Episode
from app.models.project import DramaGenre, Project, VideoStyle
from app.models.scene import SceneLocation


script_engine_module = importlib.import_module("app.engines.script_engine")
assets_engine_module = importlib.import_module("app.engines.assets_engine")
video_engine_module = importlib.import_module("app.engines.video_engine")


def _project() -> Project:
    return Project(
        id=1,
        user_id=1,
        title="Demo",
        genre=DramaGenre.URBAN,
        style=VideoStyle.REALISTIC,
    )


def _raw_script(**overrides):
    data = {
        "counts": {
            "episode_count": 1,
            "character_count": 2,
            "scene_count": 1,
        },
        "script_summary": {
            "story_overview": "女主在公司被陷害后反击。",
            "core_hook": "职场陷害与身份反转",
            "one_sentence_story": "被陷害的女主用真相完成反击。",
        },
        "story_bible": {
            "premise": "林夏被职场对手陷害后，用证据和冷静判断完成反击。",
            "world_rules": "现代都市职场环境，会议证据和公司制度决定人物处境。",
            "character_relationships": "林夏与周铭是职场对手，冲突围绕陷害和反证展开。",
            "timeline": "第1集：会议反击。",
            "episode_arc": "单集内完成陷害曝光、证据反转和人物胜负变化。",
            "visual_style": "写实都市风格，会议室光线冷静克制，镜头强调压迫感。",
            "continuity_notes": "林夏保持冷静专业形象，周铭保持紧张失控状态。",
        },
        "protagonist": "林夏",
        "genre": "都市情感",
        "background": "现代都市",
        "characters": [
            {"name": "林夏", "role": "protagonist", "description": "聪明坚韧的女主"},
            {"name": "周铭", "role": "antagonist", "description": "制造陷害的对手"},
        ],
        "scenes": [
            {"name": "公司会议室", "description": "高压会议现场", "time_of_day": "day", "interior": True},
        ],
        "episode_outline": [
            {"number": 1, "title": "会议反击", "summary": "林夏在会议上反击陷害"},
        ],
        "episodes": [
            {
                "number": 1,
                "title": "会议反击",
                "character_refs": ["林夏", "周铭"],
                "scene_refs": ["公司会议室"],
                "content": "△ （全景）公司会议室里气氛紧张。\n\n**林夏**（冷静）：\"证据在这里。\"",
            },
        ],
    }
    data.update(overrides)
    return data


def _chat_response(data: dict) -> ChatResponse:
    return ChatResponse(content=json.dumps(data, ensure_ascii=False), model="test-model")


def _chat_text_response(text: str) -> ChatResponse:
    return ChatResponse(content=text, model="test-model")


def test_parse_script_normalizes_counts_and_references():
    engine = ScriptEngine()

    result = engine._parse_script(_raw_script(), project_id=1, expected_episodes=1)
    stored = json.loads(result["script"]["raw_content"])

    assert len(result["episodes"]) == 1
    assert len(result["characters"]) == 2
    assert len(result["scenes"]) == 1
    assert stored["counts"] == {
        "episode_count": 1,
        "character_count": 2,
        "scene_count": 1,
    }
    assert stored["episodes"][0]["character_refs"] == ["林夏", "周铭"]
    assert stored["episodes"][0]["scene_refs"] == ["公司会议室"]


@pytest.mark.asyncio
async def test_create_from_text_repairs_invalid_counts_once(monkeypatch):
    engine = ScriptEngine()
    invalid = _raw_script(counts={"episode_count": 1, "character_count": 99, "scene_count": 1})
    fixed = _raw_script()
    calls = []

    async def complete(**kwargs):
        calls.append(kwargs)
        return _chat_response(invalid if len(calls) == 1 else fixed)

    monkeypatch.setattr(script_engine_module.ai_hub.chat, "complete", complete)

    result = await engine.create_from_text(
        user_input="职场反击",
        project=_project(),
        total_episodes=1,
    )

    assert len(calls) == 2
    assert len(result["characters"]) == 2
    assert len(result["scenes"]) == 1


@pytest.mark.asyncio
async def test_create_from_text_repairs_missing_story_bible_once(monkeypatch):
    engine = ScriptEngine()
    invalid = _raw_script(story_bible={})
    fixed = _raw_script()
    calls = []

    async def complete(**kwargs):
        calls.append(kwargs)
        return _chat_response(invalid if len(calls) == 1 else fixed)

    monkeypatch.setattr(script_engine_module.ai_hub.chat, "complete", complete)

    result = await engine.create_from_text(
        user_input="职场反击",
        project=_project(),
        total_episodes=1,
    )

    assert len(calls) == 2
    assert result["script"]["premise"]
    assert result["script"]["visual_style_rules"]


@pytest.mark.asyncio
async def test_create_from_text_fails_after_repair_keeps_bad_references(monkeypatch):
    engine = ScriptEngine()
    invalid = _raw_script(
        episodes=[
            {
                "number": 1,
                "title": "错误引用",
                "character_refs": ["不存在的人"],
                "scene_refs": ["公司会议室"],
                "content": "△ （全景）公司会议室。\n\n**林夏**：\"开始。\"",
            },
        ],
    )
    calls = []

    async def complete(**kwargs):
        calls.append(kwargs)
        return _chat_response(invalid)

    monkeypatch.setattr(script_engine_module.ai_hub.chat, "complete", complete)

    with pytest.raises(ValueError, match="Script validation failed"):
        await engine.create_from_text(
            user_input="职场反击",
            project=_project(),
            total_episodes=1,
        )

    assert len(calls) == 2


@pytest.mark.asyncio
async def test_create_from_docx_extracts_uploaded_characters_and_scenes(monkeypatch, tmp_path):
    engine = ScriptEngine()
    script_file = tmp_path / "script.txt"
    script_file.write_text(
        "第1集\n**出场人物：** 林夏、周铭\n**场景：** 公司会议室\n**林夏**：\"证据在这里。\"",
        encoding="utf-8",
    )

    async def complete(**kwargs):
        return _chat_response(_raw_script())

    monkeypatch.setattr(script_engine_module.ai_hub.chat, "complete", complete)

    result = await engine.create_from_docx(script_file, _project(), total_episodes=1)

    assert result["warnings"] == []
    assert [character["name"] for character in result["characters"]] == ["林夏", "周铭"]
    assert [scene["name"] for scene in result["scenes"]] == ["公司会议室"]
    assert result["script"]["premise"]
    assert result["script"]["continuity_notes"]


@pytest.mark.asyncio
async def test_create_from_docx_keeps_script_when_uploaded_extraction_fails(monkeypatch, tmp_path):
    engine = ScriptEngine()
    script_file = tmp_path / "script.txt"
    script_file.write_text("第1集\n这是一段没有标准格式的剧本文本。", encoding="utf-8")

    async def complete(**kwargs):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(script_engine_module.ai_hub.chat, "complete", complete)

    result = await engine.create_from_docx(script_file, _project(), total_episodes=1)

    assert len(result["episodes"]) == 1
    assert result["characters"] == []
    assert result["scenes"] == []
    assert result["script"]["premise"]
    assert result["warnings"] == ["角色/场景未能自动解析，可手动补充或重新解析"]


@pytest.mark.asyncio
async def test_create_from_docx_falls_back_to_rules_for_standard_markdown(monkeypatch, tmp_path):
    engine = ScriptEngine()
    script_file = tmp_path / "script.txt"
    script_file.write_text(
        "\n".join([
            "第1集：会议反击",
            "## 场次一",
            "**场景：** 内景 · 公司会议室 · 日",
            "**出场人物：** 林夏、周铭",
            "△ （全景）公司会议室里所有人盯着屏幕。",
            "**林夏**（冷静）：\"证据在这里。\"",
            "**周铭**（慌张）：\"这不可能。\"",
        ]),
        encoding="utf-8",
    )

    async def complete(**kwargs):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(script_engine_module.ai_hub.chat, "complete", complete)

    result = await engine.create_from_docx(script_file, _project(), total_episodes=1)

    assert [character["name"] for character in result["characters"]] == ["林夏", "周铭"]
    assert [scene["name"] for scene in result["scenes"]] == ["公司会议室"]
    assert result["warnings"] == []


@pytest.mark.asyncio
async def test_create_from_docx_rule_fallback_ignores_script_metadata(monkeypatch, tmp_path):
    engine = ScriptEngine()
    script_file = tmp_path / "script.txt"
    script_file.write_text(
        "\n".join([
            "剧本：逆袭短剧",
            "作者：张三",
            "类型：都市",
            "字数：1000",
            "时间：夜",
            "地点：公寓",
            "第1集：会议反击",
            "**场景：** 内景 · 公司会议室 · 日",
            "**出场人物：** 林夏、周铭",
            "**林夏**（冷静）：\"证据在这里。\"",
            "**周铭**（慌张）：\"这不可能。\"",
        ]),
        encoding="utf-8",
    )

    async def complete(**kwargs):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(script_engine_module.ai_hub.chat, "complete", complete)

    result = await engine.create_from_docx(script_file, _project(), total_episodes=1)

    assert [character["name"] for character in result["characters"]] == ["林夏", "周铭"]
    assert [scene["name"] for scene in result["scenes"]] == ["公司会议室"]
    assert result["warnings"] == []


@pytest.mark.asyncio
async def test_create_from_docx_preserves_scene_refs_with_english_spaces(monkeypatch, tmp_path):
    engine = ScriptEngine()
    script_file = tmp_path / "script.txt"
    script_file.write_text(
        "\n".join([
            "角色清单",
            "1. 林砚 - 女，32岁。Mnemosyne公司首席架构师。",
            "2. 陈墨 - 男，35岁。Mnemosyne公司CEO。",
            "",
            "场景清单",
            "（按时间顺序）",
            "1. 内景  Mnemosyne公司Project Lethe开发室  深夜",
            "",
            "第1集：开发室对峙",
            "**场景：** 内景 · Mnemosyne公司Project Lethe开发室 · 深夜",
            "**出场人物：** 林砚、陈墨",
            "**林砚**（冷静）：\"Project Lethe 不能上线。\"",
        ]),
        encoding="utf-8",
    )

    async def complete(**kwargs):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(script_engine_module.ai_hub.chat, "complete", complete)

    result = await engine.create_from_docx(script_file, _project(), total_episodes=1)

    assert [scene["name"] for scene in result["scenes"]] == ["Mnemosyne公司Project Lethe开发室"]
    stored = json.loads(result["script"]["raw_content"])
    assert stored["episodes"][0]["scene_refs"] == ["Mnemosyne公司Project Lethe开发室"]


@pytest.mark.asyncio
async def test_create_from_docx_requires_explicit_asset_fields(monkeypatch, tmp_path):
    engine = ScriptEngine()
    script_file = tmp_path / "script.txt"
    script_file.write_text(
        "\n".join([
            "剧本：逆袭短剧",
            "作者：张三",
            "类型：都市",
            "时间：夜",
            "地点：公寓",
            "第1集：会议反击",
            "**林夏**（冷静）：\"证据在这里。\"",
            "**周铭**（慌张）：\"这不可能。\"",
        ]),
        encoding="utf-8",
    )

    async def complete(**kwargs):
        return _chat_response(_raw_script())

    monkeypatch.setattr(script_engine_module.ai_hub.chat, "complete", complete)

    result = await engine.create_from_docx(script_file, _project(), total_episodes=1)

    assert result["characters"] == []
    assert result["scenes"] == []
    assert result["warnings"] == ["角色/场景未能自动解析，可手动补充或重新解析"]


@pytest.mark.asyncio
async def test_create_from_docx_keeps_field_assets_when_upload_counts_are_wrong(monkeypatch, tmp_path):
    engine = ScriptEngine()
    script_file = tmp_path / "script.txt"
    script_file.write_text(
        "第1集\n**出场人物：** 林夏、周铭\n**场景：** 公司会议室\n**林夏**：\"证据在这里。\"",
        encoding="utf-8",
    )
    extracted = _raw_script(counts={"episode_count": 1, "character_count": 0, "scene_count": 0})

    async def complete(**kwargs):
        return _chat_response(extracted)

    monkeypatch.setattr(script_engine_module.ai_hub.chat, "complete", complete)

    result = await engine.create_from_docx(script_file, _project(), total_episodes=1)

    assert [character["name"] for character in result["characters"]] == ["林夏", "周铭"]
    assert [scene["name"] for scene in result["scenes"]] == ["公司会议室"]


@pytest.mark.asyncio
async def test_regenerate_character_image_records_appearance_type(monkeypatch):
    engine = assets_engine_module.AssetsEngine()
    character = Character(
        id=7,
        project_id=1,
        name="林夏",
        role=CharacterRole.PROTAGONIST,
        description="聪明坚韧",
        reference_images=[],
    )

    async def generate(**kwargs):
        return None

    monkeypatch.setattr(assets_engine_module.ai_hub.image, "generate", generate)

    urls = await engine.regenerate_character_image(
        character=character,
        project_id=1,
        prompt="portrait",
        appearance_type="turnaround_front",
        image_name="正面",
    )

    assert urls
    assert character.reference_images[0]["appearance_type"] == "turnaround_front"
    assert character.reference_images[0]["name"] == "正面"


@pytest.mark.asyncio
async def test_regenerate_scene_image_records_state_type(monkeypatch):
    engine = assets_engine_module.AssetsEngine()
    scene = SceneLocation(
        id=8,
        project_id=1,
        name="公司会议室",
        description="高压会议现场",
        reference_images=[],
    )

    async def generate(**kwargs):
        return None

    monkeypatch.setattr(assets_engine_module.ai_hub.image, "generate", generate)

    urls = await engine.regenerate_scene_image(
        scene=scene,
        project_id=1,
        prompt="night meeting room",
        state_type="night",
        image_name="夜晚",
    )

    assert urls
    assert scene.reference_images[0]["state_type"] == "night"
    assert scene.reference_images[0]["name"] == "夜晚"


@pytest.mark.asyncio
async def test_split_storyboard_repairs_truncated_json_once(monkeypatch):
    engine = VideoEngine()
    episode = Episode(id=12, script_id=1, number=12, title="公寓清晨", content="林砚在公寓中唤醒苏远的记忆体。")
    characters = [
        Character(id=1, project_id=1, name="林砚", role=CharacterRole.PROTAGONIST, description="首席架构师"),
    ]
    scenes = [
        SceneLocation(id=1, project_id=1, name="林砚的公寓", description="清晨的智能公寓", time_of_day="dawn", interior=True),
    ]
    truncated = """{
  "segments": [
    {
      "title": "公寓清晨：记忆体苏醒",
      "shots": [
        {
          "duration": 8,
          "time_of_day": "dawn",
          "scene_ref": "@林砚的公寓",
          "camera_type": "full",
          "camera_angle": "eye_level",
          "camera_movement": "static",
          "characters": [{"name": "@林砚", "action": "站在窗边"}],
          "dialogue": "苏远，你听得到吗？",
          "voice_style": "清晨室内轻微回声",
          "background": "清晨公寓冷光笼罩，窗外城市苏醒",
"""
    fixed = {
        "segments": [
            {
                "title": "公寓清晨：记忆体苏醒",
                "shots": [
                    {
                        "duration": 8,
                        "time_of_day": "dawn",
                        "scene_ref": "@林砚的公寓",
                        "camera_type": "full",
                        "camera_angle": "eye_level",
                        "camera_movement": "static",
                        "characters": [{"name": "@林砚", "action": "站在窗边"}],
                        "dialogue": "苏远，你听得到吗？",
                        "voice_style": "清晨室内轻微回声",
                        "background": "清晨公寓冷光笼罩，窗外城市苏醒",
                        "transition": "cut",
                    },
                ],
            },
        ],
    }
    calls = []

    async def complete(**kwargs):
        calls.append(kwargs)
        return _chat_text_response(truncated if len(calls) == 1 else json.dumps(fixed, ensure_ascii=False))

    monkeypatch.setattr(video_engine_module.ai_hub.chat, "complete", complete)

    result = await engine.split_storyboard(episode, characters, scenes)

    assert len(calls) == 2
    assert result[0]["shots"][0]["scene_ref"] == "林砚的公寓"
    assert result[0]["shots"][0]["characters"][0]["char_id"] == 1
