# Atomic Chat mobile control

Atomic Chat supports MCP over HTTP and Streamable HTTP. The desktop server remains
the local cockpit; mobile Atomic Chat connects to the AI Media Hub MCP endpoint.

## Architecture

Atomic Chat mobile
  -> HTTPS/Streamable HTTP
  -> AI Media Hub mobile MCP boundary (:8787)
  -> ControlPlane
  -> authenticated Execution Agent (:8765, internal only)
  -> Windows RTX 6000

The Execution Agent is never exposed to the phone or public network.

## Windows setup

From the repository:

  $env:AMH_MCP_HTTP_TOKEN = "<long-random-token>"
  $env:AMH_MCP_HTTP_HOST = "0.0.0.0"
  $env:AMH_MCP_HTTP_PORT = "8787"
  $env:AMH_AGENT_URL = "http://127.0.0.1:8765"
  $env:AMH_AGENT_TOKEN = "<same-agent-token>"
  $env:AMH_WORKSPACE = "C:\Users\HP\Documents\GitHub\ABADI"
  $env:AMH_CONTROL_DB = "C:\Users\HP\Documents\GitHub\ABADI\data\control-plane.sqlite3"

  .\.venv\Scripts\python.exe -m ai_media_hub.mobile_mcp

For first proof, allow port 8787 only on the trusted LAN. Do not port-forward it
from the router to the public internet. For access away from home, add a private
VPN/mesh transport later; keep the MCP boundary unchanged.

## Atomic Chat mobile

In Atomic Chat on the phone, add an MCP server using HTTP and point it to:

  http://<WINDOWS-LAN-IP>:8787/mcp

Use the MCP bearer token as the server authentication credential.

Then test:

1. "افحص حالة عقدة AI Media Hub."
2. "شغّل فحص GPU."
3. "أنشئ فيديو اختبار 3 ثوانٍ وأعطني Job ID والـSHA-256."

The mobile client should receive the same narrow tools as desktop.

## Security rules

- Long random bearer token.
- Execution Agent stays on 127.0.0.1:8765.
- Mobile MCP listens only on the trusted LAN during proof.
- No router port forwarding.
- Prefer private VPN/mesh for remote access later.
- Rotate the MCP token if exposed.

## Production gate

The mobile path is proven only when Atomic Chat mobile can call node_status and
run_probe through HTTP, then produce a real artifact through ControlPlane.
