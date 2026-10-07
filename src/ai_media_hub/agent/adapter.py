from __future__ import annotations
import asyncio, json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID
from ..runtime.execution import ExecutionNode, ExecutionNodeAdapter, ExecutionRequest, ExecutionResult

class ExecutionTransportError(RuntimeError): pass

class HttpExecutionNodeAdapter(ExecutionNodeAdapter):
    def __init__(self, base_url: str, token: str, *, timeout_seconds: float = 15):
        if not base_url or not token: raise ValueError("base_url and token are required")
        self.base_url, self.token, self.timeout_seconds = base_url.rstrip("/"), token, timeout_seconds

    async def get_node(self, node_id: str) -> ExecutionNode:
        p = await asyncio.to_thread(self._request, "GET", "/v1/node", None)
        if p["id"] != node_id: raise ExecutionTransportError("Execution node identity mismatch.")
        return ExecutionNode(id=p["id"], name=p["name"], platform=p["platform"],
                             capabilities=frozenset(p["capabilities"]), labels=p.get("labels", {}))

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        p = await asyncio.to_thread(self._request, "POST", "/v1/execute", {
            "operation": request.operation, "command": request.command,
            "working_directory": request.working_directory, "environment": request.environment,
            "timeout_seconds": request.timeout_seconds, "request_id": str(request.request_id)})
        returned = UUID(p["request_id"])
        if returned != request.request_id: raise ExecutionTransportError("Execution request identity mismatch.")
        return ExecutionResult(returned, p["node_id"], p["exit_code"], p.get("stdout",""),
                               p.get("stderr",""), p.get("duration_ms"), p.get("artifacts", []))

    def _request(self, method: str, path: str, body: dict[str, Any] | None) -> dict[str, Any]:
        req = Request(f"{self.base_url}{path}", data=json.dumps(body).encode() if body else None,
                      method=method, headers={"Authorization": f"Bearer {self.token}",
                      "Content-Type":"application/json","Accept":"application/json"})
        try:
            with urlopen(req, timeout=self.timeout_seconds) as r: return json.loads(r.read().decode())
        except HTTPError as e: raise ExecutionTransportError(f"Execution agent returned HTTP {e.code}.") from e
        except (URLError, TimeoutError) as e: raise ExecutionTransportError(f"Execution agent transport failed: {e}") from e
