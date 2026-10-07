import pytest

from ai_media_hub.mobile_mcp import BearerAuthMiddleware


def test_mobile_mcp_requires_token(monkeypatch):
    monkeypatch.delenv("AMH_MCP_HTTP_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="AMH_MCP_HTTP_TOKEN"):
        BearerAuthMiddleware(lambda *_: None, "")


@pytest.mark.asyncio
async def test_mobile_mcp_rejects_bad_token():
    called = False

    async def app(scope, receive, send):
        nonlocal called
        called = True

    middleware = BearerAuthMiddleware(app, "secret")
    messages = []

    async def send(message):
        messages.append(message)

    await middleware(
        {"type": "http", "headers": [(b"authorization", b"Bearer wrong")]},
        lambda: None,
        send,
    )

    assert called is False
    assert messages[0]["status"] == 401


@pytest.mark.asyncio
async def test_mobile_mcp_accepts_token():
    called = False

    async def app(scope, receive, send):
        nonlocal called
        called = True

    middleware = BearerAuthMiddleware(app, "secret")
    await middleware(
        {"type": "http", "headers": [(b"authorization", b"Bearer secret")]},
        lambda: None,
        lambda message: None,
    )

    assert called is True
