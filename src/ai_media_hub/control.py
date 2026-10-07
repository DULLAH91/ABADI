from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from uuid import uuid4


class ControlPlaneError(RuntimeError):
    """Raised when the AI Media Hub control plane cannot complete a job."""


class ControlPlane:
    """Narrow control-plane facade over the execution node.

    This pilot keeps orchestration local and durable with SQLite. The transport
    remains the Execution Agent; Atomic Chat never receives raw shell access.
    """

    JOBS = {
        "gpu": ["nvidia-smi", "--query-gpu=name,memory.total,driver_version,utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
        "git": ["git", "status", "--short", "--branch"],
        "docker": ["docker", "version", "--format={{.Server.Version}}"],
        "ffmpeg": ["ffmpeg", "-version"],
    }

    def __init__(self) -> None:
        self.agent_url = os.getenv("AMH_AGENT_URL", "http://127.0.0.1:8765").rstrip("/")
        self.token = os.getenv("AMH_AGENT_TOKEN", "")
        self.workspace = Path(os.getenv("AMH_WORKSPACE", ".")).resolve()
        self.db_path = Path(os.getenv("AMH_CONTROL_DB", "./data/control-plane.sqlite3"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    started_at REAL,
                    finished_at REAL,
                    duration_ms REAL,
                    exit_code INTEGER,
                    artifact_path TEXT,
                    artifact_sha256 TEXT,
                    artifact_bytes INTEGER,
                    estimated_cost_usd REAL,
                    result_json TEXT NOT NULL
                )"""
            )

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"{self.agent_url}{path}", data=body, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ControlPlaneError(f"execution agent HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ControlPlaneError(f"execution agent unavailable: {exc.reason}") from exc

    def node_status(self) -> dict[str, Any]:
        return self._request("GET", "/v1/node")

    def run_probe(self, kind: str) -> dict[str, Any]:
        if kind not in self.JOBS:
            raise ControlPlaneError(f"Unsupported probe: {kind}")
        return self._run_job(kind, self.JOBS[kind])

    def produce_test_media(self, duration_seconds: int = 3) -> dict[str, Any]:
        if not 1 <= duration_seconds <= 10:
            raise ControlPlaneError("duration_seconds must be between 1 and 10")
        job_id = str(uuid4())
        artifact_dir = self.workspace / "artifacts"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        output = artifact_dir / f"amh-proof-{job_id}.mp4"
        argv = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"testsrc2=size=1280x720:rate=30:duration={duration_seconds}",
            "-c:v", "mpeg4",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output),
        ]
        return self._run_job("media", argv, job_id=job_id, artifact_path=output)

    def _run_job(
        self,
        kind: str,
        argv: list[str],
        *,
        job_id: str | None = None,
        artifact_path: Path | None = None,
    ) -> dict[str, Any]:
        job_id = job_id or str(uuid4())
        created = time.time()
        self._record(job_id, kind, "running", created, {"argv": argv})
        started = time.time()
        result = self._request(
            "POST",
            "/v1/execute",
            {
                "request_id": job_id,
                "operation": "exec",
                "argv": argv,
                "working_directory": str(self.workspace),
            },
        )
        finished = time.time()

        artifact_sha = None
        artifact_bytes = None
        if artifact_path and artifact_path.exists():
            data = artifact_path.read_bytes()
            artifact_sha = hashlib.sha256(data).hexdigest()
            artifact_bytes = len(data)

        rate = float(os.getenv("AMH_GPU_COST_PER_SECOND_USD", "0"))
        duration_ms = float(result.get("duration_ms", (finished - started) * 1000))
        estimated_cost = round((duration_ms / 1000) * rate, 6)
        status = "succeeded" if result.get("exit_code") == 0 else "failed"

        output = {
            "job_id": job_id,
            "kind": kind,
            "status": status,
            "node_id": result.get("node_id"),
            "exit_code": result.get("exit_code"),
            "duration_ms": duration_ms,
            "estimated_cost_usd": estimated_cost,
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "artifact": (
                {
                    "path": str(artifact_path),
                    "bytes": artifact_bytes,
                    "sha256": artifact_sha,
                }
                if artifact_path and artifact_path.exists()
                else None
            ),
            "telemetry": {
                "created_at": created,
                "started_at": started,
                "finished_at": finished,
            },
        }
        self._record(
            job_id,
            kind,
            status,
            created,
            output,
            started_at=started,
            finished_at=finished,
            duration_ms=duration_ms,
            exit_code=result.get("exit_code"),
            artifact_path=str(artifact_path) if artifact_path and artifact_path.exists() else None,
            artifact_sha256=artifact_sha,
            artifact_bytes=artifact_bytes,
            estimated_cost_usd=estimated_cost,
        )
        return output

    def _record(
        self,
        job_id: str,
        kind: str,
        status: str,
        created_at: float,
        result: dict[str, Any],
        *,
        started_at: float | None = None,
        finished_at: float | None = None,
        duration_ms: float | None = None,
        exit_code: int | None = None,
        artifact_path: str | None = None,
        artifact_sha256: str | None = None,
        artifact_bytes: int | None = None,
        estimated_cost_usd: float | None = None,
    ) -> None:
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                """INSERT OR REPLACE INTO jobs
                (job_id, kind, status, created_at, started_at, finished_at,
                 duration_ms, exit_code, artifact_path, artifact_sha256,
                 artifact_bytes, estimated_cost_usd, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    job_id, kind, status, created_at, started_at, finished_at,
                    duration_ms, exit_code, artifact_path, artifact_sha256,
                    artifact_bytes, estimated_cost_usd, json.dumps(result),
                ),
            )
