from __future__ import annotations

import asyncio
import os
from typing import Any
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .providers.huggingface import HuggingFaceConfig, HuggingFaceProvider
from .providers.registry import ProviderRegistry
from .runtime.models import Job, JobStatus
from .runtime.service import JobService
from .runtime.store import InMemoryJobStore


class ChatMessage(BaseModel):
    role: str
    content: str


class CreateJobRequest(BaseModel):
    operation: str = Field(default="chat")
    project_id: str = "default"
    provider: str = "huggingface"
    model: str | None = None
    messages: list[ChatMessage]


class JobResponse(BaseModel):
    id: UUID
    operation: str
    status: JobStatus
    project_id: str
    provider: str | None
    model: str | None
    output: dict[str, Any] | None
    error: str | None
    duration_ms: float | None


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Media Hub",
        version="0.1.0",
        description="Production-oriented AI media orchestration runtime.",
    )

    registry = ProviderRegistry()
    store = InMemoryJobStore()

    hf_token = os.getenv("HF_TOKEN", "").strip()
    if hf_token:
        registry.register(HuggingFaceProvider(HuggingFaceConfig.from_env()))

    service = JobService(registry, store)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "providers": await service.health(),
        }

    @app.post("/jobs", response_model=JobResponse, status_code=202)
    async def create_job(request: CreateJobRequest) -> JobResponse:
        if request.provider not in registry.names():
            raise HTTPException(
                status_code=503,
                detail=f"Provider '{request.provider}' is not configured. Set its credentials first.",
            )

        if request.operation != "chat":
            raise HTTPException(status_code=400, detail="MVP supports operation='chat' only.")

        job = Job(
            operation=request.operation,
            project_id=request.project_id,
            provider=request.provider,
            model=request.model,
            input={"messages": [m.model_dump() for m in request.messages]},
        )
        store.put(job)
        asyncio.create_task(service.execute(job))
        return JobResponse.model_validate(job, from_attributes=True)

    @app.get("/jobs/{job_id}", response_model=JobResponse)
    async def get_job(job_id: UUID) -> JobResponse:
        job = store.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        return JobResponse.model_validate(job, from_attributes=True)

    return app


app = create_app()
