# Hugging Face Integration

**Status:** Approved provider integration foundation  
**Role:** Model Hub + Inference Provider adapter

## Decision

AI Media Hub will integrate Hugging Face through a provider adapter. Core orchestration code must not import Hugging Face SDK objects directly.

Hugging Face currently provides unified access to hundreds of models through Inference Providers and exposes a Python InferenceClient. The client supports provider selection, model IDs, dedicated Inference Endpoints, and local OpenAI-compatible endpoints.

## Supported capabilities in this milestone

- Chat / text generation
- Text-to-image
- Text-to-speech
- Automatic speech recognition
- Provider health check
- Provider registry for future model routing

The adapter isolates the synchronous Hugging Face SDK behind asyncio.to_thread, so long-running inference does not block the orchestration event loop.

## Authentication

Use the environment variable HF_TOKEN.

Never commit the token. The example configuration is .env.example.

Hugging Face documents User Access Tokens as the authentication mechanism for Inference Providers.

## Provider routing

Default: HF_PROVIDER=auto

Hugging Face can automatically select a provider according to the account's inference-provider preferences. Explicit provider/model routing can be introduced later in the AI Media Hub Model Router.

## Commercial controls

The Model Registry must record, for every adopted model:

- model ID and revision
- model license
- commercial-use status
- gated-access requirements
- provider
- input/output modality
- estimated cost
- local deployment option
- replacement candidates

A Hugging Face model is not automatically approved for commercial use because it is hosted on the Hub.

## MCP

Hugging Face also provides an MCP Server for compatible agents. It can search models, datasets, Spaces, papers and documentation, and can run Jobs and community tools. This is a separate agent-tool integration and should not be coupled to the inference adapter.

## Next milestone

Connect this provider to the Core Job Runtime and Model Router, then add one real end-to-end job with a selected model and cost telemetry.
