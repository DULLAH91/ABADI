# AI Media Hub — Execution Nodes

## Decision

AI Media Hub owns the execution-node contract. External remote-control products are transports, not part of the product architecture.

```
ExecutionNode
    ↓
ExecutionNodeAdapter
    ↓
transport (HTTP / local agent / SSH / future native agent)
    ↓
physical or virtual worker
```

The first target is the Windows machine with the Quadro RTX 6000.

## Runtime authority

The AI Media Hub runtime owns job identity/state, authorization, policy, routing, timeout limits, retry/failure classification, cost/telemetry, and artifact provenance.

A transport never becomes the source of truth for job state.

## Security boundary

No execution request crosses the adapter boundary without runtime-side policy validation. The initial contract supports shell execution, but arbitrary remote access is not granted by default.

## Non-goals

Do not introduce Redis, Temporal, Kubernetes, or a third-party remote desktop product merely to establish this boundary.

## Next implementation gate

Implement one authenticated Windows execution agent and prove node health, `nvidia-smi`, repository inspection, Docker/runtime inspection, artifact return, and audit/telemetry.
