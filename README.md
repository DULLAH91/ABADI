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
- Model providers: Hugging Face, Ollama, llama.cpp, vLLM, and other adapters
- Model Hub/Inference: Hugging Face provider boundary with metadata/license review
- Workflow: n8n only where its license/use case is acceptable; otherwise Temporal or native orchestration
- Media: FFmpeg + ImageMagick
- Image/video generation: ComfyUI and model-specific workers
- Data: PostgreSQL + pgvector or Qdrant
- Queue/cache: Redis initially; dedicated broker only when justified
- Containers: Docker
- Observability: OpenTelemetry-compatible metrics/logging/tracing
- CI/CD: GitHub Actions

## Hugging Face integration

Hugging Face is integrated as a **provider boundary**, not as a vendor dependency throughout the core.

Current capabilities:
- Inference Providers with automatic routing
- Text generation/chat completion
- Image generation
- Hub model metadata lookup
- Environment-based authentication
- Explicit model/license/commercial review before production admission

See docs/technology/huggingface.md.

## Commercial rule

Open-source dependencies, models, nodes, datasets, and skills are admitted through a license/security/maintenance/commercial-use review. No dependency becomes part of the commercial core merely because it is popular.

## Current phase

**Phase 0 — Foundation → Runtime**

The architecture and commercial foundation are established. The implementation is now moving into the Core Job Runtime and provider layer.

Current execution order:

1. Provider contracts
2. Hugging Face provider integration
3. Core Job Runtime
4. Model Router
5. VoiceStudio / ComfyUI / FFmpeg workers
6. Cost and evaluation engines
7. Product UI and commercial workflows

See:
- docs/architecture/system.md
- docs/product/commercialization.md
- docs/technology/huggingface.md
- .kiro/steering/product.md
- .kiro/steering/engineering.md
- .kiro/skills/
