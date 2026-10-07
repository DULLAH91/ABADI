import pytest
from fastapi.testclient import TestClient

from ai_media_hub.api import create_app


def test_health_without_provider_is_safe():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_job_requires_provider_credentials():
    client = TestClient(create_app())
    response = client.post(
        "/jobs",
        json={
            "operation": "chat",
            "messages":[{"role":"user","content":"hello"}],
        },
    )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_runtime_imports():
    app = create_app()
    assert app.title == "AI Media Hub"
