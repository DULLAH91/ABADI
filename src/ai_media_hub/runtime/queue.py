from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from uuid import UUID

from .models import Job, JobStatus
from .store import SQLiteJobStore


class JobQueue:
    """Process-local dispatcher; SQLite remains the durable source of truth."""

    def __init__(self, store: SQLiteJobStore, execute: Callable[[Job], Awaitable[Job]]) -> None:
        self.store = store
        self._execute = execute
        self._queue: asyncio.Queue[UUID] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None

    async def start(self) -> None:
        for job in self.store.list_by_status(JobStatus.QUEUED):
            await self._queue.put(job.id)
        self._worker = asyncio.create_task(self._run(), name="ai-media-hub-worker")

    async def stop(self) -> None:
        if self._worker:
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass
            self._worker = None

    async def enqueue(self, job: Job) -> None:
        await self._queue.put(job.id)

    async def _run(self) -> None:
        while True:
            job_id = await self._queue.get()
            try:
                job = self.store.get(job_id)
                if job and job.status == JobStatus.QUEUED:
                    await self._execute(job)
            finally:
                self._queue.task_done()
