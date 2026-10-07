# Atomic Chat control-plane integration

Atomic Chat is the cockpit. AI Media Hub owns execution policy and the execution node.

## Architecture

~~~text
Atomic Chat
   │ MCP / STDIO
   ▼
ai_media_hub.mcp_server
   │
   ▼
AI Media Hub ControlPlane
   │ authenticated HTTP
   ▼
Windows Execution Agent :8765
   │
   ├── nvidia-smi
   ├── Git
   ├── Docker
   └── FFmpeg → artifact
~~~

Atomic Chat never receives arbitrary shell access. The MCP server exposes only approved,
typed operations.

## Windows setup

From the AI Media Hub repository:

~~~powershell
py -3 -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -e .
~~~

Generate a private token and start the execution agent. Keep the agent bound to
127.0.0.1 for the first proof:

~~~powershell
$env:AMH_AGENT_TOKEN = "REPLACE_WITH_A_LONG_RANDOM_TOKEN"
$env:AMH_AGENT_HOST = "127.0.0.1"
$env:AMH_AGENT_PORT = "8765"
$env:AMH_ALLOWED_ROOTS = "C:\\AI\\MediaHub"
$env:AMH_WORKSPACE = "C:\\AI\\MediaHub"

.\\.venv\\Scripts\\python.exe -m ai_media_hub.execution.agent
~~~

Use the actual repository/workspace path in place of C:\\AI\\MediaHub.

The agent must not be exposed directly to the public internet.

## Atomic Chat configuration

Atomic Chat supports local MCP servers through STDIO. Open:

**Settings → MCP Servers → Add MCP Server**

Use:

- Name: AI Media Hub
- Type: STDIO
- Command: C:\\AI\\MediaHub\\.venv\\Scripts\\python.exe
- Arguments:
  - -m
  - ai_media_hub.mcp_server

Environment:

~~~text
AMH_AGENT_URL=http://127.0.0.1:8765
AMH_AGENT_TOKEN=REPLACE_WITH_THE_SAME_TOKEN
AMH_WORKSPACE=C:\\AI\\MediaHub
AMH_CONTROL_DB=C:\\AI\\MediaHub\\data\\control-plane.sqlite3
AMH_GPU_COST_PER_SECOND_USD=0
~~~

Equivalent JSON:

~~~json
{
  "command": "C:/AI/MediaHub/.venv/Scripts/python.exe",
  "args": ["-m", "ai_media_hub.mcp_server"],
  "env": {
    "AMH_AGENT_URL": "http://127.0.0.1:8765",
    "AMH_AGENT_TOKEN": "REPLACE_WITH_THE_SAME_TOKEN",
    "AMH_WORKSPACE": "C:/AI/MediaHub",
    "AMH_CONTROL_DB": "C:/AI/MediaHub/data/control-plane.sqlite3",
    "AMH_GPU_COST_PER_SECOND_USD": "0"
  }
}
~~~

## First proof from Atomic Chat

After the server reports connected, ask:

1. **افحص حالة عقدة AI Media Hub.**
   - Expected tool: node_status
   - Expected evidence: node ID, Windows platform, Quadro RTX 6000, VRAM and driver.

2. **شغّل فحص GPU.**
   - Expected tool: run_probe with gpu.
   - Expected evidence: real nvidia-smi output and execution telemetry.

3. **أنشئ فيديو اختبار 3 ثوانٍ عبر AI Media Hub.**
   - Expected tool: produce_test_media.
   - Expected evidence:
     - Job ID
     - succeeded status
     - FFmpeg exit code 0
     - duration
     - MP4 path
     - byte size
     - SHA-256
     - estimated cost
     - timestamps

If Atomic Chat answers without a visible tool call, the MCP server is not being used.

## Production gate

This integration is considered proven only when the third call returns a real artifact
created by FFmpeg on the Windows execution node.

GPU-native image generation through ComfyUI is the next gate. It is deliberately not
part of the first probe: first prove control, execution, provenance and telemetry;
then add the expensive AI workload.

## Important design rule

Do not replace the MCP server with direct shell access. MCP is the cockpit boundary;
the ControlPlane is the policy boundary; the Execution Agent is the transport boundary.
This separation is what lets AI Media Hub later support HTTP agents, containers, SSH,
Nomad workers or other execution nodes without changing Atomic Chat.
