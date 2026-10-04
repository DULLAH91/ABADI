from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class ProviderRequest:
    task: str
    model: str
    inputs: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderResult:
    provider: str
    model: str
    task: str
    output: Any
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelProvider(Protocol):
    name: str

    async def execute(self, request: ProviderRequest) -> ProviderResult:
        ...

    async def health(self) -> dict[str, Any]:
        ...
