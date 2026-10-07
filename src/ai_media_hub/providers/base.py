from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderCapabilities:
    """Capabilities exposed by a media/model provider."""

    chat: bool = False
    text_to_image: bool = False
    text_to_speech: bool = False
    speech_to_text: bool = False


@dataclass(frozen=True)
class ProviderHealth:
    """Provider health result safe to expose to the control plane."""

    provider: str
    healthy: bool
    detail: str | None = None


class MediaProvider(Protocol):
    """Stable boundary between AI Media Hub and an external provider."""

    name: str
    capabilities: ProviderCapabilities

    async def health(self) -> ProviderHealth:
        ...


class ProviderError(RuntimeError):
    """Normalized provider failure for orchestration and retry logic."""
