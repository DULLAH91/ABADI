---
name: ai-media-engineer
description: Design and implement production-grade AI media pipelines, orchestration, model adapters, workers, evaluation, observability, and commercial controls for AI Media Hub.
---

# AI Media Engineer

## When to use
Use for architecture, implementation, review, debugging, or extension of AI Media Hub media-generation and orchestration systems.

## Workflow
1. Inspect repository structure and relevant modules.
2. Read applicable steering files.
3. Identify the domain boundary and existing interfaces.
4. Prefer the smallest production-safe change.
5. Add tests for behavior and failure paths.
6. Document operational and commercial implications.
7. Report assumptions, risks, and verification.

## Required checks
- Is this synchronous or asynchronous work?
- Does it need a queue/worker?
- Is the provider behind an adapter?
- Are inputs/outputs validated?
- Is the operation observable and cost-trackable?
- Are retries idempotent?
- Does the dependency have acceptable licensing and maintenance?
- Can the capability later run self-hosted?

## Never
- hard-code secrets
- couple core domain logic to a vendor SDK
- add dependencies without justification
- silently change public behavior
- ship untested long-running workflows
