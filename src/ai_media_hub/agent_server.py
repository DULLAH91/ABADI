from __future__ import annotations

import os
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .runtime.execution import ExecutionCapability, ExecutionNode, ExecutionRequest
from .runtime.windows_agent import WindowsExecutionAgent


class ExecuteRequest(BaseModel):
    node_id: str
    operation: str = "shell"
    command: str | None = None
    working_directory: str | None = None
    environment: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=300, ge=1, le=1800)
    request_id: str


def create_agent_app() -> FastAPI:
    token = os.getenv("AI_MEDIA_HUB_NODE_TOKEN", "").strip()
    node = ExecutionNode(
        id=os.getenv("AI_MEDIA_HUB_NODE_ID", "windows-rtx6000-01"),
        name=os.getenv("AI_MEDIA_HUB_NODE_NAME", "Windows RTX 6000"),
        platform="windows",
        capabilities=frozenset(
            {
                ExecutionCapability.SHELL,
                ExecutionCapability.FILESYSTEM,
                ExecutionCapability.PROCESS,
                ExecutionCapability.DOCKER,
                ExecutionCapability.GPU,
                ExecutionCapability.ARTIFACTS,
            }
        ),
        labels={"role": "execution", "gpu": "quadro-rtx-6000"},
    )
    patterns = tuple(
        value.strip()
        for value in os.getenv(
            "AI_MEDIA_HUB_ALLOWED_COMMANDS",
            r"nvidia-smi|python --version|git --version|docker version|ffmpeg -version",
        ).split("|")
        if value.strip()
    )
    agent = WindowsExecutionAgent(
        node,
        token=token,
        allowed_command_patterns=patterns,
    )

    app = FastAPI(
        title="AI Media Hub Windows Execution Agent",
        version="0.1.0",
    )

    def require_token(authorization: str | None = Header(default=None)) -> None:
        if not token:
            raise HTTPException(
                status_code=503, detail="Node token is not configured."
            )
        if authorization != f"Bearer {token}":
            raise HTTPException(status_code=401, detail="Unauthorized.")

    @app.get("/v1/node", dependencies=[Depends(require_token)])
    async def node_info() -> dict[str, Any]:
        return agent.health()

    @app.post("/v1/execute", dependencies=[Depends(require_token)])
    async def execute(payload: ExecuteRequest) -> dict[str, Any]:
        if payload.node_id != node.id:
            raise HTTPException(status_code=409, detail="Node identity mismatch.")
        request = ExecutionRequest(
            node_id=payload.node_id,
            operation=payload.operation,
            command=payload.command,
            working_directory=payload.working_directory,
            environment=payload.environment,
            timeout_seconds=payload.timeout_seconds,
        )
        try:
            result = await agent.execute(request)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "request_id": str(result.request_id),
            "node_id": result.node_id,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_ms": result.duration_ms,
            "artifacts": result.artifacts,
        }

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_agent_app()
