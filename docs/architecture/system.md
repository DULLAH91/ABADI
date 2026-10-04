# System Architecture

## Target architecture

```
User / Client
    |
    v
API Gateway / Web App
    |
    v
Project + Job Orchestrator
    |
    +--> Model Router ------> Provider Adapters
    |                            |
    |                            +--> Hugging Face
    |                            +--> Ollama / vLLM / llama.cpp
    |                            +--> OpenAI / other APIs
    |
    +--> Workflow Engine ---> Agents / Skills / MCP Tools
    |
    +--> Media Pipeline ----> FFmpeg / ImageMagick / ComfyUI
    |
    +--> Queue -------------> Workers / GPU Workers
    |
    +--> Artifact Store ----> Inputs / Intermediates / Outputs
    |
    +--> Metadata DB --------> PostgreSQL
    |
    +--> Vector/RAG --------> pgvector or Qdrant
    |
    +--> Observability ------> Logs / Metrics / Traces / Cost
```

## Architectural decisions

### Modular monolith first
The first release uses a modular backend with explicit domains. Services are split only when a real scaling, isolation, or deployment requirement appears.

### Provider abstraction
Generation providers are adapters. Product code calls stable interfaces such as:
- TextGenerationProvider
- ImageGenerationProvider
- VideoGenerationProvider
- AudioGenerationProvider
- EmbeddingProvider

Hugging Face is the first external model-provider adapter implemented under this boundary. The adapter exposes normalized requests/results and isolates vendor SDK details from the core.

### Model governance
A model is not admitted to a production route solely because it is discoverable or popular.

The model registry must record:
- provider
- model ID
- revision when required
- task
- license
- gated-access requirements
- provider route
- deployment mode
- cost
- quality/evaluation signals
- fallback

### Job model
Every long-running operation becomes a job with:
- id
- project_id
- workflow_id
- status
- priority
- inputs
- selected provider/model
- cost estimate/actual
- timestamps
- artifacts
- error/retry metadata

### Artifact model
Artifacts are immutable references to generated or uploaded media plus metadata, provenance, checksum, and lineage.

### Commercial telemetry
Every generation-capable operation should expose enough data to estimate unit economics without logging private content unnecessarily.
