import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.ai_hub.media_adapters import (
    MediaProviderSettings,
    MediaRequest,
    OpenAICompatibleAdapter,
    ReplicateAdapter,
    TaskEndpointAdapter,
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
from app.api.v2.storyboard import (
    SegmentGenerateRequest,
    _video_generation_options,
)
from app.data.model_catalog import BUILTIN_CATALOG
from app.data.video_model_presets import effective_video_model_config, list_video_model_presets
from app.models.media_generation import MediaCapability, MediaJobStatus
from app.services.media_generation_service import MediaGenerationService


class CaptureOpenAICompatibleAdapter(OpenAICompatibleAdapter):
    def __init__(self, config=None):
        super().__init__(
            MediaProviderSettings(
                provider_type="openai_compatible",
                base_url="https://example.test/v1",
                config=config or {},
            )
        )
        self.payload = None

    async def _post(self, path, payload):
        self.payload = payload
        return {"id": "task-1", "status": "queued"}


class CaptureTaskEndpointAdapter(TaskEndpointAdapter):
    def __init__(self, config=None):
        super().__init__(
            MediaProviderSettings(
                provider_type="runway",
                base_url="https://example.test",
                config=config or {},
            )
        )
        self.payload = None

    async def _post(self, path, payload):
        self.payload = payload
        return {"id": "task-1", "status": "queued"}


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

    def test_builtin_catalog_covers_chat_image_and_video_provider_types(self):
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
        self.assertEqual(capabilities, {"chat", "image", "video"})

    def test_builtin_video_catalog_models_resolve_effective_preset_capabilities(self):
        video_models = [
            (provider["provider_type"], model)
            for provider in BUILTIN_CATALOG
            for model in provider.get("models", [])
            if model["capability"] == "video"
        ]
        self.assertTrue(video_models)

        for provider_type, model in video_models:
            effective = effective_video_model_config(
                model_id=model["model_id"],
                provider_type=provider_type,
                default_params_json=model.get("default_params_json", {}),
                capabilities_json=model.get("capabilities_json", {}),
                param_schema_json=model.get("param_schema_json", {}),
            )
            self.assertIsNotNone(effective["preset_id"])

        sora_model = next(model for provider_type, model in video_models if model["model_id"] == "sora-2")
        sora_effective = effective_video_model_config(
            model_id=sora_model["model_id"],
            provider_type="openai_native",
            default_params_json=sora_model.get("default_params_json", {}),
            capabilities_json=sora_model.get("capabilities_json", {}),
            param_schema_json=sora_model.get("param_schema_json", {}),
        )
        self.assertEqual(sora_effective["effective_default_params_json"]["size"], "720x1280")
        self.assertEqual(sora_effective["effective_capabilities_json"]["video_size_param"], "size")

    def test_video_model_presets_are_available_for_settings_ui(self):
        presets = list_video_model_presets()
        preset_ids = {preset["preset_id"] for preset in presets}
        self.assertIn("openai/sora-2", preset_ids)
        self.assertIn("openai/sora-2-pro", preset_ids)
        self.assertIn("runway/gen4_turbo", preset_ids)

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


class OpenAICompatibleVideoPayloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_sora_video_payload_uses_size_seconds_and_drops_aspect_ratio(self):
        effective = effective_video_model_config(model_id="sora-2", provider_type="openai_native")
        adapter = CaptureOpenAICompatibleAdapter(
            config={"model_capabilities": effective["effective_capabilities_json"]}
        )

        await adapter.submit_video(
            MediaRequest(
                prompt="test",
                model_id="sora-2",
                size="720x1280",
                duration=5,
                aspect_ratio="9:16",
                first_frame="https://cdn.example.test/frame.png",
                raw_params={"aspect_ratio": "9:16", "duration": 5, "size": "720x1280"},
            )
        )

        self.assertNotIn("aspect_ratio", adapter.payload)
        self.assertEqual(adapter.payload["size"], "720x1280")
        self.assertEqual(adapter.payload["seconds"], "8")
        self.assertEqual(adapter.payload["input_reference"], {"image_url": "https://cdn.example.test/frame.png"})

    async def test_sora_2_pro_supports_1080p_size(self):
        effective = effective_video_model_config(model_id="sora-2-pro", provider_type="openai_native")
        adapter = CaptureOpenAICompatibleAdapter(
            config={"model_capabilities": effective["effective_capabilities_json"]}
        )

        await adapter.submit_video(
            MediaRequest(
                prompt="test",
                model_id="sora-2-pro",
                size="1920x1080",
                duration=20,
            )
        )

        self.assertEqual(adapter.payload["size"], "1920x1080")
        self.assertEqual(adapter.payload["seconds"], "20")

    async def test_sora_2_does_not_accept_sora_2_pro_only_size(self):
        effective = effective_video_model_config(model_id="sora-2", provider_type="openai_native")
        adapter = CaptureOpenAICompatibleAdapter(
            config={"model_capabilities": effective["effective_capabilities_json"]}
        )

        await adapter.submit_video(
            MediaRequest(
                prompt="test",
                model_id="sora-2",
                size="1920x1080",
                duration=8,
            )
        )

        self.assertNotIn("size", adapter.payload)
        self.assertEqual(adapter.payload["seconds"], "8")

    async def test_sora_2_character_does_not_match_sora_2_preset_by_prefix(self):
        effective = effective_video_model_config(model_id="sora-2-character", provider_type="openai_compatible")
        adapter = CaptureOpenAICompatibleAdapter(
            config={"model_capabilities": effective["effective_capabilities_json"]}
        )

        await adapter.submit_video(
            MediaRequest(
                prompt="test",
                model_id="sora-2-character",
                size="720x1280",
                duration=8,
                aspect_ratio="9:16",
            )
        )

        self.assertIsNone(effective["preset_id"])
        self.assertEqual(adapter.payload, {"model": "sora-2-character", "prompt": "test"})

    async def test_unknown_video_payload_drops_optional_controls_by_default(self):
        adapter = CaptureOpenAICompatibleAdapter()

        await adapter.submit_video(
            MediaRequest(
                prompt="test",
                model_id="custom-video",
                size="720x1280",
                duration=5,
                aspect_ratio="9:16",
                first_frame="https://cdn.example.test/frame.png",
                reference_images=["https://cdn.example.test/ref.png"],
                raw_params={
                    "foo": "bar",
                    "size": "720x1280",
                    "seconds": "5",
                    "aspect_ratio": "9:16",
                    "reference_images": ["https://cdn.example.test/ref.png"],
                },
            )
        )

        self.assertEqual(adapter.payload, {"model": "custom-video", "prompt": "test", "foo": "bar"})

    async def test_video_payload_can_opt_in_to_aspect_ratio_param(self):
        adapter = CaptureOpenAICompatibleAdapter(
            config={
                "model_capabilities": {
                    "video_size": True,
                    "video_size_param": "resolution",
                    "video_duration": True,
                    "video_duration_param": "duration",
                    "video_aspect_ratio": True,
                    "video_aspect_ratio_param": "ratio",
                    "video_first_frame": True,
                    "video_multi_reference": True,
                }
            }
        )

        await adapter.submit_video(
            MediaRequest(
                prompt="test",
                model_id="custom-video",
                size="1280x720",
                duration=6,
                aspect_ratio="16:9",
                first_frame="https://cdn.example.test/frame.png",
                reference_images=["https://cdn.example.test/ref.png"],
                raw_params={"aspect_ratio": "16:9"},
            )
        )

        self.assertNotIn("aspect_ratio", adapter.payload)
        self.assertEqual(adapter.payload["resolution"], "1280x720")
        self.assertEqual(adapter.payload["duration"], "6")
        self.assertEqual(adapter.payload["ratio"], "16:9")
        self.assertEqual(adapter.payload["input_reference"], {"image_url": "https://cdn.example.test/frame.png"})
        self.assertEqual(adapter.payload["reference_images"], ["https://cdn.example.test/ref.png"])


class TaskEndpointPayloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_video_payload_uses_configured_param_names(self):
        adapter = CaptureTaskEndpointAdapter(
            config={
                "model_capabilities": {
                    "video_size": True,
                    "video_size_param": "resolution",
                    "video_duration": True,
                    "video_duration_param": "duration_seconds",
                    "video_aspect_ratio": True,
                    "video_aspect_ratio_param": "ratio",
                }
            }
        )

        await adapter.submit_video(
            MediaRequest(
                prompt="test",
                model_id="custom-video",
                size="1280x720",
                duration=6,
                aspect_ratio="16:9",
            )
        )

        self.assertEqual(adapter.payload["resolution"], "1280x720")
        self.assertEqual(adapter.payload["duration_seconds"], "6")
        self.assertEqual(adapter.payload["ratio"], "16:9")
        self.assertNotIn("size", adapter.payload)
        self.assertNotIn("duration", adapter.payload)
        self.assertNotIn("aspect_ratio", adapter.payload)

    async def test_image_payload_is_not_filtered_by_video_capabilities(self):
        adapter = CaptureTaskEndpointAdapter()

        await adapter.submit_image(
            MediaRequest(
                prompt="test",
                model_id="image-model",
                size="1024x1024",
                aspect_ratio="1:1",
                first_frame="https://cdn.example.test/input.png",
            )
        )

        self.assertEqual(adapter.payload["size"], "1024x1024")
        self.assertEqual(adapter.payload["aspect_ratio"], "1:1")
        self.assertEqual(adapter.payload["image_url"], "https://cdn.example.test/input.png")


class MediaGenerationCancellationTests(unittest.IsolatedAsyncioTestCase):
    async def test_image_job_commits_running_state_before_provider_call(self):
        service = MediaGenerationService()
        job = SimpleNamespace(
            id=7,
            user_id=1,
            capability=MediaCapability.IMAGE,
            provider_id=1,
            model_id="image-model",
            status=MediaJobStatus.QUEUED,
            progress=0,
            request_json={"prompt": "test", "_output_path": "out.png"},
            provider_job_id=None,
            response_json={},
            result_assets_json=[],
            error=None,
        )
        db = AsyncMock()
        db.refresh.return_value = None
        db.flush.return_value = None
        events = []

        async def record_commit():
            events.append("commit")

        db.commit.side_effect = record_commit
        resolved = SimpleNamespace(
            provider_id=1,
            model_id="image-model",
            provider_type="openai_compatible",
            auth_type="bearer",
            base_url="https://example.test/v1",
            api_key="sk-test",
            headers={},
            config={},
            capabilities={},
            raw_params={},
        )
        async def submit_image(_request):
            events.append("provider_call")
            return SimpleNamespace(
                provider_job_id="provider-1",
                response={},
                progress=100,
                status="succeeded",
                assets=[{"url": "https://cdn.example.test/out.png"}],
                error=None,
            )

        adapter = SimpleNamespace(submit_image=AsyncMock(side_effect=submit_image), download_result=AsyncMock())

        with patch("app.services.media_generation_service.get_media_adapter", return_value=adapter):
            await service.run_existing_job(db=db, job=job, resolved=resolved, output_path="out.png")

        first_commit_order = events.index("commit")
        provider_call_order = events.index("provider_call")
        self.assertLess(first_commit_order, provider_call_order)
        self.assertEqual(job.status, MediaJobStatus.SUCCEEDED)


class VideoGenerationOptionsTests(unittest.TestCase):
    def test_unknown_model_does_not_forward_user_size_or_aspect_ratio(self):
        resolved = SimpleNamespace(
            provider_type="openai_compatible",
            auth_type="bearer",
            headers={},
            config={},
            raw_params={},
            capabilities={},
            model_id="custom-video",
        )

        options = _video_generation_options(
            resolved,
            SegmentGenerateRequest(resolution="720x1280", aspect_ratio="9:16"),
        )

        self.assertNotIn("size", options)
        self.assertNotIn("aspect_ratio", options)

    def test_sora_preset_forwards_supported_size_but_not_aspect_ratio(self):
        effective = effective_video_model_config(model_id="sora-2", provider_type="openai_native")
        resolved = SimpleNamespace(
            provider_type="openai_native",
            auth_type="bearer",
            headers={},
            config={},
            raw_params=effective["effective_default_params_json"],
            capabilities=effective["effective_capabilities_json"],
            model_id="sora-2",
        )

        options = _video_generation_options(
            resolved,
            SegmentGenerateRequest(resolution="720x1280", aspect_ratio="9:16"),
        )

        self.assertEqual(options["size"], "720x1280")
        self.assertNotIn("aspect_ratio", options)

    def test_declared_model_capabilities_forward_supported_generation_controls(self):
        resolved = SimpleNamespace(
            provider_type="openai_compatible",
            auth_type="bearer",
            headers={},
            config={},
            raw_params={},
            capabilities={
                "video_size": True,
                "video_supported_sizes": ["720x1280"],
                "video_aspect_ratio": True,
            },
            model_id="custom-video",
        )

        options = _video_generation_options(
            resolved,
            SegmentGenerateRequest(resolution="720x1280", aspect_ratio="9:16"),
        )

        self.assertEqual(options["size"], "720x1280")
        self.assertEqual(options["aspect_ratio"], "9:16")


if __name__ == "__main__":
    unittest.main()
