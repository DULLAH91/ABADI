from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
class AuditLog:
    def __init__(self, path: str = "data/agent-audit.jsonl"):
        self.path, self._lock = Path(path), Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
    def record(self, event: str, **fields: Any) -> None:
        payload={"timestamp":datetime.now(timezone.utc).isoformat(),"event":event,**fields}
        with self._lock, self.path.open("a",encoding="utf-8") as f: f.write(json.dumps(payload,default=str)+"
")
