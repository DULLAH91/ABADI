from __future__ import annotations

from threading import Lock
from uuid import UUID

from .models import Job


class InMemoryJobStore:
    """MVP store. Replace with PostgreSQL/MongoDB persistence behind this contract."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, Job] = {}
        self._lock = Lock()

    def put(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: UUID) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())
