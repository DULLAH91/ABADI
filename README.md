# AI Media Hub

**AI Systems & Generative Media Engineering**

AI Media Hub is a production-grade, self-hosted AI media orchestration platform designed to turn creative intent into repeatable, measurable, commercially deployable media workflows.

## Product mission

Build an extensible media operating layer that can orchestrate models, agents, workflows, media processors, storage, APIs, and human review—while preserving ownership of the workflow/IP.

## Business objective

The platform is not a technology collection. Every subsystem must contribute to at least one of:

- A sellable product or API
- A reusable internal capability
- A measurable reduction in production cost/time
- A defensible technical asset
- Enterprise readiness
- Investor-grade evidence of traction, efficiency, or IP

## Operating model

**ChatGPT** — architecture, research, technical review, product strategy  
**Kiro** — implementation agent, tests, refactoring, PRs  
**GitHub** — source of truth for code and engineering decisions  
**Notion** — product/knowledge/investment operating system  
**AI Media Hub** — the product and orchestration runtime

## Initial stack

- API: Python + FastAPI
- Frontend: Next.js when UI work begins
- Workflow: n8n only where its license/use case is acceptable; otherwise Temporal or native orchestration
- Media: FFmpeg + ImageMagick
- Image/video generation: ComfyUI and model-specific workers
- LLM runtime: Ollama / llama.cpp / vLLM as workload requires
- Data: PostgreSQL + pgvector or Qdrant
- Queue/cache: Redis initially; dedicated broker only when justified
- Containers: Docker
- Observability: OpenTelemetry-compatible metrics/logging/tracing
- CI/CD: GitHub Actions

## Commercial rule

Open-source dependencies, models, nodes, datasets, and skills are admitted through a license/security/maintenance/commercial-use review. No dependency becomes part of the commercial core merely because it is popular.

## Current phase

**Phase 0 — Foundation and commercial architecture**

The first implementation target is a clean platform skeleton with explicit boundaries, tests, configuration, security controls, and a commercialization registry.

See:
- docs/architecture/system.md
- docs/product/commercialization.md
- .kiro/steering/product.md
- .kiro/steering/engineering.md
- .kiro/skills/
