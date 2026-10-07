from __future__ import annotations

import os
import sqlite3
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .providers.huggingface import HuggingFaceConfig, HuggingFaceProvider
from .providers.registry import ProviderRegistry
from .runtime.models import Job, JobStatus
from .runtime.queue import JobQueue
from .runtime.service import JobService
from .runtime.store import SQLiteJobStore


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
    error_code: str | None
    correlation_id: str
    attempt: int
    created_at: Any
    started_at: Any
    completed_at: Any
    duration_ms: float | None


def create_app(store_path: str | None = None) -> FastAPI:
    registry = ProviderRegistry()
    store = SQLiteJobStore(store_path or os.getenv("AI_MEDIA_HUB_DB", "data/runtime.db"))
    if os.getenv("HF_TOKEN", "").strip():
        registry.register(HuggingFaceProvider(HuggingFaceConfig.from_env()))

    service = JobService(registry, store)
    queue = JobQueue(store, service.execute)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await queue.start()
        yield
        await queue.stop()

    app = FastAPI(
        title="AI Media Hub",
        version="0.2.0",
        description="Production-oriented AI media orchestration runtime.",
        lifespan=lifespan,
    )

    @app.get("/health/live")
    async def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    async def readiness() -> dict[str, Any]:
        return {"status": "ready", "providers": await service.health()}

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "providers": await service.health()}

    @app.post("/jobs", response_model=JobResponse, status_code=202)
    async def create_job(
        request: CreateJobRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> JobResponse:
        if request.provider not in registry.names():
            raise HTTPException(
                status_code=503,
                detail=f"Provider '{request.provider}' is not configured.",
            )
        if request.operation != "chat":
            raise HTTPException(status_code=400, detail="MVP supports operation='chat' only.")

        if idempotency_key:
            existing = store.get_by_idempotency_key(idempotency_key)
            if existing:
                return JobResponse.model_validate(existing, from_attributes=True)

        job = Job(
            operation=request.operation,
            project_id=request.project_id,
            provider=request.provider,
            model=request.model,
            idempotency_key=idempotency_key,
            input={"messages": [m.model_dump() for m in request.messages]},
        )
        try:
            store.put(job)
        except sqlite3.IntegrityError as exc:
            if idempotency_key:
                existing = store.get_by_idempotency_key(idempotency_key)
                if existing:
                    return JobResponse.model_validate(existing, from_attributes=True)
            raise HTTPException(status_code=409, detail="Job could not be created.") from exc

        await queue.enqueue(job)
        return JobResponse.model_validate(job, from_attributes=True)

    @app.get("/jobs/{job_id}", response_model=JobResponse)
    async def get_job(job_id: UUID) -> JobResponse:
        job = store.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        return JobResponse.model_validate(job, from_attributes=True)

    return app


app = create_app()
