from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock
from uuid import UUID

from .models import Job, JobStatus


class SQLiteJobStore:
    """Durable local job store; persistence remains behind a replaceable contract."""

    def __init__(self, path: str | Path = "data/runtime.db") -> None:
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, operation TEXT NOT NULL, status TEXT NOT NULL,
                project_id TEXT NOT NULL, model TEXT, input_json TEXT NOT NULL,
                output_json TEXT, error TEXT, error_code TEXT, provider TEXT,
                idempotency_key TEXT UNIQUE, correlation_id TEXT NOT NULL,
                attempt INTEGER NOT NULL, max_attempts INTEGER NOT NULL,
                created_at TEXT NOT NULL, started_at TEXT, completed_at TEXT,
                cost_actual REAL)""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_correlation ON jobs(correlation_id)")

    def put(self, job: Job) -> Job:
        with self._lock, self._connect() as db:
            db.execute("""INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET operation=excluded.operation,status=excluded.status,
                project_id=excluded.project_id,model=excluded.model,input_json=excluded.input_json,
                output_json=excluded.output_json,error=excluded.error,error_code=excluded.error_code,
                provider=excluded.provider,idempotency_key=excluded.idempotency_key,
                correlation_id=excluded.correlation_id,attempt=excluded.attempt,
                max_attempts=excluded.max_attempts,created_at=excluded.created_at,
                started_at=excluded.started_at,completed_at=excluded.completed_at,
                cost_actual=excluded.cost_actual""",
                (str(job.id),job.operation,job.status.value,job.project_id,job.model,
                 json.dumps(job.input),json.dumps(job.output) if job.output is not None else None,
                 job.error,job.error_code,job.provider,job.idempotency_key,job.correlation_id,
                 job.attempt,job.max_attempts,job.created_at.isoformat(),
                 job.started_at.isoformat() if job.started_at else None,
                 job.completed_at.isoformat() if job.completed_at else None,job.cost_actual))
        return job

    def get(self, job_id: UUID) -> Job | None:
        with self._lock, self._connect() as db:
            row=db.execute("SELECT * FROM jobs WHERE id=?",(str(job_id),)).fetchone()
        return self._from_row(row) if row else None

    def get_by_idempotency_key(self, key: str) -> Job | None:
        with self._lock, self._connect() as db:
            row=db.execute("SELECT * FROM jobs WHERE idempotency_key=?",(key,)).fetchone()
        return self._from_row(row) if row else None

    def list_by_status(self, status: JobStatus) -> list[Job]:
        with self._lock, self._connect() as db:
            rows=db.execute("SELECT * FROM jobs WHERE status=? ORDER BY created_at",(status.value,)).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Job:
        parse=lambda value: datetime.fromisoformat(value) if value else None
        return Job(id=UUID(row["id"]),operation=row["operation"],status=JobStatus(row["status"]),
            project_id=row["project_id"],model=row["model"],input=json.loads(row["input_json"]),
            output=json.loads(row["output_json"]) if row["output_json"] else None,error=row["error"],
            error_code=row["error_code"],provider=row["provider"],idempotency_key=row["idempotency_key"],
            correlation_id=row["correlation_id"],attempt=row["attempt"],max_attempts=row["max_attempts"],
            created_at=parse(row["created_at"]),started_at=parse(row["started_at"]),
            completed_at=parse(row["completed_at"]),cost_actual=row["cost_actual"])
