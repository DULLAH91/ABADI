from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class Job:
    id: UUID = field(default_factory=uuid4)
    operation: str = "chat"
    status: JobStatus = JobStatus.QUEUED
    project_id: str = "default"
    model: str | None = None
    input: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None
    provider: str | None = None
    idempotency_key: str | None = None
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    attempt: int = 0
    max_attempts: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cost_actual: float | None = None

    @property
    def duration_ms(self) -> float | None:
        if not self.started_at or not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds() * 1000
