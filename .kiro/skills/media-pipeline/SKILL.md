---
name: media-pipeline
description: Build reliable media-processing pipelines using FFmpeg, ImageMagick, GPU workers, artifact lineage, validation, and deterministic job execution.
---

# Media Pipeline

## Pipeline stages
1. Validate input
2. Normalize metadata
3. Create immutable working artifact
4. Process/generate
5. Validate output
6. Record lineage and checksum
7. Publish artifact
8. Emit metrics and cost data

## FFmpeg rules
- Pin/record the FFmpeg build.
- Prefer LGPL-compatible builds/configurations for commercial products unless GPL obligations are intentionally accepted.
- Record codec/container decisions.
- Never overwrite source artifacts.
- Make jobs resumable where practical.

## Failure handling
Classify failures as input, dependency, model, infrastructure, timeout, validation, or unknown. Retry only retryable classes and make retries idempotent.
