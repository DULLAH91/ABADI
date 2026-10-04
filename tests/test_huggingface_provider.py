from types import SimpleNamespace

import pytest

from ai_media_hub.providers.base import ProviderError
from ai_media_hub.providers.huggingface import HuggingFaceConfig, HuggingFaceProvider
from ai_media_hub.providers.registry import ProviderRegistry


class FakeAPI:
    def whoami(self):
        return {"name": "test-user"}


class FakeChat:
    class Completions:
        def create(self, **kwargs):
            assert kwargs["model"] == "test/model"
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="hello from hf"))]
            )

    completions = Completions()


class FakeClient:
    chat = FakeChat()

    def text_to_speech(self, **kwargs):
        assert kwargs["model"] == "test/tts"
        return b"audio"

    def text_to_image(self, **kwargs):
        assert kwargs["model"] == "test/image"
        return "image-object"

    def automatic_speech_recognition(self, **kwargs):
        assert kwargs["model"] == "test/asr"
        return SimpleNamespace(text="hello", chunks=[])


@pytest.fixture
def provider():
    config = HuggingFaceConfig(
        token="placeholder",
        provider="auto",
        default_model="test/model",
    )
    return HuggingFaceProvider(config, client=FakeClient(), api=FakeAPI())


@pytest.mark.asyncio
async def test_health_isolated_from_network(provider):
    health = await provider.health()
    assert health.healthy is True
    assert health.provider == "huggingface"


@pytest.mark.asyncio
async def test_chat_uses_adapter_boundary(provider):
    result = await provider.chat(messages=[{"role": "user", "content": "hello"}])
    assert result == "hello from hf"


@pytest.mark.asyncio
async def test_tts_image_and_asr(provider):
    assert await provider.text_to_speech(text="hello", model="test/tts") == b"audio"
    assert await provider.text_to_image(prompt="cat", model="test/image") == "image-object"
    assert await provider.speech_to_text(audio=b"audio", model="test/asr") == {
        "text": "hello",
        "chunks": [],
    }


@pytest.mark.asyncio
async def test_missing_model_fails_before_network(provider):
    provider.config = HuggingFaceConfig(token="placeholder", provider="auto")
    with pytest.raises(ProviderError):
        await provider.chat(messages=[{"role": "user", "content": "hello"}])


def test_registry():
    provider = HuggingFaceProvider(
        HuggingFaceConfig(token="placeholder"),
        client=FakeClient(),
        api=FakeAPI(),
    )
    registry = ProviderRegistry([provider])
    assert registry.names() == ("huggingface",)
    assert registry.get("huggingface") is provider
