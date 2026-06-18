import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from app.ai_hub.media_adapters import (
    MediaProviderSettings,
    OpenAICompatibleAdapter,
    ReplicateAdapter,
    get_media_adapter,
    _normalize_status,
    _task_or_asset_result,
)
from app.ai_hub.image import (
    ImageService,
    _is_chat_completions_image_model,
    _prompt_with_ratio_marker,
    _ratio_for_size,
)
from app.ai_hub._models import ImageResponse
from app.core.ai_config import (
    has_capability,
    normalize_api_base_url,
    normalize_capabilities,
)
from app.data.model_catalog import BUILTIN_CATALOG


class AIConfigTests(unittest.TestCase):
    def test_normalize_api_base_url_trims_and_ensures_v1(self):
        self.assertEqual(
            normalize_api_base_url(" https://api.laozhang.ai/v1 "),
            "https://api.laozhang.ai/v1",
        )
        self.assertEqual(
            normalize_api_base_url("https://api.deepseek.com/"),
            "https://api.deepseek.com/v1",
        )

    def test_capability_normalization(self):
        self.assertEqual(
            normalize_capabilities(" chat, image ,video ,, TTS "),
            "chat,image,video,tts",
        )
        self.assertTrue(has_capability("chat, image", "image"))

    def test_builtin_catalog_covers_image_and_video_provider_types(self):
        provider_types = {item["provider_type"] for item in BUILTIN_CATALOG}
        self.assertIn("openai_compatible", provider_types)
        self.assertIn("replicate", provider_types)
        self.assertIn("fal", provider_types)
        self.assertIn("runway", provider_types)
        self.assertIn("luma", provider_types)
        self.assertIn("dashscope", provider_types)

        capabilities = {
            model["capability"]
            for provider in BUILTIN_CATALOG
            for model in provider.get("models", [])
        }
        self.assertEqual(capabilities, {"image", "video"})

    def test_chat_completions_image_models(self):
        self.assertTrue(_is_chat_completions_image_model(" sora_image "))
        self.assertTrue(_is_chat_completions_image_model("gpt-4o-image"))
        self.assertFalse(_is_chat_completions_image_model("gpt-image-1-mini"))

    def test_sora_prompt_ratio_marker(self):
        self.assertEqual(_ratio_for_size("1024x1792"), "2:3")
        self.assertEqual(_ratio_for_size("1792x1024"), "3:2")
        self.assertEqual(_ratio_for_size("1024x1024"), "1:1")
        self.assertEqual(
            _prompt_with_ratio_marker("portrait", "1024x1792"),
            "portrait\u30102:3\u3011",
        )
        self.assertEqual(
            _prompt_with_ratio_marker("avatar[1:1]", "1024x1792"),
            "avatar[1:1]",
        )

    def test_media_adapter_registry_and_auth_headers(self):
        openai_adapter = get_media_adapter(
            MediaProviderSettings(
                provider_type="openai_compatible",
                auth_type="bearer",
                base_url="https://example.test/v1",
                api_key="sk-test",
            )
        )
        self.assertIsInstance(openai_adapter, OpenAICompatibleAdapter)
        self.assertEqual(openai_adapter._headers()["Authorization"], "Bearer sk-test")

        api_key_adapter = get_media_adapter(
            MediaProviderSettings(
                provider_type="replicate",
                auth_type="api-key",
                base_url="https://api.replicate.com/v1",
                api_key="token",
                config={"api_key_header": "X-Test-Key", "auth_prefix": "Key"},
            )
        )
        self.assertIsInstance(api_key_adapter, ReplicateAdapter)
        self.assertEqual(api_key_adapter._headers()["X-Test-Key"], "Key token")

    def test_media_status_and_asset_normalization(self):
        self.assertEqual(_normalize_status("completed"), "succeeded")
        self.assertEqual(_normalize_status("pending"), "queued")
        self.assertEqual(_normalize_status("processing"), "running")
        self.assertEqual(_normalize_status("canceled"), "cancelled")

        result = _task_or_asset_result(
            {
                "id": "task-1",
                "status": "processing",
                "output": ["https://cdn.example.test/out.mp4"],
            },
            "video",
        )
        self.assertEqual(result.status, "succeeded")
        self.assertEqual(result.provider_job_id, "task-1")
        self.assertEqual(result.assets[0]["url"], "https://cdn.example.test/out.mp4")


class ImageServiceRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_sora_image_uses_chat_endpoint_directly(self):
        service = ImageService()
        response = ImageResponse(image_path="out.png", model="sora_image")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = f"{tmp_dir}/out.png"
            with (
                patch.object(
                    service,
                    "_generate_chat",
                    new=AsyncMock(return_value=response),
                ) as generate_chat,
                patch.object(service, "_generate_b64", new=AsyncMock()) as generate_b64,
                patch.object(service, "_generate_url", new=AsyncMock()) as generate_url,
            ):
                result = await service.generate(
                    "portrait",
                    output_path,
                    model="sora_image",
                    size="1024x1792",
                )

        self.assertIs(result, response)
        generate_chat.assert_awaited_once()
        generate_b64.assert_not_called()
        generate_url.assert_not_called()


if __name__ == "__main__":
    unittest.main()
