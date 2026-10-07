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

## Node responsibilities

An execution node advertises identity, platform, capabilities, routing labels, health, resource access, and artifact production.

The first target node is the Windows machine with the Quadro RTX 6000.

## Runtime responsibilities

The AI Media Hub runtime remains authoritative for job identity/state, authorization, policy, routing, timeout limits, retry/failure classification, cost/telemetry, and artifact provenance.

A transport must never become the source of truth for job state.

## Security boundary

No execution request crosses the adapter boundary without runtime-side policy validation.

The initial contract supports shell execution, but arbitrary remote access is not granted by default. Capabilities and allowed operations are explicit.

## Non-goals

Do not introduce Redis, Temporal, Kubernetes, or a third-party remote desktop product merely to establish this boundary.

## Next implementation gate

Implement one authenticated Windows execution agent against this contract, then prove:

1. node registration/health
2. `nvidia-smi` execution
3. repository inspection
4. Docker/runtime inspection
5. artifact return
6. audit/telemetry

Only after that gate passes should the node become an active production worker.
