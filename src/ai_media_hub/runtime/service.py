from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..providers.base import ProviderError
from ..providers.registry import ProviderRegistry
from .models import Job, JobStatus
from .store import SQLiteJobStore


class JobService:
    def __init__(self, registry: ProviderRegistry, store: SQLiteJobStore) -> None:
        self.registry=registry
        self.store=store

    async def execute(self, job: Job) -> Job:
        current=self.store.get(job.id)
        if current and current.status in {JobStatus.SUCCEEDED,JobStatus.FAILED}:
            return current
        job.status=JobStatus.RUNNING
        job.attempt+=1
        job.started_at=datetime.now(timezone.utc)
        self.store.put(job)
        try:
            provider_name=job.provider or "huggingface"
            provider=self.registry.get(provider_name)
            job.provider=provider_name
            if job.operation!="chat":
                raise ValueError(f"Unsupported operation: {job.operation}")
            result=await provider.chat(messages=job.input["messages"],model=job.model)
            job.output={"text":result}
            job.status=JobStatus.SUCCEEDED
        except (ProviderError,ValueError,KeyError) as exc:
            job.status=JobStatus.FAILED
            job.error_code=type(exc).__name__.upper()
            job.error=str(exc)
        except Exception as exc:
            job.status=JobStatus.FAILED
            job.error_code="UNEXPECTED_ERROR"
            job.error=f"{type(exc).__name__}: {exc}"
        finally:
            job.completed_at=datetime.now(timezone.utc)
            self.store.put(job)
        return job

    async def health(self) -> dict[str,Any]:
        return {name:(await self.registry.get(name).health()).__dict__ for name in self.registry.names()}
