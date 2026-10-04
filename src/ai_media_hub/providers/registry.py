from __future__ import annotations

from collections.abc import Iterable

from .base import MediaProvider


class ProviderRegistry:
    """Runtime registry used by the future Model Router."""

    def __init__(self, providers: Iterable[MediaProvider] = ()) -> None:
        self._providers = {provider.name: provider for provider in providers}

    def register(self, provider: MediaProvider) -> None:
        if provider.name in self._providers:
            raise ValueError(f"Provider already registered: {provider.name}")
        self._providers[provider.name] = provider

    def get(self, name: str) -> MediaProvider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise KeyError(f"Unknown provider: {name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))
