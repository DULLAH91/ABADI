from __future__ import annotations

import hmac
import os
from dataclasses import dataclass

DEFAULT_ALLOWED_EXECUTABLES = frozenset({
    "python", "python.exe", "py", "py.exe",
    "git", "git.exe", "docker", "docker.exe",
    "nvidia-smi", "nvidia-smi.exe",
    "ffmpeg", "ffmpeg.exe", "magick", "magick.exe",
})


@dataclass(frozen=True)
class AgentSecurityPolicy:
    token: str
    mode: str = "restricted"
    allowed_executables: frozenset[str] = DEFAULT_ALLOWED_EXECUTABLES
    max_timeout_seconds: int = 1800
    allowed_working_roots: tuple[str, ...] = ()

    @classmethod
    def from_env(cls) -> "AgentSecurityPolicy":
        token = os.getenv("AI_MEDIA_HUB_AGENT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("AI_MEDIA_HUB_AGENT_TOKEN is required.")
        mode = os.getenv("AI_MEDIA_HUB_AGENT_MODE", "restricted").strip().lower()
        if mode not in {"restricted", "trusted"}:
            raise RuntimeError("AI_MEDIA_HUB_AGENT_MODE must be restricted or trusted.")
        raw = os.getenv("AI_MEDIA_HUB_ALLOWED_ROOTS", "").strip()
        roots = tuple(os.path.abspath(x.strip()) for x in raw.split(";") if x.strip())
        return cls(token=token, mode=mode, allowed_working_roots=roots)

    def authenticate(self, supplied_token: str) -> bool:
        return bool(supplied_token) and hmac.compare_digest(self.token, supplied_token)

    def validate(self, command: str, working_directory: str | None, timeout_seconds: int) -> None:
        if not 1 <= timeout_seconds <= self.max_timeout_seconds:
            raise PermissionError(
                f"timeout_seconds must be between 1 and {self.max_timeout_seconds}."
            )
        if working_directory and self.allowed_working_roots:
            directory = os.path.abspath(working_directory)
            allowed = any(
                directory == root or directory.startswith(root + os.sep)
                for root in self.allowed_working_roots
            )
            if not allowed:
                raise PermissionError("Working directory is outside the allowed roots.")
        if self.mode == "trusted":
            return
        executable = os.path.basename(command.strip().split(maxsplit=1)[0])
        if executable.lower() not in {x.lower() for x in self.allowed_executables}:
            raise PermissionError(
                f"Executable '{executable}' is not allowed in restricted mode."
            )
