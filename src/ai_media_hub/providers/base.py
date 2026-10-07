from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderCapabilities:
    chat: bool = False
    text_to_image: bool = False
    text_to_speech: bool = False
    speech_to_text: bool = False


@dataclass(frozen=True)
class ProviderHealth:
    provider: str
    healthy: bool
    detail: str | None = None


class MediaProvider(Protocol):
    name: str
    capabilities: ProviderCapabilities
    async def health(self) -> ProviderHealth: ...


class ProviderError(RuntimeError):
    """Normalized provider failure for orchestration and retry logic."""
