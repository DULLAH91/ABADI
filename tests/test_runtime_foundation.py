from pathlib import Path

import pytest

from ai_media_hub.runtime.models import Job, JobStatus
from ai_media_hub.runtime.store import SQLiteJobStore


def test_job_store_survives_reopen(tmp_path: Path):
    db = tmp_path / "runtime.db"
    first = SQLiteJobStore(db)
    job = Job(project_id="media")
    first.put(job)

    restored = SQLiteJobStore(db).get(job.id)
    assert restored is not None
    assert restored.project_id == "media"
    assert restored.status == JobStatus.QUEUED


def test_idempotency_lookup(tmp_path: Path):
    store = SQLiteJobStore(tmp_path / "runtime.db")
    job = Job(idempotency_key="request-123")
    store.put(job)

    restored = store.get_by_idempotency_key("request-123")
    assert restored is not None
    assert restored.id == job.id


@pytest.mark.asyncio
async def test_service_classifies_provider_errors(tmp_path: Path):
    from ai_media_hub.providers.base import ProviderError
    from ai_media_hub.runtime.service import JobService

    class Provider:
        name = "fake"
        capabilities = None

        async def chat(self, messages, model=None):
            raise ProviderError("provider unavailable")

        async def health(self):
            return None

    class Registry:
        def get(self, name):
            return Provider()

        def names(self):
            return ("fake",)

    store = SQLiteJobStore(tmp_path / "runtime.db")
    service = JobService(Registry(), store)
    job = Job(provider="fake", input={"messages": []})
    await service.execute(job)

    assert job.status == JobStatus.FAILED
    assert job.error_code == "PROVIDERERROR"
    assert job.attempt == 1
