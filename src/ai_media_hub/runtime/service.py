from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..providers.base import ProviderError
from ..providers.registry import ProviderRegistry
from .models import Job, JobStatus
from .store import InMemoryJobStore


class JobService:
    def __init__(self, registry: ProviderRegistry, store: InMemoryJobStore) -> None:
        self.registry = registry
        self.store = store

    async def execute(self, job: Job) -> Job:
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        self.store.put(job)

        try:
            provider_name = job.provider or "huggingface"
            provider = self.registry.get(provider_name)
            job.provider = provider_name

            if job.operation == "chat":
                result = await provider.chat(
                    messages=job.input["messages"],
                    model=job.model,
                )
                job.output = {"text": result}
            else:
                raise ValueError(f"Unsupported operation: {job.operation}")

            job.status = JobStatus.SUCCEEDED
        except (ProviderError, ValueError, KeyError) as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = f"{type(exc).__name__}: {exc}"
        finally:
            job.completed_at = datetime.now(timezone.utc)
            self.store.put(job)

        return job

    async def health(self) -> dict[str, Any]:
        results = {}
        for name in self.registry.names():
            results[name] = (await self.registry.get(name).health()).__dict__
        return results
