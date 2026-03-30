"""
测试 AI Hub 图片生成 - 《挽救计划》洛基与格雷斯拥抱场景
"""
import asyncio
import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_hub import ai_hub


async def main():
    prompt = (
        "A cinematic movie scene from a sci-fi film: "
        "Two astronauts, Ryland Grace (a thin Caucasian man with short brown hair, "
        "wearing a worn space suit) and Rocky/Loki (a spider-like alien creature "
        "with five legs, rock-like exoskeleton, living in a high-temperature ammonia "
        "atmosphere inside a transparent xenonite enclosure), sharing an emotional "
        "embrace/touching moment. Rocky extends his claws gently touching Grace's "
        "space helmet. The setting is inside a spaceship with dim warm lighting, "
        "stars visible through the window. The mood is deeply emotional, a reunion "
        "of two friends who saved each other across the galaxy. "
        "Project Hail Mary movie style, highly detailed, cinematic lighting, "
        "8K quality, emotional, warm color tones, film grain."
    )

    output_path = "./storage/test_images/hail_mary_embrace.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print("=" * 60)
    print("🎬 DramaForge AI Hub - 图片生成测试")
    print("=" * 60)
    print(f"📝 主题: 《挽救计划》洛基与格雷斯拥抱")
    print(f"🤖 模型: sora-image")
    print(f"📐 尺寸: 1024x1792 (竖屏短剧)")
    print(f"💾 输出: {output_path}")
    print("-" * 60)
    print("⏳ 正在生成图片...")

    try:
        result = await ai_hub.image.generate(
            prompt=prompt,
            output_path=output_path,
        )
        print("-" * 60)
        print("✅ 图片生成成功！")
        print(f"   📁 文件路径: {result.image_path}")
        print(f"   🔗 图片URL:  {result.image_url or '(base64直存)'}")
        print(f"   🤖 使用模型: {result.model}")

        # 检查文件大小
        file_size = os.path.getsize(result.image_path)
        print(f"   📦 文件大小: {file_size / 1024:.1f} KB")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await ai_hub.close()


if __name__ == "__main__":
    asyncio.run(main())
