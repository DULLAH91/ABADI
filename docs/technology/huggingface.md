# Hugging Face — Provider Integration

**Status:** Integrated as a provider boundary  
**Role:** Model Hub + inference provider + model metadata source

AI Media Hub uses Hugging Face through a dedicated HuggingFaceProvider adapter. Product code must not depend directly on the Hugging Face SDK.

## Capabilities

- Inference Providers through AsyncInferenceClient
- Automatic routing with provider="auto"
- Text generation/chat completion
- Image generation
- Hub model metadata lookup for registry and commercial review
- Environment-based authentication

## Security

Use a least-privilege Hugging Face User Access Token. Fine-grained tokens are preferred for production. Never commit the token, place it in source code, or send it through chat.

The repository ships only .env.example. Keep real credentials in the deployment secret store or local environment.

## Commercial governance

A model being available on the Hub does not automatically approve it for commercial use.

Before a model is promoted to a production route, record:

1. Exact model ID
2. Exact revision/commit when reproducibility matters
3. Model license
4. Base-model and component licenses where applicable
5. Gated-access terms, if applicable
6. Provider terms and pricing
7. Privacy/data-handling implications
8. Local-vs-hosted execution path
9. Fallback model/provider

model_info() feeds this review process; it does not replace legal review of the model card and license.

## Architecture

    AI Media Hub
         |
         v
    Model Router
         |
         +--> HuggingFaceProvider
         |       |
         |       +--> HF Inference Providers
         |       +--> Hub model metadata
         |
         +--> Ollama / vLLM / llama.cpp
         +--> OpenAI / other adapters
         +--> ComfyUI / media workers

## Initial tasks

- text.generation
- image.generation

Additional tasks must be added through explicit mappings and tests; do not pass arbitrary SDK calls through the core.

## Next integration

The next runtime milestone is the Core Job Runtime. It will call providers through ProviderRequest/ProviderResult, attach model/provider metadata to each job, and record cost/latency telemetry.
