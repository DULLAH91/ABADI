from __future__ import annotations

import asyncio
import os
import platform
import shutil
import time
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from ..runtime.execution import ExecutionCapability, ExecutionNode, ExecutionRequest, ExecutionResult
from .audit import AuditLog
from .security import AgentSecurityPolicy


class ExecutePayload(BaseModel):
    operation: str = Field(default="shell")
    command: str
    working_directory: str | None = None
    environment: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=300, ge=1, le=1800)


class AgentServer:
    def __init__(self, policy: AgentSecurityPolicy, audit: AuditLog | None = None) -> None:
        self.policy = policy
        self.audit = audit or AuditLog()
        self.node = self._build_node()

    def _build_node(self) -> ExecutionNode:
        capabilities = {
            ExecutionCapability.SHELL,
            ExecutionCapability.FILESYSTEM,
            ExecutionCapability.PROCESS,
            ExecutionCapability.ARTIFACTS,
        }
        if shutil.which("docker"):
            capabilities.add(ExecutionCapability.DOCKER)
        if shutil.which("nvidia-smi"):
            capabilities.add(ExecutionCapability.GPU)
        return ExecutionNode(
            id=os.getenv("AI_MEDIA_HUB_NODE_ID", platform.node()).strip(),
            name=os.getenv("AI_MEDIA_HUB_NODE_NAME", platform.node()).strip(),
            platform=platform.system().lower(),
            capabilities=frozenset(capabilities),
            labels={"hostname": platform.node(), "architecture": platform.machine()},
        )

    def authenticate(self, authorization: str | None) -> None:
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not self.policy.authenticate(token):
            raise HTTPException(status_code=401, detail="Unauthorized.")

    async def execute(self, payload: ExecutePayload) -> ExecutionResult:
        if payload.operation != "shell":
            raise HTTPException(status_code=400, detail="Only shell operation is enabled.")
        try:
            self.policy.validate(payload.command, payload.working_directory, payload.timeout_seconds)
        except PermissionError as exc:
            self.audit.record("execution_denied", command=payload.command, reason=str(exc))
            raise HTTPException(status_code=403, detail=str(exc)) from exc

        request = ExecutionRequest(
            node_id=self.node.id,
            operation=payload.operation,
            command=payload.command,
            working_directory=payload.working_directory,
            environment=payload.environment,
            timeout_seconds=payload.timeout_seconds,
        )
        started = time.monotonic()
        self.audit.record(
            "execution_started",
            request_id=str(request.request_id),
            node_id=self.node.id,
            operation=request.operation,
            command=request.command,
        )
        env = os.environ.copy()
        env.update(payload.environment)
        env["AI_MEDIA_HUB_REQUEST_ID"] = str(request.request_id)

        try:
            process = await asyncio.create_subprocess_shell(
                request.command,
                cwd=request.working_directory,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=request.timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                self.audit.record("execution_timeout", request_id=str(request.request_id))
                raise HTTPException(status_code=408, detail="Execution timed out.")

            result = ExecutionResult(
                request_id=request.request_id,
                node_id=self.node.id,
                exit_code=process.returncode or 0,
                stdout=stdout.decode(errors="replace"),
                stderr=stderr.decode(errors="replace"),
                duration_ms=(time.monotonic() - started) * 1000,
            )
            self.audit.record(
                "execution_completed",
                request_id=str(request.request_id),
                exit_code=result.exit_code,
                duration_ms=result.duration_ms,
            )
            return result
        except HTTPException:
            raise
        except Exception as exc:
            self.audit.record(
                "execution_error",
                request_id=str(request.request_id),
                error=type(exc).__name__,
            )
            raise HTTPException(status_code=500, detail="Execution failed.") from exc


def create_app() -> FastAPI:
    policy = AgentSecurityPolicy.from_env()
    agent = AgentServer(policy)
    app = FastAPI(
        title="AI Media Hub Execution Agent",
        version="0.2.0",
        description="Authenticated execution node for AI Media Hub.",
    )

    def auth(authorization: str | None = Header(default=None)) -> None:
        agent.authenticate(authorization)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "node": agent.node.id, "platform": agent.node.platform}

    @app.get("/v1/node", dependencies=[Depends(auth)])
    async def node() -> dict[str, Any]:
        return {
            "id": agent.node.id,
            "name": agent.node.name,
            "platform": agent.node.platform,
            "capabilities": sorted(c.value for c in agent.node.capabilities),
            "labels": agent.node.labels,
        }

    @app.post("/v1/execute", dependencies=[Depends(auth)])
    async def execute(payload: ExecutePayload) -> dict[str, Any]:
        result = await agent.execute(payload)
        return {
            "request_id": str(result.request_id),
            "node_id": result.node_id,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_ms": result.duration_ms,
            "artifacts": result.artifacts,
        }

    return app
