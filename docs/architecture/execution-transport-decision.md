# Execution Transport Decision

Date: 2026-10-07

## Decision

AI Media Hub owns the execution-node contract. The product must not couple its core architecture to a remote desktop product.

For the first Windows RTX 6000 deployment, use **lnwjud** as the preferred external execution transport candidate, behind the AI Media Hub ExecutionNodeAdapter.

Reference: https://github.com/engasnm111/lnwjud

## Why

lnwjud already provides the operational surface we would otherwise spend significant time rebuilding:

- Windows workspace access
- policy-checked filesystem operations
- Git integration
- bounded process execution
- process lifecycle and logs
- audit metadata
- project-aware commands
- MCP transport
- OpenAI Secure MCP Tunnel support
- outbound-only remote connection for ChatGPT web

This gives AI Media Hub a faster path to a real Windows execution node without making lnwjud part of the product core.

## Boundary

The architecture remains:

AI Media Hub Runtime
  -> ExecutionNodeAdapter
  -> transport
  -> Windows execution node

The adapter is the compatibility boundary.

lnwjud is therefore replaceable. If its license, security posture, reliability, feature direction, or economics cease to satisfy the product requirements, another transport can implement the same contract.

## Security requirements

The Windows node must:

1. use a private/outbound tunnel rather than a public shell endpoint;
2. operate only on explicitly registered project/workspace roots;
3. retain audit records;
4. use process execution with bounded arguments, timeouts, and cancellation;
5. keep destructive operations confirmation-gated;
6. never expose runtime credentials or secrets to the model unnecessarily;
7. remain a user-owned execution node.

## Product moat

We do not compete with lnwjud.

AI Media Hub owns:

- job orchestration
- model/provider routing
- workflow planning
- execution policies
- evaluation
- artifact provenance
- cost intelligence
- production telemetry
- commercial workflows

The transport is infrastructure. The intelligence and production system are the product.

## Rejection rule

Do not merge or fork third-party execution software into the AI Media Hub core unless a concrete requirement cannot be satisfied through the adapter boundary.

## Next gate

Connect the Windows RTX 6000 node through the chosen transport and prove:

- node discovery
- authenticated read access
- repository status
- Docker state
- GPU state
- controlled command execution
- artifact transfer
- audit trail
- timeout/failure handling

Only after that evidence exists should the node be marked production-ready.
