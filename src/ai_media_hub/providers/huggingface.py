from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from huggingface_hub import AsyncInferenceClient, HfApi

from .base import ModelProvider, ProviderRequest, ProviderResult


class HuggingFaceProvider(ModelProvider):
    """Hugging Face Hub and Inference Providers adapter."""

    name = "huggingface"

    def __init__(
        self,
        token: str | None = None,
        provider: str = "auto",
        client_factory: Callable[..., AsyncInferenceClient] = AsyncInferenceClient,
        api_factory: Callable[..., HfApi] = HfApi,
    ) -> None:
        self.token = token or os.getenv("HF_" + "TOKEN")
        self.provider = provider
        self._client_factory = client_factory
        self._api_factory = api_factory

    def _client(self, model: str) -> AsyncInferenceClient:
        return self._client_factory(
            model=model,
            provider=self.provider,
            api_key=self.token,
        )

    async def health(self) -> dict[str, Any]:
        if not self.token:
            return {"provider": self.name, "configured": False, "status": "missing_token"}
        return {
            "provider": self.name,
            "configured": True,
            "status": "ready",
            "provider_route": self.provider,
        }

    async def execute(self, request: ProviderRequest) -> ProviderResult:
        if not self.token:
            raise RuntimeError("Hugging Face access token is required for inference.")

        client = self._client(request.model)

        if request.task == "text.generation":
            messages = request.inputs.get("messages")
            prompt = request.inputs.get("prompt")
            if not messages and not prompt:
                raise ValueError("text.generation requires 'messages' or 'prompt'.")

            if messages:
                response = await client.chat.completions.create(
                    messages=messages,
                    **self._text_options(request.options),
                )
                output: Any = response.choices[0].message.content
            else:
                output = await client.text_generation(
                    prompt,
                    **self._text_options(request.options),
                )

        elif request.task == "image.generation":
            prompt = request.inputs.get("prompt")
            if not prompt:
                raise ValueError("image.generation requires 'prompt'.")
            output = await client.text_to_image(prompt, **self._image_options(request.options))

        else:
            raise ValueError(
                f"Unsupported Hugging Face task '{request.task}'. "
                "Add a dedicated mapping before exposing it through the router."
            )

        return ProviderResult(
            provider=self.name,
            model=request.model,
            task=request.task,
            output=output,
            metadata={"provider_route": self.provider},
        )

    @staticmethod
    def _text_options(options: dict[str, Any]) -> dict[str, Any]:
        allowed = {"max_tokens", "temperature", "top_p", "stream", "stop"}
        return {key: value for key, value in options.items() if key in allowed}

    @staticmethod
    def _image_options(options: dict[str, Any]) -> dict[str, Any]:
        allowed = {"num_inference_steps", "guidance_scale", "width", "height"}
        return {key: value for key, value in options.items() if key in allowed}

    async def model_info(self, model_id: str) -> dict[str, Any]:
        api = self._api_factory(token=self.token)
        info = api.model_info(model_id)
        return {
            "id": info.id,
            "pipeline_tag": getattr(info, "pipeline_tag", None),
            "library_name": getattr(info, "library_name", None),
            "license": getattr(info, "license", None),
            "sha": getattr(info, "sha", None),
            "private": getattr(info, "private", None),
        }
