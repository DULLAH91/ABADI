# VoiceStudio — Technology Evaluation

**Category:** Audio / TTS / Voice Cloning / Dubbing / ASR  
**Status:** Pilot candidate — not approved for proprietary embedding

## Why it matters to AI Media Hub

VoiceStudio is a strong candidate for the Audio Worker layer. Current project documentation reports 16 TTS engines, 11 ASR engines, a 646-language catalogue, local REST/SSE/WebSocket APIs, an OpenAI-compatible audio API, MCP support, Docker support, and optional remote workers. This makes it unusually relevant to our agent/workflow architecture.

## Proposed role

Use VoiceStudio as an **audio capability provider**, not as the core of AI Media Hub.

Target integrations:
- TTS worker
- Voice cloning worker
- Video dubbing worker
- Transcription/ASR worker
- Long-form audiobook/story worker
- MCP audio tool provider
- OpenAI-compatible audio adapter

## Commercial decision

**Pilot: YES**  
**Direct proprietary embedding: NO, unless licensing is resolved**

The application is AGPL-3.0. The upstream project states that generated audio may be sold, but modifying VoiceStudio and providing the modified application as a network service can trigger AGPL source-availability obligations. The project also advertises a commercial license for proprietary embedding. Optional engines/models retain their own licenses.

Therefore:
1. Prefer running an unmodified VoiceStudio worker behind a clearly defined integration boundary.
2. Do not copy VoiceStudio code into the proprietary AI Media Hub core.
3. Do not assume model licenses match the application license.
4. Record the exact VoiceStudio release and each selected engine/model license.
5. If we need proprietary embedding or modifications, evaluate the commercial license first.

## Architecture fit

```
AI Media Hub
   |
   | AudioProvider interface
   v
VoiceStudio Adapter
   |
   +--> TTS
   +--> Voice Clone
   +--> Dubbing
   +--> ASR
   +--> MCP
```

The core platform must depend on our adapter contract, never on VoiceStudio internals.

## Product opportunities

1. Arabic advertising voice factory
2. Multi-language campaign dubbing
3. Documentary narration pipeline
4. Audiobook production
5. Social-video voice generation
6. Enterprise private voice workflows

## Risks

- AGPL obligations
- Model-specific licenses
- Voice consent/right-of-publicity requirements
- Active-beta stability
- GPU/RAM requirements vary by engine
- Quality varies substantially by language and engine

## Acceptance tests for pilot

- Arabic TTS quality
- Arabic voice cloning quality with explicit consent
- English/Arabic dubbing alignment
- Batch throughput
- GPU memory consumption
- API reliability
- Docker deployment
- MCP integration
- Audio provenance/watermark behavior
- Cost per minute
- Failure/retry behavior

## Decision

**ADOPT AS PILOT AUDIO WORKER, NOT AS PROPRIETARY CORE.**

Reference: https://github.com/debpalash/VoiceStudio
