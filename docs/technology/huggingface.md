# Hugging Face Integration

**Status:** Approved provider integration foundation  
**Role:** Model Hub + Inference Provider adapter

## Decision

AI Media Hub integrates Hugging Face through a provider adapter. Core orchestration code must not import Hugging Face SDK objects directly.

Hugging Face Inference Providers provide unified access to supported models and a Python `InferenceClient`. The client supports automatic or explicit provider selection and can also target dedicated Inference Endpoints or compatible local endpoints.

## Supported capabilities in this milestone

- Chat / text generation
- Text-to-image
- Text-to-speech
- Automatic speech recognition
- Provider health check
- Provider registry for future model routing

Synchronous SDK calls are isolated behind `asyncio.to_thread` so they do not block the async orchestration event loop.

## Configuration

Runtime configuration is environment-based:

- `HF_TOKEN`
- `HF_PROVIDER` (default: `auto`)
- `HF_TIMEOUT_SECONDS`
- `HF_DEFAULT_MODEL`
- `HF_BILL_TO`

No credential is committed to the repository.

## Provider routing

The adapter defaults to Hugging Face `auto` routing. The future AI Media Hub Model Router will apply product policy across:

- quality
- cost
- latency
- model/license eligibility
- local vs hosted execution
- fallback availability

## Commercial controls

A model hosted on Hugging Face is not automatically commercially approved. The Model Registry must record:

- model ID and revision
- model license
- commercial-use status
- gated-access requirements
- provider
- modality
- estimated cost
- local deployment option
- replacement candidates

## MCP

Hugging Face also provides an MCP server for compatible agents. That integration is a separate agent-tool capability and must not be coupled directly to the inference adapter.

## Next milestone

Connect `HuggingFaceProvider` to the Core Job Runtime and Model Router, then execute one real end-to-end job with cost telemetry.
