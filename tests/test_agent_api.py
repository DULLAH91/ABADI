from fastapi.testclient import TestClient
from ai_media_hub.agent.server import create_app
def test_authenticated_node_endpoint(monkeypatch):
    monkeypatch.setenv("AI_MEDIA_HUB_AGENT_TOKEN","test-secret")
    r=TestClient(create_app()).get("/v1/node",headers={"Authorization":"Bearer test-secret"})
    assert r.status_code==200 and "capabilities" in r.json()
def test_unauthenticated_node_endpoint(monkeypatch):
    monkeypatch.setenv("AI_MEDIA_HUB_AGENT_TOKEN","test-secret")
    assert TestClient(create_app()).get("/v1/node").status_code==401
