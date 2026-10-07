from __future__ import annotations
import hmac, os, re
from dataclasses import dataclass
DEFAULT_ALLOWED_COMMAND_PATTERNS=(r"^nvidia-smi$",r"^nvidia-smis+-[A-Za-z0-9_-]+$",r"^python(?:.exe)? --version$",r"^py(?:.exe)? --version$",r"^git(?:.exe)? --version$",r"^git(?:.exe)? status$",r"^docker(?:.exe)? version$",r"^ffmpeg(?:.exe)? -version$")
SHELL_META=re.compile(r"(?:&&||||[&|<>;`$()]||
)")
@dataclass(frozen=True)
class AgentSecurityPolicy:
    token:str
    mode:str="restricted"
    allowed_command_patterns:tuple[str,...]=DEFAULT_ALLOWED_COMMAND_PATTERNS
    max_timeout_seconds:int=1800
    allowed_working_roots:tuple[str,...]=()
    @classmethod
    def from_env(cls):
        token=os.getenv("AI_MEDIA_HUB_AGENT_TOKEN","").strip()
        if not token: raise RuntimeError("AI_MEDIA_HUB_AGENT_TOKEN is required.")
        mode=os.getenv("AI_MEDIA_HUB_AGENT_MODE","restricted").strip().lower()
        if mode not in {"restricted","trusted"}: raise RuntimeError("AI_MEDIA_HUB_AGENT_MODE must be restricted or trusted.")
        raw=os.getenv("AI_MEDIA_HUB_ALLOWED_ROOTS","").strip()
        roots=tuple(os.path.abspath(x.strip()) for x in raw.split(";") if x.strip())
        if mode=="restricted" and not roots: roots=(os.getcwd(),)
        rawp=os.getenv("AI_MEDIA_HUB_ALLOWED_COMMAND_PATTERNS","").strip()
        patterns=tuple(x.strip() for x in rawp.split(";") if x.strip()) if rawp else DEFAULT_ALLOWED_COMMAND_PATTERNS
        return cls(token,mode,patterns,1800,roots)
    def authenticate(self,supplied_token:str)->bool: return bool(supplied_token) and hmac.compare_digest(self.token,supplied_token)
    def validate(self,command:str,working_directory:str|None,timeout_seconds:int)->None:
        if not 1<=timeout_seconds<=self.max_timeout_seconds: raise PermissionError(f"timeout_seconds must be between 1 and {self.max_timeout_seconds}.")
        if working_directory and self.allowed_working_roots:
            d=os.path.abspath(working_directory)
            if not any(d==r or d.startswith(r+os.sep) for r in self.allowed_working_roots): raise PermissionError("Working directory is outside the allowed roots.")
        if self.mode=="trusted": return
        if SHELL_META.search(command): raise PermissionError("Shell composition/operators are disabled in restricted mode.")
        if not any(re.fullmatch(p,command.strip(),flags=re.IGNORECASE) for p in self.allowed_command_patterns):
            raise PermissionError("Command is not allowed by the restricted execution policy.")
