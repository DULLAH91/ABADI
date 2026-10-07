from __future__ import annotations

import json
import os
from typing import Awaitable, Callable

import uvicorn
from mcp.server.mcpserver import MCPServer

from ai_media_hub.mcp_server import mcp


class BearerAuthMiddleware:
    """Minimal bearer-token boundary for the mobile MCP endpoint."""

    def __init__(self, app: Callable, token: str) -> None:
        if not token:
            raise RuntimeError("AMH_MCP_HTTP_TOKEN is required")
        self.app = app
        self.token = token.encode("utf-8")

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.lower(): value
            for key, value in scope.get("headers", [])
        }
        expected = b"Bearer " + self.token
        if headers.get(b"authorization") != expected:
            body = json.dumps({"error": "unauthorized"}).encode("utf-8")
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                    (b"www-authenticate", b"Bearer"),
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return

        await self.app(scope, receive, send)


def create_app() -> Callable:
    token = os.getenv("AMH_MCP_HTTP_TOKEN", "")
    host = os.getenv("AMH_MCP_HTTP_HOST", "0.0.0.0")
    app = mcp.streamable_http_app(
        host=host,
        stateless_http=True,
        json_response=True,
        max_request_body_size=1_048_576,
    )
    return BearerAuthMiddleware(app, token)


def main() -> None:
    host = os.getenv("AMH_MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("AMH_MCP_HTTP_PORT", "8787"))
    uvicorn.run(create_app(), host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
