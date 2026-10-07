from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from ..runtime.execution import ExecutionNode, ExecutionNodeAdapter, ExecutionRequest, ExecutionResult


class ExecutionTransportError(RuntimeError):
    """Normalized transport failure for runtime retry/classification."""


class HttpExecutionNodeAdapter(ExecutionNodeAdapter):
    """Authenticated HTTP transport for an AI Media Hub execution agent."""

    def __init__(self, base_url: str, token: str, *, timeout_seconds: float = 15) -> None:
        if not base_url:
            raise ValueError("base_url is required")
        if not token:
            raise ValueError("token is required")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds

    async def get_node(self, node_id: str) -> ExecutionNode:
        payload = await asyncio.to_thread(self._request, "GET", "/v1/node", None)
        if payload["id"] != node_id:
            raise ExecutionTransportError("Execution node identity mismatch.")
        return ExecutionNode(
            id=payload["id"],
            name=payload["name"],
            platform=payload["platform"],
            capabilities=frozenset(payload["capabilities"]),
            labels=payload.get("labels", {}),
        )

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        payload = await asyncio.to_thread(
            self._request,
            "POST",
            "/v1/execute",
            {
                "operation": request.operation,
                "command": request.command,
                "working_directory": request.working_directory,
                "environment": request.environment,
                "timeout_seconds": request.timeout_seconds,
                "request_id": str(request.request_id),
            },
        )
        returned_id = UUID(payload["request_id"])
        if returned_id != request.request_id:
            raise ExecutionTransportError("Execution request identity mismatch.")
        return ExecutionResult(
            request_id=returned_id,
            node_id=payload["node_id"],
            exit_code=payload["exit_code"],
            stdout=payload.get("stdout", ""),
            stderr=payload.get("stderr", ""),
            duration_ms=payload.get("duration_ms"),
            artifacts=payload.get("artifacts", []),
        )

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        data = json.dumps(body).encode() if body is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode())
        except HTTPError as exc:
            raise ExecutionTransportError(
                f"Execution agent returned HTTP {exc.code}."
            ) from exc
        except (URLError, TimeoutError) as exc:
            raise ExecutionTransportError(
                f"Execution agent transport failed: {exc}"
            ) from exc
