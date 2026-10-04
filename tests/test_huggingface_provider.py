from __future__ import annotations

import pytest

from ai_media_hub.providers.base import ProviderRequest
from ai_media_hub.providers.huggingface import HuggingFaceProvider
from ai_media_hub.providers.registry import ProviderRegistry


class FakeCompletions:
    async def create(self, **kwargs):
        class Message:
            content = "hello from fake provider"

        class Choice:
            message = Message()

        class Response:
            choices = [Choice()]

        assert kwargs["messages"][0]["role"] == "user"
        return Response()


class FakeChat:
    completions = FakeCompletions()


class FakeClient:
    chat = FakeChat()

    async def text_generation(self, prompt, **kwargs):
        return f"generated: {prompt}"

    async def text_to_image(self, prompt, **kwargs):
        return {"prompt": prompt, "format": "fake-image"}


def fake_client_factory(**kwargs):
    return FakeClient()


@pytest.mark.asyncio
async def test_text_generation_is_normalized(monkeypatch):
    monkeypatch.setenv("HF_" + "TOKEN", "unit")
    provider = HuggingFaceProvider(client_factory=fake_client_factory)

    result = await provider.execute(
        ProviderRequest(
            task="text.generation",
            model="example/model",
            inputs={"messages": [{"role": "user", "content": "hello"}]},
        )
    )

    assert result.provider == "huggingface"
    assert result.output == "hello from fake provider"


@pytest.mark.asyncio
async def test_missing_token_is_explicit(monkeypatch):
    monkeypatch.delenv("HF_" + "TOKEN", raising=False)
    provider = HuggingFaceProvider()

    health = await provider.health()
    assert health["status"] == "missing_token"

    with pytest.raises(RuntimeError, match="access token"):
        await provider.execute(
            ProviderRequest(
                task="text.generation",
                model="example/model",
                inputs={"prompt": "hello"},
            )
        )


def test_registry_keeps_provider_boundary():
    registry = ProviderRegistry()
    provider = HuggingFaceProvider(token="unit")
    registry.register(provider)

    assert registry.names() == ("huggingface",)
    assert registry.get("huggingface") is provider
