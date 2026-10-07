# AI Media Hub — Windows Execution Agent

The Windows Execution Agent is the first concrete implementation of the AI Media Hub ExecutionNode contract.

Architecture:
Living Core -> Runtime -> ExecutionNodeAdapter -> authenticated transport -> Windows Execution Agent -> GPU/Docker/FFmpeg/ComfyUI/filesystem.

## Security boundary

- Loopback binding is the default deployment posture.
- Every control-plane request requires a bearer token.
- Bearer comparison uses constant-time comparison.
- Commands are restricted by explicit full-match regular expressions.
- Every command has a bounded timeout.
- Node identity is checked on every execution request.
- The control-plane request ID is preserved end-to-end.
- Accepted, rejected, timeout, and completed requests can be written as JSONL audit events.
- Secrets are not written to the audit log.
- The agent does not own job state.

## Endpoints

- GET /health — local liveness
- GET /v1/node — authenticated node identity/capabilities
- POST /v1/execute — authenticated, policy-filtered execution

## Environment

Required:
- AI_MEDIA_HUB_NODE_TOKEN

Optional:
- AI_MEDIA_HUB_NODE_ID — defaults to windows-rtx6000-01
- AI_MEDIA_HUB_NODE_NAME — defaults to Windows RTX 6000
- AI_MEDIA_HUB_ALLOWED_COMMANDS — pipe-separated full-match regex allowlist
- AI_MEDIA_HUB_AUDIT_LOG — optional JSONL audit path

Default commands are deliberately narrow:
- nvidia-smi
- python --version
- git --version
- docker version
- ffmpeg -version

Do not expand the allowlist casually. Prefer adding typed capability-specific operations over exposing arbitrary shell.

## Start on Windows

Set a long random node token:

$env:AI_MEDIA_HUB_NODE_TOKEN="replace-with-a-long-random-secret"

Start locally:

python -m uvicorn ai_media_hub.agent_server:app --host 127.0.0.1 --port 8787

Do not expose port 8787 directly to the public internet. Remote connectivity belongs behind an authenticated relay or zero-trust transport.

## Production gate

Before this node can execute project workflows, add:
1. replay/idempotency protection
2. authenticated remote transport
3. typed capability-specific operations
4. artifact upload/download contract
5. CPU/GPU/RAM/disk telemetry
6. central Job ID correlation
7. Windows service installation and restart policy
8. end-to-end tests against the RTX 6000 node
