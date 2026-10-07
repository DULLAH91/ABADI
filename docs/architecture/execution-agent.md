# AI Media Hub — Windows Execution Agent

The Windows Execution Agent is the first concrete ExecutionNode implementation.

Living Core -> Runtime -> ExecutionNodeAdapter -> authenticated transport -> Execution Agent -> GPU/Docker/FFmpeg/ComfyUI/filesystem.

## Security

- localhost binding by default
- bearer authentication with constant-time comparison
- restricted mode uses full-match command patterns, not executable-name allowlists
- shell composition is blocked in restricted mode
- working-directory roots can be constrained
- execution timeout is bounded to 30 minutes
- request IDs are preserved end-to-end
- append-only JSONL audit is supported
- the agent never owns Job state

## API

GET /health
GET /v1/node (authenticated)
POST /v1/execute (authenticated)

## Environment

AI_MEDIA_HUB_AGENT_TOKEN is required.
AI_MEDIA_HUB_AGENT_MODE defaults to restricted.
AI_MEDIA_HUB_ALLOWED_ROOTS optionally constrains working directories.
AI_MEDIA_HUB_ALLOWED_COMMAND_PATTERNS optionally replaces the default safe command patterns.
AI_MEDIA_HUB_AGENT_HOST defaults to 127.0.0.1.
AI_MEDIA_HUB_AGENT_PORT defaults to 8787.

Restricted defaults intentionally allow only safe probes such as nvidia-smi, tool version checks, and git status. Do not expose arbitrary shell through Restricted Mode.

Trusted Mode is an explicit operator decision and must only be used on a private trusted network.

## Production gate

Before activating the RTX 6000 as a production worker:
1. add replay/idempotency protection
2. put remote transport behind authenticated relay or zero-trust networking
3. add typed capability operations
4. add artifact transfer
5. add resource telemetry
6. correlate Job IDs centrally
7. install as a Windows service with restart policy
8. run authenticated end-to-end tests on the real node
