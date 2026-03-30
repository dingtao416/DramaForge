"""测试视频生成 - 多模型自动降级"""
import asyncio, sys, os, time
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.ai_hub import ai_hub

async def main():
    output_path = "./storage/test_videos/hail_mary_embrace.mp4"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    prompt = (
        "Cinematic sci-fi scene: Inside a dimly lit spaceship, an astronaut "
        "in a worn white space suit slowly approaches a transparent enclosure "
        "filled with glowing golden ammonia gas. Inside the enclosure, a rocky "
        "alien creature with a stone-like exoskeleton gently extends its claw "
        "towards the astronaut. The astronaut places his gloved hand against "
        "the glass, meeting the alien's claw. Warm golden light illuminates "
        "their faces. Dust particles float in the air. Camera slowly pushes in. "
        "Emotional, cinematic, film grain, warm color grading, 4K quality."
    )

    # Show fallback chain
    models = ai_hub.video.list_models()
    print("🎬 视频生成测试 (多模型自动降级)")
    print(f"   降级链: {' → '.join(models['fallback_chain'])}")
    print(f"   输出: {output_path}")
    print("⏳ 开始生成...\n")

    t0 = time.time()
    try:
        result = await ai_hub.video.generate(prompt=prompt, output_path=output_path)
        elapsed = time.time() - t0
        file_size = os.path.getsize(result.video_path)
        print(f"\n✅ 视频生成成功！")
        print(f"   📁 路径:   {result.video_path}")
        print(f"   🔗 URL:    {result.video_url}")
        print(f"   🤖 模型:   {result.model}")
        print(f"   ⏱️  耗时:  {elapsed:.1f}s")
        print(f"   📦 大小:   {file_size/1024:.1f} KB")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"\n❌ 全部模型失败 (耗时 {elapsed:.1f}s): {e}")
    finally:
        await ai_hub.close()

if __name__ == "__main__":
    asyncio.run(main())
