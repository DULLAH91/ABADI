---
name: security-review
description: Review AI Media Hub code and integrations for secrets, file handling, network access, agent permissions, MCP risk, authentication, authorization, and supply-chain issues.
---

# Security Review

Check:
- secrets and credentials
- file upload validation
- path traversal
- command injection
- unsafe subprocess usage
- SSRF
- arbitrary URL fetching
- model/tool prompt injection
- MCP permissions
- container privileges
- dependency supply chain
- authentication/authorization
- tenant/project isolation
- auditability

For agentic execution, default to least privilege and explicit approval for destructive or externally consequential operations.
