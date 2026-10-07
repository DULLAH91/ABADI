from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID, uuid4


class ExecutionCapability(StrEnum):
    FILESYSTEM = "filesystem"
    SHELL = "shell"
    PROCESS = "process"
    DOCKER = "docker"
    GPU = "gpu"
    ARTIFACTS = "artifacts"


@dataclass(frozen=True)
class ExecutionNode:
    """Identity and advertised capabilities of a physical/virtual execution node."""

    id: str
    name: str
    platform: str
    capabilities: frozenset[ExecutionCapability] = frozenset()
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionRequest:
    """Provider-neutral command envelope sent to an execution node."""

    node_id: str
    operation: str
    command: str | None = None
    working_directory: str | None = None
    environment: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 300
    request_id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True)
class ExecutionResult:
    request_id: UUID
    node_id: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_ms: float | None = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)


class ExecutionPolicyError(ValueError):
    """Raised when an execution request violates node/runtime policy."""


class ExecutionNodeAdapter(Protocol):
    """Transport contract. HTTP, local agent, SSH, or another transport may implement it."""

    async def get_node(self, node_id: str) -> ExecutionNode: ...

    async def execute(self, request: ExecutionRequest) -> ExecutionResult: ...


def validate_execution_request(
    request: ExecutionRequest,
    node: ExecutionNode,
    *,
    allowed_operations: frozenset[str] = frozenset({"shell"}),
    max_timeout_seconds: int = 1800,
) -> None:
    """Apply runtime-side safety policy before a request crosses the transport boundary."""

    if request.node_id != node.id:
        raise ExecutionPolicyError("Execution node does not match the request.")

    if request.operation not in allowed_operations:
        raise ExecutionPolicyError(
            f"Operation '{request.operation}' is not allowed by runtime policy."
        )

    if request.operation == "shell" and ExecutionCapability.SHELL not in node.capabilities:
        raise ExecutionPolicyError("Execution node does not advertise shell capability.")

    if not 1 <= request.timeout_seconds <= max_timeout_seconds:
        raise ExecutionPolicyError(
            f"timeout_seconds must be between 1 and {max_timeout_seconds}."
        )

    if request.operation == "shell" and not request.command:
        raise ExecutionPolicyError("Shell execution requires a command.")
