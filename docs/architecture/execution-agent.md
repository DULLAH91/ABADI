# AI Media Hub Execution Agent

The Execution Agent is the first concrete implementation behind the ExecutionNode contract.

## Security model

- Bearer token is mandatory.
- The agent binds to localhost by default.
- Shell interpreters are disabled by default.
- Subprocess execution uses shell=False.
- Environment overrides for critical Windows variables are blocked.
- Optional allowed filesystem roots constrain working directories.
- Output is bounded.
- Every completed execution is written to an append-only JSONL audit log.
- Runtime-side policy remains authoritative; the agent is not a job database.

## API

GET /health is unauthenticated and returns node capability/health metadata.

GET /v1/node requires the bearer token.

POST /v1/execute requires the bearer token and accepts an argv-based execution request.

Example payload:
{
  "request_id": "uuid",
  "operation": "exec",
  "argv": ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
  "timeout_seconds": 30
}

## Deployment

The first deployment target is the Windows RTX 6000 machine.

Keep AMH_AGENT_HOST=127.0.0.1 until a secure transport/identity layer is installed. Do not expose the agent directly to the public internet.

For remote control, place a mutually authenticated transport or private network gateway in front of the agent. The transport implements ExecutionNodeAdapter; the agent itself remains unchanged.

## Next gate

Prove on the real Windows node:
1. health
2. authenticated node info
3. nvidia-smi
4. Git inspection
5. Docker inspection
6. artifact upload/download
7. audit verification
8. failure/timeout behavior
