from __future__ import annotations

import asyncio
import json
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .execution import ExecutionNode, ExecutionNodeAdapter, ExecutionRequest, ExecutionResult


class WindowsExecutionAgentError(RuntimeError):
    pass


class WindowsExecutionAgent:
    """Authenticated Windows execution service with explicit policy and audit."""

    def __init__(
        self,
        node: ExecutionNode,
        *,
        token: str,
        allowed_command_patterns: tuple[str, ...],
        audit_log: str | None = None,
    ) -> None:
        if not token:
            raise ValueError("AI_MEDIA_HUB_NODE_TOKEN must be configured.")
        self.node = node
        self.token = token
        self.allowed_command_patterns = tuple(
            re.compile(pattern, re.IGNORECASE)
            for pattern in allowed_command_patterns
        )
        self.audit_log = Path(audit_log) if audit_log else None

    def _command_allowed(self, command: str) -> bool:
        return any(
            pattern.fullmatch(command.strip())
            for pattern in self.allowed_command_patterns
        )

    def _audit(self, event: str, request: ExecutionRequest, **extra: Any) -> None:
        if not self.audit_log:
            return
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "event": event,
            "request_id": str(request.request_id),
            "node_id": request.node_id,
            "operation": request.operation,
            "command": request.command,
            "timestamp": time.time(),
            **extra,
        }
        with self.audit_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if request.node_id != self.node.id:
            raise WindowsExecutionAgentError("Node identity mismatch.")

        if request.operation != "shell":
            self._audit("rejected", request, reason="unsupported_operation")
            raise WindowsExecutionAgentError(
                f"Unsupported operation: {request.operation}"
            )

        command = (request.command or "").strip()
        if not self._command_allowed(command):
            self._audit("rejected", request, reason="command_policy")
            raise WindowsExecutionAgentError("Command rejected by node policy.")

        self._audit("accepted", request)
        started = time.perf_counter()
        completed = await asyncio.create_subprocess_shell(
            command,
            cwd=request.working_directory or None,
            env={**os.environ, **request.environment},
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                completed.communicate(), timeout=request.timeout_seconds
            )
        except asyncio.TimeoutError as exc:
            completed.kill()
            await completed.wait()
            self._audit("timeout", request)
            raise WindowsExecutionAgentError("Command timed out.") from exc

        duration_ms = (time.perf_counter() - started) * 1000
        self._audit(
            "completed",
            request,
            exit_code=completed.returncode,
            duration_ms=duration_ms,
        )
        return ExecutionResult(
            request_id=request.request_id,
            node_id=self.node.id,
            exit_code=completed.returncode,
            stdout=stdout.decode(errors="replace"),
            stderr=stderr.decode(errors="replace"),
            duration_ms=duration_ms,
        )

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "node": {
                "id": self.node.id,
                "name": self.node.name,
                "platform": self.node.platform,
                "capabilities": sorted(c.value for c in self.node.capabilities),
                "labels": self.node.labels,
            },
        }


class WindowsExecutionAdapter(ExecutionNodeAdapter):
    """Runtime transport adapter for an authenticated Windows agent."""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    async def get_node(self, node_id: str) -> ExecutionNode:
        payload = await asyncio.to_thread(self._request, "GET", "/v1/node", None)
        node = payload["node"]
        if node["id"] != node_id:
            raise WindowsExecutionAgentError("Unexpected execution node identity.")
        return ExecutionNode(
            id=node["id"],
            name=node["name"],
            platform=node["platform"],
            capabilities=frozenset(node["capabilities"]),
            labels=node.get("labels", {}),
        )

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        payload = await asyncio.to_thread(
            self._request,
            "POST",
            "/v1/execute",
            {
                "node_id": request.node_id,
                "operation": request.operation,
                "command": request.command,
                "working_directory": request.working_directory,
                "environment": request.environment,
                "timeout_seconds": request.timeout_seconds,
                "request_id": str(request.request_id),
            },
        )
        return ExecutionResult(
            request_id=request.request_id,
            node_id=payload["node_id"],
            exit_code=payload["exit_code"],
            stdout=payload.get("stdout", ""),
            stderr=payload.get("stderr", ""),
            duration_ms=payload.get("duration_ms"),
            artifacts=payload.get("artifacts", []),
        )

    def _request(
        self, method: str, path: str, body: dict[str, Any] | None
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
            with urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode())
        except (HTTPError, URLError, TimeoutError) as exc:
            raise WindowsExecutionAgentError(
                f"Windows execution agent request failed: {exc}"
            ) from exc
