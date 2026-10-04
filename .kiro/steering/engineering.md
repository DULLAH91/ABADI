# Engineering Steering

## Non-negotiable
Inspect before modifying. Preserve existing behavior unless a change explicitly requires it. Keep changes scoped and reversible.

## Architecture
- Modular monolith first; split services only when operational or scaling evidence requires it.
- Domain logic must not depend directly on UI or vendor SDKs.
- External providers use adapters/interfaces.
- Long-running work runs asynchronously.
- Configuration comes from environment/config files, never source code secrets.

## Quality
- Python code uses type hints and clear module boundaries.
- Public APIs have request/response schemas.
- Tests cover critical domain logic and failure paths.
- Prefer deterministic unit tests and isolated integration tests.
- Add structured logging and correlation/job IDs to asynchronous operations.

## Security
- Never commit secrets, tokens, credentials, model keys, or private user media.
- Validate uploaded files and external URLs.
- Apply least privilege to agents and MCP servers.
- Treat generated content and model outputs as untrusted input where appropriate.
- Record security-sensitive configuration changes.

## Git
- Work on feature branches.
- One coherent change per commit where practical.
- PRs must explain intent, risks, tests, and rollback.
- Never silently rewrite the default branch.

## Definition of done
Implementation + tests + documentation + configuration example + observability + security review where applicable.
