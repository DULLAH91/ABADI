# Hugging Face Provider

AI Media Hub uses Hugging Face through an adapter boundary. The core domain does not import provider SDK objects.

Supported capabilities in this foundation: chat, text-to-image, text-to-speech, automatic speech recognition, and provider health checks.

The runtime reads Hugging Face configuration from environment variables. No real credential belongs in source control.

Model selection and commercial approval remain Model Registry responsibilities. A Hub model is not automatically approved for commercial use.

Next: connect this provider to the Core Job Runtime and Model Router, then record execution cost and latency per job.
