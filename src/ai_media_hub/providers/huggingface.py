from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, BinaryIO

from huggingface_hub import HfApi, InferenceClient

from .base import MediaProvider, ProviderCapabilities, ProviderError, ProviderHealth


@dataclass(frozen=True)
class HuggingFaceConfig:
    token: str
    provider: str = "auto"
    timeout_seconds: float = 120.0
    default_model: str | None = None
    bill_to: str | None = None

    @classmethod
    def from_env(cls) -> "HuggingFaceConfig":
        token = os.getenv("HF_TOKEN", "").strip()
        if not token:
            raise ValueError("HF_TOKEN is required to use Hugging Face.")
        return cls(
            token=token,
            provider=os.getenv("HF_PROVIDER", "auto").strip() or "auto",
            timeout_seconds=float(os.getenv("HF_TIMEOUT_SECONDS", "120")),
            default_model=os.getenv("HF_DEFAULT_MODEL", "").strip() or None,
            bill_to=os.getenv("HF_BILL_TO", "").strip() or None,
        )


class HuggingFaceProvider(MediaProvider):
    name = "huggingface"
    capabilities = ProviderCapabilities(
        chat=True, text_to_image=True, text_to_speech=True, speech_to_text=True
    )

    def __init__(self, config: HuggingFaceConfig, client: InferenceClient | None = None,
                 api: HfApi | None = None) -> None:
        self.config=config
        self._client=client or InferenceClient(provider=config.provider,token=config.token,
                                                timeout=config.timeout_seconds,bill_to=config.bill_to)
        self._api=api or HfApi(token=config.token)

    def _model(self, model: str | None) -> str | None:
        return model or self.config.default_model

    async def health(self) -> ProviderHealth:
        try:
            await asyncio.to_thread(self._api.whoami)
            return ProviderHealth(provider=self.name,healthy=True)
        except Exception as exc:
            return ProviderHealth(provider=self.name,healthy=False,
                                  detail=f"{type(exc).__name__}: {exc}")

    async def chat(self, *, messages: list[dict[str,Any]], model: str | None = None, **kwargs: Any) -> str:
        selected=self._model(model)
        if not selected:
            raise ProviderError("A Hugging Face model ID is required for chat.")
        try:
            response=await asyncio.to_thread(self._client.chat.completions.create,
                                             model=selected,messages=messages,**kwargs)
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise ProviderError(f"Hugging Face chat inference failed: {type(exc).__name__}: {exc}") from exc

    async def text_to_image(self, *, prompt: str, model: str | None = None, **kwargs: Any) -> Any:
        selected=self._model(model)
        if not selected:
            raise ProviderError("A Hugging Face model ID is required for image generation.")
        try:
            return await asyncio.to_thread(self._client.text_to_image,prompt=prompt,model=selected,**kwargs)
        except Exception as exc:
            raise ProviderError(f"Hugging Face image inference failed: {type(exc).__name__}: {exc}") from exc

    async def text_to_speech(self, *, text: str, model: str | None = None, **kwargs: Any) -> bytes:
        selected=self._model(model)
        if not selected:
            raise ProviderError("A Hugging Face model ID is required for text-to-speech.")
        try:
            return await asyncio.to_thread(self._client.text_to_speech,text=text,model=selected,**kwargs)
        except Exception as exc:
            raise ProviderError(f"Hugging Face TTS inference failed: {type(exc).__name__}: {exc}") from exc

    async def speech_to_text(self, *, audio: bytes | str | BinaryIO, model: str | None = None, **kwargs: Any) -> dict[str,Any]:
        try:
            response=await asyncio.to_thread(self._client.automatic_speech_recognition,
                                             audio=audio,model=self._model(model),**kwargs)
            return {"text":getattr(response,"text",str(response)),
                    "chunks":getattr(response,"chunks",None)}
        except Exception as exc:
            raise ProviderError(f"Hugging Face ASR inference failed: {type(exc).__name__}: {exc}") from exc
