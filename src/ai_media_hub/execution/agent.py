from __future__ import annotations

import json
import os
import platform
import secrets
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from uuid import uuid4

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_OUTPUT_BYTES = 1_000_000
DEFAULT_TIMEOUT = 300
MAX_TIMEOUT = 1800


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    return default if value is None else value.lower() in {"1", "true", "yes", "on"}


class ExecutionAgent:
    """Small Windows-friendly execution daemon."""

    def __init__(self) -> None:
        self.node_id = os.getenv("AMH_NODE_ID", f"windows-{platform.node().lower()}")
        self.node_name = os.getenv("AMH_NODE_NAME", platform.node())
        self.token = os.getenv("AMH_AGENT_TOKEN", "")
        self.allow_shell = _env_bool("AMH_ALLOW_SHELL", False)
        self.allowed_roots = [
            Path(p).resolve()
            for p in os.getenv("AMH_ALLOWED_ROOTS", "").split(";")
            if p.strip()
        ]
        self.audit_path = Path(os.getenv("AMH_AUDIT_PATH", "./data/execution-audit.jsonl"))
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

    def authenticate(self, supplied: str | None) -> bool:
        return bool(self.token) and bool(supplied) and secrets.compare_digest(supplied, self.token)

    def node_info(self) -> dict[str, Any]:
        gpu, _ = self._command([
            "nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"
        ], 10)
        return {
            "id": self.node_id,
            "name": self.node_name,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "capabilities": ["health", "exec", "gpu"],
            "gpu": gpu,
        }

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        request_id = str(payload.get("request_id") or uuid4())
        timeout = int(payload.get("timeout_seconds", DEFAULT_TIMEOUT))
        cwd = payload.get("working_directory")
        started = time.monotonic()

        if not 1 <= timeout <= MAX_TIMEOUT:
            raise ValueError(f"timeout_seconds must be between 1 and {MAX_TIMEOUT}")

        if payload.get("operation", "exec") != "exec":
            raise ValueError("Only operation='exec' is enabled by default.")

        argv = payload.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise ValueError("argv must be a non-empty string list.")

        executable = Path(argv[0]).name.lower()
        if executable in {"cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe"}:
            if not self.allow_shell:
                raise PermissionError("Shell interpreters are disabled by policy.")

        if cwd:
            cwd_path = Path(cwd).resolve()
            if self.allowed_roots and not self._inside_allowed_root(cwd_path):
                raise PermissionError("working_directory is outside allowed roots.")
            cwd = str(cwd_path)

        env = os.environ.copy()
        for key, value in (payload.get("environment") or {}).items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("environment must contain string key/value pairs.")
            if key.upper() in {"PATH", "PATHEXT", "SYSTEMROOT", "COMSPEC"}:
                raise PermissionError(f"Environment override '{key}' is not allowed.")
            env[key] = value

        completed = subprocess.run(
            argv, cwd=cwd, env=env, capture_output=True, text=True,
            timeout=timeout, shell=False, check=False
        )
        result = {
            "request_id": request_id,
            "node_id": self.node_id,
            "exit_code": completed.returncode,
            "stdout": completed.stdout[:MAX_OUTPUT_BYTES],
            "stderr": completed.stderr[:MAX_OUTPUT_BYTES],
            "duration_ms": round((time.monotonic() - started) * 1000, 2),
        }
        self._audit("execution.completed", {
            "request_id": request_id, "argv": argv,
            "exit_code": completed.returncode, "duration_ms": result["duration_ms"],
        })
        return result

    def _command(self, argv: list[str], timeout: int) -> tuple[str, int]:
        try:
            result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, shell=False)
            return result.stdout[:MAX_OUTPUT_BYTES], result.returncode
        except (OSError, subprocess.SubprocessError) as exc:
            return str(exc), 1

    def _inside_allowed_root(self, path: Path) -> bool:
        return any(path == root or root in path.parents for root in self.allowed_roots)

    def _audit(self, event: str, data: dict[str, Any]) -> None:
        record = {"ts": time.time(), "event": event, "node_id": self.node_id, **data}
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


class AgentHandler(BaseHTTPRequestHandler):
    server_version = "AI-Media-Hub-Agent/0.1"

    def _agent(self) -> ExecutionAgent:
        return self.server.agent  # type: ignore[attr-defined]

    def _auth(self) -> bool:
        header = self.headers.get("Authorization", "")
        supplied = header[7:] if header.startswith("Bearer ") else None
        return self._agent().authenticate(supplied)

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, {"status": "ok", "node": self._agent().node_info()})
            return
        if not self._auth():
            self._send(401, {"error": "unauthorized"})
            return
        if self.path == "/v1/node":
            self._send(200, self._agent().node_info())
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if not self._auth():
            self._send(401, {"error": "unauthorized"})
            return
        if self.path != "/v1/execute":
            self._send(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 2_000_000:
                raise ValueError("request body too large")
            payload = json.loads(self.rfile.read(length) or b"{}")
            self._send(200, self._agent().execute(payload))
        except subprocess.TimeoutExpired:
            self._send(408, {"error": "execution_timeout"})
        except PermissionError as exc:
            self._send(403, {"error": str(exc)})
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})
        except Exception as exc:
            self._send(500, {"error": f"{type(exc).__name__}: {exc}"})

    def log_message(self, format: str, *args: Any) -> None:
        return


def run() -> None:
    agent = ExecutionAgent()
    host = os.getenv("AMH_AGENT_HOST", DEFAULT_HOST)
    port = int(os.getenv("AMH_AGENT_PORT", str(DEFAULT_PORT)))
    if not agent.token:
        raise RuntimeError("AMH_AGENT_TOKEN must be configured.")
    server = ThreadingHTTPServer((host, port), AgentHandler)
    server.agent = agent  # type: ignore[attr-defined]
    print(f"AI Media Hub Execution Agent: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
