"""
测试 AI Hub 全链路 - 基于《挽救计划》洛基与格雷斯拥抱场景
1. LLM: 为图片生成旁白文案
2. TTS: 将旁白转为语音
3. Video: 用 Sora 2 生成对应视频片段
"""
import asyncio
import sys
import os
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_hub import ai_hub


def fmt_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{int(seconds//60)}m{seconds%60:.1f}s"


async def test_llm_narration():
    """Step 1: 用 LLM 为场景生成旁白"""
    print("\n" + "=" * 60)
    print("📝 Step 1/3: LLM 生成旁白文案")
    print("=" * 60)

    t0 = time.time()
    narration = await ai_hub.chat.ask(
        prompt=(
            "你是一位专业的短剧旁白撰写者。请为以下电影场景写一段30-50字的中文旁白，"
            "要求：深情、有画面感、适合短视频配音。\n\n"
            "场景：《挽救计划》(Project Hail Mary) 中，宇航员格雷斯与外星生物洛基"
            "在飞船中重逢。洛基隔着氙晶石隔舱，伸出岩石般的爪子温柔触碰格雷斯的头盔。"
            "两个来自不同星球的朋友，跨越银河拯救了彼此的世界。这是他们最后的告别，"
            "也是最深的羁绊。\n\n"
            "只输出旁白文案本身，不要加任何标注。"
        ),
        system="你是专业短剧旁白作家，文字简洁有力，富有感情。",
        temperature=0.9,
        max_tokens=200,
    )

    elapsed = time.time() - t0
    print(f"⏱️  耗时: {fmt_time(elapsed)}")
    print(f"📄 旁白内容:\n")
    print(f"   「{narration.strip()}」\n")
    return narration.strip()


async def test_tts(narration: str):
    """Step 2: TTS 语音合成"""
    print("=" * 60)
    print("🔊 Step 2/3: TTS 语音合成")
    print("=" * 60)

    output_path = "./storage/test_audio/hail_mary_narration.mp3"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"   模型: tts-1-hd")
    print(f"   音色: nova (年轻女声)")
    print(f"   文本长度: {len(narration)} 字")
    print(f"   输出: {output_path}")
    print("-" * 60)
    print("⏳ 正在合成语音...")

    t0 = time.time()
    result = await ai_hub.tts.speak(
        text=narration,
        output_path=output_path,
        voice="nova",
    )
    elapsed = time.time() - t0

    file_size = os.path.getsize(result.audio_path)
    print(f"\n✅ TTS 合成成功！")
    print(f"   📁 文件路径: {result.audio_path}")
    print(f"   🎙️  音色: {result.voice}")
    print(f"   ⏱️  耗时: {fmt_time(elapsed)}")
    print(f"   📦 文件大小: {file_size / 1024:.1f} KB")
    print(f"   ⏳ 预估时长: {result.duration:.1f}s\n")
    return result


async def test_video():
    """Step 3: Sora 2 视频生成"""
    print("=" * 60)
    print("🎬 Step 3/3: Sora 2 视频生成")
    print("=" * 60)

    output_path = "./storage/test_videos/hail_mary_embrace.mp4"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    video_prompt = (
        "Cinematic sci-fi scene: Inside a dimly lit spaceship, an astronaut "
        "in a worn white space suit slowly approaches a transparent enclosure "
        "filled with glowing golden ammonia gas. Inside the enclosure, a rocky "
        "alien creature with a stone-like exoskeleton gently extends its claw "
        "towards the astronaut. The astronaut places his gloved hand against "
        "the glass, meeting the alien's claw. Warm golden light illuminates "
        "their faces. Dust particles float in the air. Camera slowly pushes in. "
        "Emotional, cinematic, film grain, warm color grading, 4K quality."
    )

    print(f"   模型: {os.environ.get('VIDEO_MODEL', 'sora-2')}")
    print(f"   模式: 异步 API")
    print(f"   输出: {output_path}")
    print(f"   Prompt 长度: {len(video_prompt)} chars")
    print("-" * 60)
    print("⏳ 正在提交视频生成任务...")

    t0 = time.time()
    try:
        result = await ai_hub.video.generate(
            prompt=video_prompt,
            output_path=output_path,
        )
        elapsed = time.time() - t0

        file_size = os.path.getsize(result.video_path)
        print(f"\n✅ 视频生成成功！")
        print(f"   📁 文件路径: {result.video_path}")
        print(f"   🔗 视频URL:  {result.video_url}")
        print(f"   🤖 使用模型: {result.model}")
        print(f"   📊 任务状态: {result.status}")
        print(f"   🆔 任务ID:   {result.task_id or 'N/A'}")
        print(f"   ⏱️  总耗时:  {fmt_time(elapsed)}")
        print(f"   📦 文件大小: {file_size / 1024:.1f} KB")
        return result

    except Exception as e:
        elapsed = time.time() - t0
        print(f"\n⚠️  视频生成异常 (耗时 {fmt_time(elapsed)}): {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    print("🚀" + "=" * 58)
    print("  DramaForge AI Hub - 全链路测试")
    print("  主题: 《挽救计划》洛基与格雷斯拥抱")
    print("=" * 60)

    total_t0 = time.time()

    # Step 1: LLM 生成旁白
    narration = await test_llm_narration()

    # Step 2: TTS 语音合成
    tts_result = await test_tts(narration)

    # Step 3: Sora 2 视频生成
    video_result = await test_video()

    # Summary
    total_elapsed = time.time() - total_t0
    print("\n" + "=" * 60)
    print("📊 全链路测试总结")
    print("=" * 60)
    print(f"   ✅ LLM 旁白:  「{narration[:30]}...」")
    print(f"   ✅ TTS 语音:  {tts_result.audio_path} ({tts_result.duration:.1f}s)")
    if video_result:
        print(f"   ✅ Sora 视频: {video_result.video_path}")
    else:
        print(f"   ⚠️  Sora 视频: 生成中/失败 (见上方日志)")
    print(f"   ⏱️  总耗时:   {fmt_time(total_elapsed)}")
    print(f"   🖼️  图片:     ./storage/test_images/hail_mary_embrace.png")
    print("=" * 60)

    await ai_hub.close()


if __name__ == "__main__":
    asyncio.run(main())
