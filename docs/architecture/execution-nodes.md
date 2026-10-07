# AI Media Hub — Execution Nodes

## Decision

AI Media Hub owns the execution-node contract. External remote-control products are transports, not part of the product architecture.

The runtime therefore depends on:

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

An execution node advertises:

- identity and platform
- capabilities
- labels used by routing
- execution health
- access to GPU/CPU resources
- artifact production

The first target node is the Windows machine with the Quadro RTX 6000.

## Runtime responsibilities

The AI Media Hub runtime remains authoritative for:

- job identity and state
- authorization and policy
- routing
- timeout limits
- retry/failure classification
- cost and telemetry
- artifact provenance

A transport must never become the source of truth for job state.

## Security boundary

No execution request crosses the adapter boundary without runtime-side policy validation.

The initial contract supports shell execution, but the implementation deliberately does not grant arbitrary remote access by default. Capabilities and allowed operations are explicit.

## Non-goals

This layer does not introduce Redis, Temporal, Kubernetes, or a third-party remote desktop product.

Those may become implementations or infrastructure later if measured workload requirements justify them.

## Next implementation gate

Implement one authenticated Windows execution agent against this contract, then prove:

1. node registration/health
2. `nvidia-smi` execution
3. repository inspection
4. Docker/runtime inspection
5. artifact return
6. audit/telemetry

Only after that gate passes should the node become an active production worker.
