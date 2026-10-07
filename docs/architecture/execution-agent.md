# AI Media Hub — Execution Agent

The execution agent is the first concrete implementation of the AI Media Hub execution-node contract.

Living Core -> Runtime -> ExecutionNodeAdapter -> authenticated transport -> Windows Execution Agent -> GPU/Docker/FFmpeg/ComfyUI/filesystem.

## Security boundary

- Bearer token authentication with constant-time comparison.
- Restricted mode is the default.
- Restricted mode permits only explicitly allowlisted executables.
- Working-directory roots can be constrained.
- Every command has a hard timeout.
- Append-only JSONL audit events are emitted.
- Bearer tokens are never written to the audit log.

Trusted mode is an explicit operator decision and must only be used on a private trusted network.

## Runtime authority

The agent is not the source of truth for jobs. It executes requests and returns results. Job state, routing, policy, retry, cost, telemetry, and artifact provenance belong to the AI Media Hub runtime.

## Network boundary

Default binding is localhost. Do not expose the agent directly to the public internet. A future relay or zero-trust transport belongs behind ExecutionNodeAdapter.

## Windows registration gate

The RTX 6000 node becomes production-eligible only after proving authenticated node discovery, nvidia-smi, Git inspection, Docker inspection, artifact return, audit trail, and timeout/failure behavior.

## Environment

Required: AI_MEDIA_HUB_AGENT_TOKEN

Optional: AI_MEDIA_HUB_NODE_ID, AI_MEDIA_HUB_NODE_NAME, AI_MEDIA_HUB_AGENT_MODE=restricted|trusted, AI_MEDIA_HUB_ALLOWED_ROOTS, AI_MEDIA_HUB_AGENT_HOST, AI_MEDIA_HUB_AGENT_PORT.
