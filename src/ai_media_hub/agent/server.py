from __future__ import annotations
import asyncio, os, platform, shutil, time
from typing import Any
from uuid import UUID, uuid4
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from ..runtime.execution import ExecutionCapability, ExecutionNode, ExecutionRequest, ExecutionResult
from .audit import AuditLog
from .security import AgentSecurityPolicy
class ExecutePayload(BaseModel):
    operation:str=Field(default="shell")
    command:str
    working_directory:str|None=None
    environment:dict[str,str]=Field(default_factory=dict)
    timeout_seconds:int=Field(default=300,ge=1,le=1800)
    request_id:UUID|None=None
class AgentServer:
    def __init__(self,policy,audit=None): self.policy,self.audit,self.node=policy,audit or AuditLog(),self._build_node()
    def _build_node(self):
        caps={ExecutionCapability.SHELL,ExecutionCapability.FILESYSTEM,ExecutionCapability.PROCESS,ExecutionCapability.ARTIFACTS}
        if shutil.which("docker"): caps.add(ExecutionCapability.DOCKER)
        if shutil.which("nvidia-smi"): caps.add(ExecutionCapability.GPU)
        return ExecutionNode(os.getenv("AI_MEDIA_HUB_NODE_ID",platform.node()),os.getenv("AI_MEDIA_HUB_NODE_NAME",platform.node()),platform.system().lower(),frozenset(caps),{"hostname":platform.node(),"architecture":platform.machine()})
    def authenticate(self,authorization):
        scheme,_,token=(authorization or "").partition(" ")
        if scheme.lower()!="bearer" or not self.policy.authenticate(token): raise HTTPException(401,"Unauthorized.")
    async def execute(self,payload):
        if payload.operation!="shell": raise HTTPException(400,"Only shell operation is enabled.")
        try: self.policy.validate(payload.command,payload.working_directory,payload.timeout_seconds)
        except PermissionError as e:
            self.audit.record("execution_denied",command=payload.command,reason=str(e)); raise HTTPException(403,str(e)) from e
        req=ExecutionRequest(self.node.id,payload.operation,payload.command,payload.working_directory,payload.environment,payload.timeout_seconds,payload.request_id or uuid4())
        start=time.monotonic(); self.audit.record("execution_started",request_id=str(req.request_id),node_id=req.node_id,command=req.command)
        env=os.environ.copy(); env.update(payload.environment); env["AI_MEDIA_HUB_REQUEST_ID"]=str(req.request_id)
        try:
            p=await asyncio.create_subprocess_shell(req.command,cwd=req.working_directory,env=env,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
            try: out,err=await asyncio.wait_for(p.communicate(),timeout=req.timeout_seconds)
            except asyncio.TimeoutError:
                p.kill(); await p.communicate(); self.audit.record("execution_timeout",request_id=str(req.request_id)); raise HTTPException(408,"Execution timed out.")
            result=ExecutionResult(req.request_id,self.node.id,p.returncode or 0,out.decode(errors="replace"),err.decode(errors="replace"),(time.monotonic()-start)*1000,[])
            self.audit.record("execution_completed",request_id=str(req.request_id),exit_code=result.exit_code,duration_ms=result.duration_ms)
            return result
        except HTTPException: raise
        except Exception as e:
            self.audit.record("execution_error",request_id=str(req.request_id),error=type(e).__name__); raise HTTPException(500,"Execution failed.") from e
def create_app():
    policy=AgentSecurityPolicy.from_env(); agent=AgentServer(policy); app=FastAPI(title="AI Media Hub Execution Agent",version="0.2.0")
    def auth(authorization:str|None=Header(default=None)): agent.authenticate(authorization)
    @app.get("/health")
    async def health(): return {"status":"ok","node":agent.node.id,"platform":agent.node.platform}
    @app.get("/v1/node",dependencies=[Depends(auth)])
    async def node(): return {"id":agent.node.id,"name":agent.node.name,"platform":agent.node.platform,"capabilities":sorted(c.value for c in agent.node.capabilities),"labels":agent.node.labels}
    @app.post("/v1/execute",dependencies=[Depends(auth)])
    async def execute(payload:ExecutePayload):
        r=await agent.execute(payload); return {"request_id":str(r.request_id),"node_id":r.node_id,"exit_code":r.exit_code,"stdout":r.stdout,"stderr":r.stderr,"duration_ms":r.duration_ms,"artifacts":r.artifacts}
    return app
